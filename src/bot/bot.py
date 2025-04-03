import json
import time
import logging
from typing import Dict, Optional

from environs import env
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from src.database import Database
from src.vk_client import VkClient


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Bot:

    def __init__(self) -> None:
        """Инициализация бота с проверкой токенов"""
        self._check_env_vars()

        try:
            # Инициализация подключения к VK API
            self.vk_session = VkApi(token=env('VK_BOT_TOKEN'))
            self.vk = self.vk_session.get_api()

            # Проверка подключения к VK API
            self._check_vk_connection()

            # Инициализация LongPoll
            self.longpoll = VkLongPoll(self.vk_session)

            logger.info("✅ LongPoll инициализирован")

            # Инициализация базы данных
            self.db = Database()
            logger.info(f"🛢️ Подключено к PostgreSQL: {env('DB_NAME')}")

            # Инициализация обработчика VK
            self.vk_client = VkClient(env('VK_API_TOKEN'))

            # Словарь для хранения состояний пользователей
            self.user_states = {}

        except Exception as e:
            logger.critical(f"Ошибка инициализации бота: {e}")
            raise

    def _check_vk_connection(self):
        """Проверяет подключение к VK API"""
        try:
            group_info = self.vk.groups.getById()
            logger.info(f"✅ Успешное подключение к группе: {group_info[0]['name']}")
        except Exception as e:
            logger.critical(f"❌ Ошибка подключения к VK API: {e}")
            raise RuntimeError(f"VK API connection failed: {e}")

    @staticmethod
    def _check_env_vars():
        """Проверка наличия всех необходимых переменных окружения"""
        required_vars = ['VK_BOT_TOKEN', 'VK_API_TOKEN']
        missing = [var for var in required_vars if not env(var)]

        if missing:
            logger.critical(f"Отсутствуют переменные: {', '.join(missing)}")

            # Создаем/обновляем .env файл с шаблоном
            with open('.env', 'w') as f:
                for var in required_vars:
                    f.write(f"{var}=\n")

            raise ValueError(
                "Файл .env обновлен. Пожалуйста, заполните недостающие переменные и перезапустите бота."
            )

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
            logger.info("Все соединения закрыты")

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
        - like: лайк фотографии
        - next: показать следующего пользователя
        - block: добавление пользователя в черный список
        """
        try:
            # Проверка валидности payload
            if not isinstance(payload, dict):
                logger.error(f"Получен некорректный payload: {payload}")
                self._send_message(user_id, "❌ Ошибка: неверный формат действия")
                return

            action = payload.get('type')
            if not action:
                logger.error(f"Payload не содержит тип действия: {payload}")
                self._send_message(user_id, "❌ Неизвестное действие")
                return

            # Обработка разных типов действий
            if action == "add_fav":
                if 'user_id' not in payload:
                    logger.error(f"Отсутствует user_id в add_fav: {payload}")
                    self._send_message(user_id, "❌ Ошибка: не указан пользователь")
                    return

                fav_id = payload['user_id']
                if self.db.add(user_id, fav_id):
                    self._send_message(user_id, "✅ Пользователь добавлен в избранное!")
                else:
                    self._send_message(user_id, "⚠️ Пользователь уже в избранном")

            elif action == "like":
                if 'photo_id' not in payload:
                    logger.error(f"Отсутствует photo_id в like: {payload}")
                    self._send_message(user_id, "❌ Ошибка: не указана фотография")
                    return

                photo_id = payload['photo_id']
                owner_id = payload.get('owner_id', payload.get('user_id'))

                if not owner_id:
                    logger.error(f"Отсутствует owner_id в like: {payload}")
                    self._send_message(user_id, "❌ Ошибка: не указан владелец фото")
                    return

                if self.vk_client.like_photo(photo_id, owner_id):
                    self._send_message(user_id, "❤️ Лайк поставлен!")
                else:
                    self._send_message(user_id, "❌ Не удалось поставить лайк")

            elif action == "next":
                self._show_next_user(user_id)

            elif action == "block":
                if 'user_id' not in payload:
                    logger.error(f"Отсутствует user_id в block: {payload}")
                    self._send_message(user_id, "❌ Ошибка: не указан пользователь")
                    return

                block_id = payload['user_id']
                if self.db.add_to_blacklist(user_id, block_id):
                    self._send_message(user_id, "🚫 Пользователь добавлен в ЧС")
                    self._show_next_user(user_id)
                else:
                    self._send_message(user_id, "⚠️ Пользователь уже в ЧС")

            else:
                logger.error(f"Неизвестный тип действия: {action}")
                self._send_message(user_id, "⚠️ Неизвестное действие")

        except KeyError as e:
            logger.error(f"Отсутствует обязательное поле в payload: {e}")
            self._send_message(user_id, "❌ Ошибка: неверные данные действия")
        except Exception as e:
            logger.error(f"Критическая ошибка обработки payload: {e}", exc_info=True)
            self._send_message(user_id, "❌ Произошла ошибка при обработке действия")

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
            user_info = self.vk_client.get_user(user_id)
            if not user_info:
                self._send_message(user_id, "❌ Не удалось получить ваши данные")
                return

            # Устанавливаем параметры поиска
            age = user_info.age or 25
            search_params = {
                'sex': 1 if user_info.sex == 2 else 2,
                'city': user_info.city.id if user_info.city else None,
                'age_from': max(age - 5, 18),
                'age_to': age + 5,
                'has_photo': 1
            }

            # Ищем пользователей
            # todo: Не разумнее ли сохранять кеш в памяти, а не в базе данных? Как его экспирировать в БД?
            users = self.db.get_cached_results(user_id, search_params)
            if users is None:
                # todo: добавить людей из избранного и из чёрного списка в исключения.
                users = self.vk_client.search_users(exclude=[user_id], **search_params) or []
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
            photos = self.vk_client.get_user_photos(user['id'], top=3)

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
            attachments = [f"photo{photo.owner_id}_{photo.id}" for photo in photos]

            # Создаем клавиатуру
            keyboard = self.vk.create_keyboard(user['id'], photos[0].id)

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

    @staticmethod
    def _main_keyboard() -> str:
        """Создает основную клавиатуру"""
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Поиск', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Избранное', color=VkKeyboardColor.POSITIVE)
        return keyboard.get_keyboard()
