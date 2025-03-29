import vk_api
from vk_api.exceptions import ApiError


class VKHandler:
    def __init__(self, token):
        self.vk = vk_api.VkApi(token=token)
        self.api = self.vk.get_api()

    def get_user_info(self, user_id):
        try:
            response = self.api.users.get(user_ids=user_id, fields='city,sex,bdate')
            if response:
                user = response[0]
                age = self._parse_age(user.get('bdate'))
                city = user.get('city', {}).get('title', '') if 'city' in user else ''
                return {
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'age': age,
                    'sex': user.get('sex', 0),
                    'city': city
                }
            return None
        except ApiError as e:
            print(f"Ошибка получения данных пользователя: {e}")
            return None

    def _parse_age(self, bdate):
        if not bdate:
            return None
        parts = bdate.split('.')
        if len(parts) < 3:
            return None
        from datetime import date
        today = date.today()
        birth_year = int(parts[2])
        return today.year - birth_year

    def search_users(self, params):
        try:
            response = self.api.users.search(
                count=1000,
                has_photo=1,
                fields='photo_max_orig,city',
                **params
            )
            return response['items']
        except ApiError as e:
            print(f"Ошибка поиска пользователей: {e}")
            return []

    def get_photos(self, user_id):
        try:
            photos = self.api.photos.get(owner_id=user_id, album_id='profile', extended=1)
            sorted_photos = sorted(photos['items'], key=lambda x: x['likes']['count'], reverse=True)
            return sorted_photos[:3]
        except ApiError as e:
            print(f"Ошибка получения фотографий: {e}")
            return []
