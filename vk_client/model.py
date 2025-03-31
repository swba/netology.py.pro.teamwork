from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


class ModelBase(ABC):
    """Base model class"""

    @classmethod
    def sanitize_values(cls, values: Dict):
        return {k: v for k, v in values.items() if k in cls.__annotations__}

    @classmethod
    def from_values(cls, values: Dict):
        kwargs = cls.sanitize_values(values)
        return cls(**kwargs)


@dataclass
class VkLastSeen(ModelBase):
    """VK "last seen" model"""
    time: int
    platform: int


@dataclass
class VkPlace(ModelBase):
    """Base model of a place (city, country) in VK"""
    id: int
    title: str


@dataclass
class VkUser(ModelBase):
    """VK user model"""
    id: int
    first_name: str
    last_name: str
    can_access_closed: bool = None
    is_closed: bool = None
    about: str = None
    bdate: str = None
    city: VkPlace = None
    country: VkPlace = None
    has_photo: int = None
    is_friend: int = None
    last_seen: VkLastSeen = None
    photo_100: str = None
    photo_id: str = None
    photo_max: str = None
    relation: int = None
    sex: int = None
    status: str = None

    def __post_init__(self):
        # Convert city and country to objects.
        for field in ['city', 'country']:
            if data := getattr(self, field):
                setattr(self, field, VkPlace(**data))
        # Convert "Last seen" to object.
        if last_seen := getattr(self, 'last_seen'):
            self.last_seen = VkLastSeen(**last_seen)

    @property
    def age(self) -> Optional[int]:
        """Returns user's age"""
        if self.bdate and self.bdate.count('.') == 2:
            if dt := datetime.strptime(self.bdate, '%d.%m.%Y'):
                # @see https://stackoverflow.com/a/9754466/5111076
                today = datetime.today()
                return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))


@dataclass
class VkPhotoCopy(ModelBase):
    """VK photo copy model"""
    type: str
    url: str
    width: int
    height: int


@dataclass
class VkCounterBase(ModelBase):
    """Base model for a counter object"""
    count: int


@dataclass
class VkPhotoLikes(VkCounterBase):
    """VK photo likes model"""
    user_likes: int


@dataclass
class VkPhoto(ModelBase):
    """VK photo model"""
    id: int
    album_id: int
    owner_id: int
    user_id: int = None
    text: str = None
    date: int = None
    sizes: List[VkPhotoCopy] = None
    width: int = None
    height: int = None
    likes: VkPhotoLikes = None
    comments: VkCounterBase = None
    reposts: VkCounterBase = None
    tags: VkCounterBase = None

    def __post_init__(self):
        # Convert sizes to objects.
        if sizes := getattr(self, 'sizes'):
            self.sizes = [VkPhotoCopy(**item) for item in sizes]
        # Convert comments, reposts and tags to objects.
        for field in ['comments', 'reposts', 'tags']:
            if data := getattr(self, field):
                setattr(self, field, VkCounterBase(**data))
        # Convert likes to object.
        if likes := getattr(self, 'likes'):
            self.likes = VkPhotoLikes(**likes)
