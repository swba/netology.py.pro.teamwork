from environs import env
import pytest

from vk_client import VkClient


TEST_USERS = [
    {
        'id': 1,
        'first_name': 'Павел',
        'last_name': 'Дуров',
        'age': 40,
        'photos_profile': {
            'count': 9,
            'id_first': 215187843
        },
        'photos_wall': {
            'count': 230,
            'id_first': 228175223,
            'id_top': 285102078
        },
    },
    {
        'id': 153151548,
        'first_name': 'Юрий',
        'last_name': 'Шевчук',
        'photos_profile': {
            'count': 2,
            'id_first': 456239017
        },
        'photos_wall': {
            'count': 7,
            'id_first': 304092328,
            'id_top': 457239090
        },
    },
]


class TestVkClient:

    def setup_method(self):
        env.read_env()
        vk_token = env('VK_API_TOKEN')
        self.vk_client = VkClient(vk_token)

    @pytest.mark.parametrize('user', TEST_USERS)
    def test_get_user(self, user):
        """Tests get_user method"""
        vk_user = self.vk_client.get_user(user['id'])
        assert vk_user.first_name == user['first_name']
        assert vk_user.last_name == user['last_name']
        if 'age' in user:
            assert vk_user.age == user['age']

    @pytest.mark.parametrize('users', [TEST_USERS])
    def test_get_users(self, users):
        """Tests get_users method"""
        vk_users = self.vk_client.get_users([user['id'] for user in users])
        for vk_user, user in zip(vk_users, users):
            assert vk_user.id == user['id']
            assert vk_user.first_name == user['first_name']
            assert vk_user.last_name == user['last_name']
            if 'age' in user:
                assert vk_user.age == user['age']

    @pytest.mark.parametrize('user', TEST_USERS)
    def test_search_users(self, user):
        """Tests search_users method"""
        vk_users = self.vk_client.search_users(q=f"{user['first_name']} {user['last_name']}")
        assert vk_users[0].id == user['id']

    @pytest.mark.parametrize('user', TEST_USERS)
    def test_get_user_photos(self, user):
        """Tests get_user_photos method"""
        # Profile photos.
        photos = self.vk_client.get_user_photos(user['id'])
        assert len(photos) == user['photos_profile']['count']
        assert photos[0].id == user['photos_profile']['id_first']
        # Wall photos.
        photos = self.vk_client.get_user_photos(user['id'], album_id='wall', count=1000)
        assert len(photos) == user['photos_wall']['count']
        assert photos[0].id == user['photos_wall']['id_first']
        # Top-3 wall photos.
        photos = self.vk_client.get_user_photos(user['id'], top=3, album_id='wall')
        assert photos[0].id == user['photos_wall']['id_top']
