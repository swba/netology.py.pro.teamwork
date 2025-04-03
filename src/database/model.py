from typing import List

import sqlalchemy as sq
from sqlalchemy import Engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.types import Integer, String

from src.utils import get_age, get_gender, get_relation


Base = declarative_base()


class UserBase(Base):
    """Базовая модель для всех таблиц с информацией о пользователе"""

    id: Mapped[int] = mapped_column(primary_key=True)
    # ID пользователя ВКонтакте.
    vk_id: Mapped[int] = mapped_column(nullable=False)
    # Имя.
    first_name: Mapped[str] = mapped_column(nullable=False)
    # Фамилия.
    last_name: Mapped[str] = mapped_column(nullable=False)
    # Пол.
    sex: Mapped[int] = mapped_column(nullable=True)
    # Семейное положение.
    relation: Mapped[int] = mapped_column(nullable=True)
    # Дата рождения.
    bdate: Mapped[str] = mapped_column(String(10), nullable=True)
    # Идентификатор города.
    city: Mapped[int] = mapped_column(nullable=True)
    # Идентификатор ВУЗа.
    university: Mapped[int] = mapped_column(nullable=True)

    def __str__(self):
        return (f"ID ВКонтакте: {self.vk_id}\n"
                f"Имя и фамилия: {self.first_name} {self.last_name}\n"
                f"Семейное положение: {get_relation(self.relation)}"
                f"Пол: {get_gender(self.sex)}\n"
                f"Возраст: {get_age(self.bdate)}\n"
                f"Идентификатор ВУЗа: {self.univer}\n"
                f"Идентификатор города: {self.city}")


class UserInfo(UserBase):
    """ Модель данных пользователя ВКонтакте"""

    __tablename__ = "user_info"

    preferences: Mapped['UserPreferences'] = relationship(
        back_populates="user_info",
        cascade = "all, delete-orphan"
    )

    favorites: Mapped[List['UserFavorites']] = relationship(
        back_populates = "user_info",
        cascade = "all, delete-orphan"
    )

    black_list: Mapped[List['UserBlackList']] = relationship(
        back_populates = "user_info",
        cascade = "all, delete-orphan"
    )


class UserPreferences(Base):
    """Модель предпочтений пользователя для поиска партнера"""

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = sq.Column(sq.Integer, sq.ForeignKey("user_info.id"), nullable=False)
    sex: Mapped[int] = mapped_column(nullable=True)
    relation: Mapped[int] = mapped_column(nullable=True)
    age_from: Mapped[int] = mapped_column(nullable=True)
    age_to: Mapped[int] = mapped_column(nullable=True)
    city: Mapped[int] = mapped_column(nullable=True)

    user = relationship(UserInfo, backref="preferences")

    def __str__(self):
        return (f"Ваши критерии поиска:\n"
                f"1. Пол: {get_gender(self.sex)}\n"
                f"2. Семейное положение: {get_relation(self.relation)}\n"
                f"3. Нижний возраст: {self.age_from}\n"
                f"4. Верхний возраст: {self.age_to}\n"
                f"5. Идентификатор города: {self.city}")


class UserFavorites(UserBase):
    """ Модель профилей, которые понравились пользователю"""

    __tablename__ = "user_favorites"

    user_id: Mapped[int] = sq.Column(sq.Integer, sq.ForeignKey("user_info.id"), nullable=False)

    user = relationship(UserInfo, backref="favorites")


class UserBlackList(UserBase):
    """Модель людей в черном списке для игнорирования в дальнейшем поиске"""

    __tablename__ = "user_black_list"

    user_id: Mapped[int] = sq.Column(sq.Integer, sq.ForeignKey("user_info.id"), nullable=False)

    user = relationship(UserInfo, backref="black_list")


def create_tables(engine: Engine):
    """Creates model tables in the database"""
    Base.metadata.create_all(engine)

def drop_tables(engine: Engine):
    """Drops all model tables"""
    Base.metadata.drop_all(engine)
