from typing import List, Optional, Type

from environs import env
import sqlalchemy as sq
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .model import create_tables, UserInfo, UserPreferences, UserFavorites, UserBlackList


class Database:
    """Provides API to work with the database"""

    @staticmethod
    def get_engine() -> Engine:
        """Creates and returns an SQLAlchemy engine"""
        db_host = env('DB_HOST')
        db_port = env('DB_PORT')
        db_name = env('DB_NAME')
        db_user = env('DB_USER')
        db_pass = env('DB_PASS')

        dsn = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
        return sq.create_engine(dsn)

    def __init__(self):
        self.engine = self.get_engine()
        create_tables(self.engine)

    def add_user(self, vk_id: int, first_name: str, last_name: str,
                 sex: int = None, relation: int = None, bdate: str = None,
                 city: int = None, university: int = None) -> Optional[UserInfo]:
        """Добавляет пользователя в БД"""
        with Session(self.engine) as session:
            try:
                user = UserInfo(vk_id=vk_id, first_name=first_name,
                                last_name=last_name, sex=sex, relation=relation,
                                bdate=bdate, city=city, university=university)
                session.add(user)
                session.commit()
                return user
            except Exception as e:
                print(e)

    def get_user(self, *, user_id: int = None, vk_id: int = None) -> Optional[UserInfo]:
        """Возвращает пользователя по его ID или ID ВКонтакте"""
        with Session(self.engine) as session:
            if user_id:
                return session.query(UserInfo).filter(UserInfo.id == user_id).first()
            elif vk_id:
                return session.query(UserInfo).filter(UserInfo.vk_id == vk_id).first()

    def get_user_preferences(self, user: UserInfo) -> Optional[UserPreferences]:
        """Возвращает предпочтения поиска пользователя"""
        with Session(self.engine) as session:
            return session.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()

    def set_user_preferences(self, user: UserInfo, sex: int = None,
                             relation: int = None, age_from: int = None,
                             age_to: int = None, city: int = None) -> Optional[UserPreferences]:
        """Сохраняет предпочтения поиска пользователя"""
        with Session(self.engine) as session:
            try:
                if prefs := self.get_user_preferences(user):
                    prefs.sex = sex
                    prefs.relation = relation
                    prefs.age_from = age_from
                    prefs.age_to = age_to
                    prefs.city = city
                else:
                    prefs = UserPreferences(sex=sex, relation=relation,
                                            age_from=age_from, age_to=age_to,
                                            city=city)
                    session.add(prefs)
                session.commit()
                return prefs
            except Exception as e:
                print(e)

    def is_user_favorite(self, user: UserInfo, vk_id: int) -> bool:
        """Проверяет, находится ли пользователь в избранном"""
        with Session(self.engine) as session:
            return session.query(UserFavorites).filter(
                UserFavorites.user_id == user.id and
                UserFavorites.vk_id == vk_id
            ).count() > 0

    def add_to_user_favorites(self, user: UserInfo, vk_id: int, first_name: str,
                              last_name: str, sex: int = None, relation: int = None,
                              bdate: str = None, city: int = None,
                              university: int = None) -> Optional[UserFavorites]:
        """Добавляет пользователя в избранное"""
        with Session(self.engine) as session:
            try:
                user = UserFavorites(user=user, vk_id=vk_id, first_name=first_name,
                                     last_name=last_name, sex=sex, relation=relation,
                                     bdate=bdate, city=city, university=university)
                session.add(user)
                session.commit()
                return user
            except Exception as e:
                print(e)

    def remove_from_user_favorites(self, user: UserInfo, vk_id: int):
        """Удаляет пользователя из избранного"""
        with Session(self.engine) as session:
            try:
                session.query(UserFavorites).filter(
                    UserFavorites.user_id == user.id and
                    UserFavorites.vk_id == vk_id
                ).delete()
                session.commit()
            except Exception as e:
                print(e)

    def get_user_favorites(self, user: UserInfo) -> List[Type[UserFavorites]]:
        """Возвращает всех избранных пользователей"""
        with Session(self.engine) as session:
            return session.query(UserFavorites).filter(
                UserFavorites.user_id == user.id
            ).all()

    def is_user_black_listed(self, user: UserInfo, vk_id: int) -> bool:
        """Проверяет, находится ли пользователь в чёрном списке"""
        with Session(self.engine) as session:
            return session.query(UserBlackList).filter(
                UserBlackList.user_id == user.id and
                UserBlackList.vk_id == vk_id
            ).count() > 0

    def add_to_user_black_list(self, user: UserInfo, vk_id: int, first_name: str,
                              last_name: str, sex: int = None, relation: int = None,
                              bdate: str = None, city: int = None,
                              university: int = None) -> Optional[UserBlackList]:
        """Добавляет пользователя в чёрный список"""
        with Session(self.engine) as session:
            try:
                user = UserBlackList(user=user, vk_id=vk_id, first_name=first_name,
                                     last_name=last_name, sex=sex, relation=relation,
                                     bdate=bdate, city=city, university=university)
                session.add(user)
                session.commit()
                return user
            except Exception as e:
                print(e)

    def remove_from_user_black_list(self, user: UserInfo, vk_id: int):
        """Удаляет пользователя из чёрного списка"""
        with Session(self.engine) as session:
            try:
                session.query(UserBlackList).filter(
                    UserBlackList.user_id == user.id and
                    UserBlackList.vk_id == vk_id
                ).delete()
                session.commit()
            except Exception as e:
                print(e)

    def get_user_black_list(self, user: UserInfo) -> List[Type[UserBlackList]]:
        """Возвращает чёрный список пользователей"""
        with Session(self.engine) as session:
            return session.query(UserBlackList).filter(
                UserBlackList.user_id == user.id
            ).all()
