import os
import json
import time
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
import vk_api
from vk_api import VkApi, ApiError
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from database import Database
from vk_handler import VKHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Bot:
    def __init__(self) -> None:
        """Инициализация бота с проверкой токенов"""
        load_dotenv()
        self._check_env_vars()

        try:
            # Инициализация подключения к VK API
            self.vk_session = VkApi(token=os.getenv('VK_TOKEN_GROUP'))
            self.vk = self.vk_session.get_api()

            # Проверка подключения к VK API
            self._check_vk_connection()

            # Инициализация LongPoll
            self.longpoll = VkLongPoll(self.vk_session)

            logger.info("✅ LongPoll инициализирован")

            # Инициализация базы данных
            self.db = Database()
            logger.info(f"🛢️ Подключено к PostgreSQL: {os.getenv('DB_NAME')}")

            # Инициализация обработчика VK
            self.vk_handler = VKHandler(os.getenv('VK_TOKEN_USER'), db=self.db)

            # Словарь для хранения состояний пользователей
            self.user_states = {}

        except Exception as e:
            logger.critical(f"Ошибка инициализации бота: {e}")
            raise

    def _check_vk_connection(self):  # <-- Добавьте этот метод
        """Проверяет подключение к VK API"""
        try:
            group_info = self.vk.groups.getById()
            logger.info(f"✅ Успешное подключение к группе: {group_info[0]['name']}")
            return True
        except Exception as e:
            logger.critical(f"❌ Ошибка подключения к VK API: {e}")
            raise RuntimeError(f"VK API connection failed: {e}")

    def _check_env_vars(self):
        """Проверка наличия всех необходимых переменных окружения"""
        required_vars = ['VK_TOKEN_GROUP', 'VK_TOKEN_USER', 'VK_ID']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            logger.critical(f"Отсутствуют переменные: {', '.join(missing)}")

            # Создаем/обновляем .env файл с шаблоном
            with open('.env', 'w') as f:
                for var in required_vars:
                    f.write(f"{var}=\n")

            raise ValueError(
                "Файл .env обновлен. Пожалуйста, заполните недостающие переменные и перезапустите бота."
            )

    def _check_group_token(self):
        """Проверка валидности группового токена"""
        try:
            group_info = self.vk.groups.getById()
            logger.info(f"Успешное подключение к группе: {group_info[0]['name']}")
        except ApiError as e:
            if e.code == 5:
                logger.critical("Недействительный групповой токен!")
                logger.info("Как получить новый групповой токен:")
                logger.info("1. Перейдите в управление сообществом")
                logger.info("2. Настройки -> API -> Создать ключ")
                logger.info("3. Выберите права: Управление сообществом, Сообщения")
            raise

    def run(self) -> None:
        """Основной цикл работы бота"""
        logger.info("Запуск основного цикла бота...")

        try:
            while True:
                try:
                    for event in self.longpoll.listen():
                        try:
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                self._handle_event(event)
                        except Exception as e:
                            logger.error(f"Ошибка обработки события: {e}")
                            time.sleep(1)

                except KeyboardInterrupt:
                    logger.info("Бот остановлен пользователем")
                    break
                except Exception as e:
                    logger.error(f"Ошибка LongPoll: {e}")
                    time.sleep(10)

        finally:
            logger.info("Завершение работы бота")
            if hasattr(self, 'db'):
                self.db.close()
            logger.info("Все соединения закрыты")

    def _check_connection(self):
        """Проверка соединения перед запуском"""
        try:
            # Проверка группового токена
            group_info = self.vk.groups.getById()
            logger.info(f"Подключение к группе: {group_info[0]['name']}")

            # Проверка пользовательского токена
            if hasattr(self, 'vk_handler'):
                try:
                    user_info = self.vk_handler.user_vk.users.get()
                    logger.info("Пользовательский токен валиден")
                except ApiError as e:
                    if e.code == 5:
                        logger.critical("ОШИБКА: Неверный пользовательский токен!")
                        logger.info("Как получить новый токен:")
                        logger.info("1. Перейдите по ссылке:")
                        logger.info(
                            f"https://oauth.vk.com/authorize?client_id=ваш_app_id&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=friends,photos,groups,offline&response_type=token&v=5.131")
                        logger.info("2. Скопируйте token из адресной строки")
                        raise
        except ApiError as e:
            logger.critical(f"Ошибка подключения: {e}")
            raise

    def _handle_event(self, event) -> None:
        """Обрабатывает входящее событие"""
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                try:
                    # Проверяем наличие payload более безопасным способом
                    payload = getattr(event, 'payload', None)
                    if payload:
                        try:
                            payload_data = json.loads(payload)
                            self._handle_payload(user_id, payload_data)
                        except json.JSONDecodeError:
                            self._handle_text(user_id, event.text.lower())
                    else:
                        self._handle_text(user_id, event.text.lower())
                except Exception as e:
                    logger.error(f"Ошибка обработки команды: {e}", exc_info=True)
                    self._send_message(user_id, "Произошла ошибка при обработке команды. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Ошибка обработки события: {e}", exc_info=True)

    def _handle_payload(self, user_id: int, payload: Dict) -> None:
        """Обрабатывает действия из интерактивной клавиатуры

        Args:
            user_id: ID пользователя, отправившего действие
            payload: Словарь с данными действия

        Обрабатывает следующие типы действий:
        - add_fav: добавление пользователя в избранное
        - like: лайк фотографии (с проверкой дублирования)
        - next: показать следующего пользователя
        - block: добавление пользователя в черный список
        """
        try:
            # Проверка валидности payload
            if not payload or not isinstance(payload, dict):
                logger.error(f"Получен некорректный payload: {payload}")
                self._send_message(user_id, "❌ Ошибка: неверный формат действия")
                return

            # Логирование полученного payload для отладки
            logger.debug(f"Обработка payload от user_id={user_id}: {payload}")

            action = payload.get('type')
            if not action:
                logger.error(f"Payload не содержит тип действия: {payload}")
                self._send_message(user_id, "❌ Неизвестное действие")
                return

            # Обработка разных типов действий
            if action == "add_fav":
                self._handle_add_favorite(user_id, payload)

            elif action == "like":
                self._handle_like(user_id, payload)

            elif action == "next":
                self._handle_next_user(user_id)

            elif action == "block":
                self._handle_block(user_id, payload)

            else:
                logger.error(f"Неизвестный тип действия: {action}")
                self._send_message(user_id, "⚠️ Неизвестное действие")

        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON в payload: {payload}")
            self._send_message(user_id, "❌ Ошибка: неверный формат данных")
        except KeyError as e:
            logger.error(f"Отсутствует обязательное поле в payload: {e}")
            self._send_message(user_id, f"❌ Ошибка: отсутствует поле {e}")
        except Exception as e:
            logger.error(f"Критическая ошибка обработки payload: {e}", exc_info=True)
            self._send_message(user_id, "❌ Произошла ошибка при обработке действия")

    def _handle_add_favorite(self, user_id: int, payload: Dict) -> None:
        """Обрабатывает добавление в избранное"""
        if 'user_id' not in payload:
            logger.error(f"Отсутствует user_id в add_fav: {payload}")
            self._send_message(user_id, "❌ Ошибка: не указан пользователь")
            return

        fav_id = payload['user_id']
        try:
            # Получаем информацию о пользователе для сообщения
            fav_info = self.vk_handler.get_user_info(fav_id)
            name = f"{fav_info.get('first_name', '')} {fav_info.get('last_name', '')}" if fav_info else "Пользователь"

            # Проверяем, есть ли уже в избранном
            favorites = self.db.get_favorites(user_id)
            if fav_id in favorites:
                self._send_message(user_id, f"ℹ️ {name} уже в вашем избранном")
                return

            # Пытаемся добавить
            if self.db.add_favorite(user_id, fav_id):
                self._send_message(user_id, f"✅ {name} добавлен(а) в избранное!")
            else:
                self._send_message(user_id, "❌ Ошибка при добавлении в избранное")

        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")
            self._send_message(user_id, "❌ Ошибка при добавлении в избранное")

    def _handle_like(self, user_id: int, payload: Dict) -> None:
        """Обрабатывает лайк фотографии"""
        required_fields = ['photo_id', 'owner_id']
        missing = [field for field in required_fields if field not in payload]
        if missing:
            logger.error(f"Отсутствуют поля в like: {missing}")
            self._send_message(user_id, f"❌ Ошибка: отсутствуют поля {', '.join(missing)}")
            return

        photo_id = payload['photo_id']
        owner_id = payload['owner_id']

        try:
            # Проверяем, не ставил ли уже лайк
            if self.db.has_liked_photo(user_id, photo_id):
                self._send_message(user_id, "❤️ Вы уже лайкали это фото ранее!")
                return

            # Ставим лайк через VK API и сохраняем в БД
            if self.vk_handler.like_photo(photo_id, owner_id, user_id):
                # Получаем информацию о владельце фото для красивого сообщения
                user_info = self.vk_handler.get_user_info(owner_id)
                name = f"{user_info.get('first_name', 'Пользователь')}" if user_info else "Пользователю"
                self._send_message(user_id, f"❤️ Лайк {name} успешно поставлен!")
            else:
                self._send_message(user_id, "❌ Не удалось поставить лайк")
        except ApiError as e:
            if e.code == 15:  # Access denied
                self._send_message(user_id, "❌ Невозможно поставить лайк (доступ запрещен)")
            else:
                logger.error(f"API error in like: {e}")
                self._send_message(user_id, "❌ Ошибка API при постановке лайка")
        except Exception as e:
            logger.error(f"Ошибка обработки лайка: {e}")
            self._send_message(user_id, "❌ Ошибка при обработке лайка")

    def _handle_next_user(self, user_id: int) -> None:
        """Обрабатывает запрос на следующего пользователя"""
        try:
            self._show_next_user(user_id)
        except Exception as e:
            logger.error(f"Ошибка переключения пользователя: {e}")
            self._send_message(user_id, "❌ Ошибка при поиске следующего пользователя")

    def _handle_block(self, user_id: int, payload: Dict) -> None:
        """Обрабатывает добавление в черный список"""
        if 'user_id' not in payload:
            logger.error(f"Отсутствует user_id в block: {payload}")
            self._send_message(user_id, "❌ Ошибка: не указан пользователь")
            return

        block_id = payload['user_id']
        try:
            if self.db.add_to_blacklist(user_id, block_id):
                # Получаем информацию о заблокированном пользователе
                block_info = self.vk_handler.get_user_info(block_id)
                if block_info:
                    name = f"{block_info.get('first_name', '')} {block_info.get('last_name', '')}"
                    self._send_message(user_id, f"🚫 {name} добавлен(а) в ЧС")
                else:
                    self._send_message(user_id, "🚫 Пользователь добавлен в ЧС")
                self._show_next_user(user_id)
            else:
                self._send_message(user_id, "⚠️ Пользователь уже в ЧС")
        except Exception as e:
            logger.error(f"Ошибка добавления в ЧС: {e}")
            self._send_message(user_id, "❌ Ошибка при добавлении в ЧС")

    def _handle_text(self, user_id: int, text: str) -> None:
        """Обрабатывает текстовые команды"""
        try:
            if text in ['привет', 'начать', 'старт']:
                self._send_message(
                    user_id,
                    "👋 Привет! Я бот для знакомств.\n"
                    "🔍 Начни поиск командой 'поиск'\n"
                    "⭐ Посмотреть избранное: 'избранное'",
                    self._main_keyboard()
                )
            elif text == 'поиск':
                self._start_search(user_id)
            elif text == 'избранное':
                self._show_favorites(user_id)
            else:
                self._send_message(
                    user_id,
                    "ℹ️ Используйте кнопки или команды:\n"
                    "🔍 'поиск' - начать поиск\n"
                    "⭐ 'избранное' - ваши избранные",
                    self._main_keyboard()
                )
        except Exception as e:
            logger.error(f"Ошибка обработки текста: {e}")
            self._send_message(user_id, "❌ Произошла ошибка")

    def _start_search(self, user_id: int) -> None:
        """Начинает новый поиск"""
        try:
            logger.info(f"Начало поиска для пользователя {user_id}")

            # Получаем информацию о пользователе
            user_info = self.vk_handler.get_user_info(user_id)
            if not user_info:
                self._send_message(user_id, "❌ Не удалось получить ваши данные")
                return

            # Устанавливаем параметры поиска
            age = user_info.get('age', 25)
            search_params = {
                'user_id': user_id,
                'sex': 1 if user_info.get('sex') == 2 else 2,
                'city': user_info.get('city', {}).get('title') if isinstance(user_info.get('city'),
                                                                             dict) else 'Не указан',
                'age_from': max(age - 5, 18),
                'age_to': age + 5,
                'interests': user_info.get('interests', '')
            }

            # Ищем пользователей
            users = self.db.get_cached_results(user_id, search_params)
            if users is None:
                users = self.vk_handler.search_users(search_params) or []
                if users:
                    self.db.cache_results(user_id, search_params, users)

            # Фильтруем результаты
            users = [
                u for u in users
                if not self.db.check_blacklist(user_id, u.get('id'))
                   and u.get('id') not in self.db.get_favorites(user_id)
            ]

            if not users:
                self._send_message(user_id, "😔 Нет подходящих пользователей")
                return

            # Сохраняем состояние
            self.user_states[user_id] = {
                'users': users,
                'index': 0
            }

            self._show_user(user_id)

        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            self._send_message(user_id, "❌ Ошибка при поиске")

    def _show_user(self, user_id: int) -> None:
        """Показывает карточку пользователя"""
        try:
            if user_id not in self.user_states:
                self._send_message(user_id, "🔍 Начните поиск командой 'поиск'")
                return

            current = self.user_states[user_id]
            if current['index'] >= len(current['users']):
                self._send_message(user_id, "😔 Пользователи закончились")
                return

            user = current['users'][current['index']]
            photos = self.vk_handler.get_photos(user['id'])

            if not photos:
                self._show_next_user(user_id)
                return

            # Формируем сообщение
            profile_link = f"https://vk.com/id{user['id']}"
            message = (
                f"👤 {user.get('first_name', '')} {user.get('last_name', '')}\n"
                f"🎂 Возраст: {user.get('age', 'не указан')}\n"
                f"🏙️ Город: {user.get('city', {}).get('title', 'не указан')}\n"
                f"🔗 Ссылка: {profile_link}"
            )

            # Формируем вложения (фото)
            attachments = [f"photo{photo['owner_id']}_{photo['id']}" for photo in photos[:3]]

            # Создаем клавиатуру
            keyboard = self.vk_handler.create_keyboard(user['id'], photos[0]['id'])

            self._send_message(
                user_id=user_id,
                message=message,
                keyboard=keyboard,
                attachment=",".join(attachments)
            )

        except Exception as e:
            logger.error(f"Ошибка показа пользователя: {e}")
            self._send_message(user_id, "❌ Ошибка при загрузке профиля")

    def _show_next_user(self, user_id: int) -> None:
        """Показывает следующего пользователя"""
        if user_id in self.user_states:
            self.user_states[user_id]['index'] += 1
            self._show_user(user_id)
        else:
            self._send_message(user_id, "🔍 Начните поиск командой 'поиск'")

    def _show_favorites(self, user_id: int) -> None:
        """Показывает избранных пользователей"""
        try:
            favorites = self.db.get_favorites(user_id)
            if not favorites:
                self._send_message(user_id, "⭐ Список избранных пуст")
                return

            message = "⭐ Ваши избранные:\n" + "\n".join(
                f"{i + 1}. vk.com/id{uid}" for i, uid in enumerate(favorites[:10]))

            self._send_message(user_id, message, self._main_keyboard())
        except Exception as e:
            logger.error(f"Ошибка показа избранных: {e}")
            self._send_message(user_id, "❌ Ошибка при загрузке избранных")

    def _send_message(self, user_id: int, message: str,
                      keyboard: Optional[str] = None,
                      attachment: Optional[str] = None) -> None:
        """Отправляет сообщение пользователю"""
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id(),
                'dont_parse_links': 1
            }

            if keyboard:
                params['keyboard'] = keyboard
            if attachment:
                params['attachment'] = attachment

            self.vk.messages.send(**params)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    def _main_keyboard(self) -> str:
        """Создает основную клавиатуру"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Избранное', color=VkKeyboardColor.POSITIVE)
        return keyboard.get_keyboard()


if __name__ == '__main__':
    try:
        bot = Bot()
        bot.run()
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
