from typing import List, Optional, Unpack

import vk_api

from .model import VkUser, VkPhoto
from .params import ParamsPhotosGet, ParamsUsersSearch


class VkClient:
    """A client for VK API

    See https://dev.vk.com/ru/reference

    """
    DEFAULT_VERSION = '5.199'

    def __init__(self, token: str, version: str = None):
        """VK API client constructor

        Args:
            token: VK API access token.
            version: (optional) VK API version.

        Raises:
            vk_api.AuthError: In case of authentication error.

        """
        self._vk_session = vk_api.VkApi(
            token=token,
            api_version=version or self.DEFAULT_VERSION
        )

    def get_user(self, user_id: int, fields: str = 'about,bdate,city,sex,photo_max') -> Optional[VkUser]:
        """Retrieves user info.

        @see https://dev.vk.com/ru/method/users.get

        Args:
            user_id: VK user ID.
            fields: (optional) List of additional fields to fetch.

        Returns:
            VK user object.

        Raises:
            vk_api.VkApiError: If VK API responded with an error.

        """
        users = self._vk_session.method('users.get', {
            'user_ids': str(user_id),
            'fields': fields
        })
        return VkUser.from_values(users[0]) if users else None

    def get_users(self, user_ids: List[int], fields: str = 'about,bdate,city,sex,photo_max') -> List[VkUser]:
        """Retrieves users info.

        @see https://dev.vk.com/ru/method/users.get

        Args:
            user_ids: IDs of VK users.
            fields: (optional) List of additional fields to fetch.

        Returns:
            List of VK user objects.

        Raises:
            vk_api.VkApiError: If VK API responded with an error.

        """
        users = self._vk_session.method('users.get', {
            'user_ids': ','.join(str(user_id) for user_id in user_ids),
            'fields': fields
        })
        return [VkUser.from_values(user) for user in users]

    def search_users(self, exclude: List[int] = None, **params: Unpack[ParamsUsersSearch]) -> List[VkUser]:
        """Searches users.

        Args:
            exclude: (optional) IDs of users to exclude from search.
            params: (optional) Parameters to be passed to the search method.

        Returns:
            List of VK user objects.

        Raises:
            vk_api.VkApiError: If VK API responded with an error.

        """
        result = self._vk_session.method('users.search', params)
        users = result['items']
        return [VkUser.from_values(user) for user in users if not exclude or user['id'] not in exclude]

    def get_user_photos(self, user_id: int, top: int = None, **params: Unpack[ParamsPhotosGet]) -> List[VkPhoto]:
        """Returns user photos

        See https://dev.vk.com/ru/method/photos.get

        Args:
            user_id: ID of VK user to get photos of.
            top: (optional) If set, that many photos will be returned,
                sorted by count of likes.
            params: (optional) Additional method parameters. Default
                value for `album_id` is "profile". If top is not None,
                then `extended` is always 1 and `count` is always 1000.

        Returns:
            Parsed endpoint response containing photos information.

        Raises:
            VKError: If VK API responded with an error.

        """
        values = {
            'album_id': 'profile',
            **params,
            'owner_id': user_id,
        }
        if top:
            values['extended'] = 1
            values['count'] = 1000
        result = self._vk_session.method('photos.get', values)
        photos = result['items']
        if top:
            photos.sort(key=lambda photo: photo['likes']['count'], reverse=True)
            photos = photos[:top]
        return [VkPhoto.from_values(photo) for photo in photos]

    def like_photo(self, photo_id: int) -> int:
        """Likes a photo

        Args:
            photo_id: Photo ID.

        Returns:
            Number of photo likes.

        Raises:
            VKError: If VK API responded with an error.

        """
        result = self._vk_session.method('likes.add', {
            'type': 'photo',
            'item_id': photo_id,
        })
        return result['likes']

    def unlike_photo(self, photo_id: int) -> int:
        """Unlikes a photo

        Args:
            photo_id: Photo ID.

        Returns:
            Number of photo likes.

        Raises:
            VKError: If VK API responded with an error.

        """
        result = self._vk_session.method('likes.delete', {
            'type': 'photo',
            'item_id': photo_id,
        })
        return result['likes']
