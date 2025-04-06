import vk_api
from vk_api.exceptions import ApiError
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VKHandler:
    """Класс для взаимодействия с API ВКонтакте"""

    SEARCH_WEIGHTS = {
        'age': 0.4,
        'city': 0.3,
        'interests': 0.2,
        'friends': 0.1
    }

    def __init__(self, token: str, db=None):
        """Инициализация VK API обработчика"""
        self.token = token
        self.db = db

        try:
            # Инициализация сессии VK API
            self.vk_session = vk_api.VkApi(token=token)
            self.vk = self.vk_session.get_api()  # Основной API клиент
            logger.info("VK API успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации VK API: {e}")
            raise RuntimeError(f"Ошибка инициализации VK API: {e}")

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получает расширенную информацию о пользователе"""
        try:
            response = self.vk.users.get(
                user_ids=user_id,
                fields='sex,city,bdate,interests,music,books,groups'
            )

            if not response or not isinstance(response, list):
                return None

            user_data = response[0]

            return {
                'id': user_id,
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'sex': user_data.get('sex', 0),
                'city': self._parse_city(user_data.get('city')),
                'age': self._calculate_age(user_data.get('bdate')),
                'interests': self._get_interests(user_data),
                'bdate': user_data.get('bdate', '')
            }

        except ApiError as e:
            logger.error(f"API error getting user info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    def search_users(self, search_params: Dict) -> List[Dict]:
        """Поиск пользователей по заданным параметрам"""
        try:
            params = {
                'count': 1000,
                'has_photo': 1,
                'fields': 'city,photo_max_orig,sex,bdate,interests',
                'age_from': search_params.get('age_from', 18),
                'age_to': search_params.get('age_to', 35),
                'sex': search_params.get('sex', 1),
                'city': search_params.get('city_id', 0),
                'status': 6  # Не состоит в браке
            }

            # Удаляем None значения
            params = {k: v for k, v in params.items() if v is not None}

            response = self.vk.users.search(**params)

            if not response or 'items' not in response:
                return []

            return response['items']

        except ApiError as e:
            logger.error(f"API search error: {e}")
            if e.code == 6:  # Слишком много запросов
                time.sleep(0.5)
                return self.search_users(search_params)
            return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_photos(self, user_id: int) -> List[Dict]:
        """Безопасное получение фото (работает даже без прав на tagged)"""
        try:
            # Основные фото профиля
            profile_photos = self.vk.photos.get(
                owner_id=user_id,
                album_id='profile',
                extended=1,
                count=30
            ).get('items', [])

            # Пытаемся получить фото с отметками (если есть права)
            tagged_photos = []
            try:
                tagged_photos = self.vk.photos.getUserPhotos(
                    user_id=user_id,
                    extended=1,
                    count=30
                ).get('items', [])
            except ApiError as e:
                logger.debug(f"No access to tagged photos: {e}")

            # Объединяем и сортируем
            all_photos = sorted(
                profile_photos + tagged_photos,
                key=lambda x: x.get('likes', {}).get('count', 0),
                reverse=True
            )

            return all_photos[:3]  # Топ-3 фото

        except Exception as e:
            logger.error(f"Error getting photos: {e}")
            return []

    def like_photo(self, photo_id: int, owner_id: int, user_id: int) -> bool:
        """
        Ставит лайк на фото и сохраняет информацию в БД

        Args:
            photo_id: ID фотографии
            owner_id: ID владельца фото
            user_id: ID пользователя, который ставит лайк

        Returns:
            True если лайк успешно поставлен, иначе False
        """
        try:
            # Проверяем, не ставили ли уже лайк
            if self.db and self.db.has_liked_photo(user_id, photo_id):
                logger.info(f"User {user_id} already liked photo {photo_id}")
                return False

            # Ставим лайк через API
            self.vk.likes.add(
                type='photo',
                owner_id=owner_id,
                item_id=photo_id
            )

            # Сохраняем информацию о лайке в БД
            if self.db:
                self.db.add_like(user_id, owner_id, photo_id)

            return True
        except ApiError as e:
            logger.error(f"API like error: {e}")
            return False
        except Exception as e:
            logger.error(f"Like error: {e}")
            return False

    def create_keyboard(self, user_id: int, photo_id: int) -> str:
        """Создает интерактивную клавиатуру"""
        keyboard = VkKeyboard(inline=True)

        # Кнопка добавления в избранное
        keyboard.add_button(
            label="❤️ В избранное",
            color=VkKeyboardColor.POSITIVE,
            payload={
                "type": "add_fav",
                "user_id": user_id
            }
        )

        # Кнопка лайка фото
        keyboard.add_button(
            label="👍 Лайк",
            color=VkKeyboardColor.SECONDARY,
            payload={
                "type": "like",
                "photo_id": photo_id,
                "owner_id": user_id
            }
        )

        keyboard.add_line()  # Новая строка

        # Кнопка следующего пользователя
        keyboard.add_button(
            label="➡️ Дальше",
            color=VkKeyboardColor.PRIMARY,
            payload={"type": "next"}
        )

        # Кнопка добавления в ЧС
        keyboard.add_button(
            label="🚫 ЧС",
            color=VkKeyboardColor.NEGATIVE,
            payload={
                "type": "block",
                "user_id": user_id
            }
        )

        return keyboard.get_keyboard()

    # Вспомогательные методы
    def _parse_city(self, city_data: Any) -> Dict:
        """Парсит данные города"""
        if not city_data:
            return {'id': 0, 'title': 'Не указан'}
        if isinstance(city_data, str):
            return {'id': 0, 'title': city_data}
        if isinstance(city_data, dict):
            return {
                'id': city_data.get('id', 0),
                'title': city_data.get('title', 'Не указан')
            }
        return {'id': 0, 'title': 'Не указан'}

    def _calculate_age(self, bdate: Optional[str]) -> int:
        """Вычисляет возраст по дате рождения"""
        if not bdate or len(bdate.split('.')) < 3:
            return 25  # Значение по умолчанию

        try:
            birth_year = int(bdate.split('.')[2])
            return datetime.now().year - birth_year
        except (ValueError, IndexError):
            return 25

    def _get_interests(self, user_data: Dict) -> Dict[str, List[str]]:
        """Формирует словарь интересов"""
        return {
            'music': user_data.get('music', '').lower().split(','),
            'books': user_data.get('books', '').lower().split(','),
            'interests': user_data.get('interests', '').lower().split(','),
            'groups': self._get_group_names(user_data.get('groups', []))
        }

    def _get_group_names(self, group_ids: List[int]) -> List[str]:
        """Получает названия групп по их ID"""
        if not group_ids:
            return []

        try:
            groups = self.vk.groups.getById(group_ids=group_ids)
            return [g['name'].lower() for g in groups]
        except ApiError:
            return []
