from typing import Required, TypedDict

from .types import TypeBoolean, TypeLang, TypeSex, TypeSort, TypeStatus


class ParamsGeneral(TypedDict, total=False):
    """General VK API parameters

    See https://dev.vk.com/en/api/api-requests#General%20parameters

    """
    lang: TypeLang
    test_mode: TypeBoolean


class ParamsPhotosGet(ParamsGeneral, total=False):
    """VK API: photos.get parameters

    See https://dev.vk.com/en/method/photos.get#Parameters

    """
    owner_id: str
    album_id: str
    photo_ids: str
    rev: TypeBoolean
    extended: TypeBoolean
    feed_type: str
    feed: int
    photo_sizes: TypeBoolean
    offset: int
    count: int


class ParamsUsersSearch(ParamsGeneral, total=False):
    """VK API: users.search parameters

    See https://dev.vk.com/en/method/users.search#Parameters

    """
    q: str
    sort: TypeSort
    offset: int
    count: int
    fields: str
    city: int
    country: int
    sex: TypeSex
    status: TypeStatus
    age_from: int
    age_to: int
    birth_day: int
    birth_month: int
    birth_year: int
    online: TypeBoolean
    has_photo: TypeBoolean
