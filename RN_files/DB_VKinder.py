import psycopg2
import sqlalchemy
import sqlalchemy as sq
from sqlalchemy import BigInteger
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


Base = declarative_base()


class VKuserInfo(Base):

    ''' Функция для создания таблицы в БД для сохранения
        данных пользователя для дальнейших манипуляций
        в работе бота'''
    
    __tablename__ = "vk_user_info"

    id = sq.Column(sq.Integer, primary_key=True)
    # Сохраняем id пользования
    user_id = sq.Column(sq.BigInteger, unique=True, nullable=True)
    # Сохраняем имя
    first_name = sq.Column(sq.String, unique=False, nullable=False)
    # Сохраняем фамилию
    last_name = sq.Column(sq.String, unique=False, nullable=False)
    # Сохраняем пол
    sex = sq.Column(sq.String(length=7), unique=False, nullable=True)
    # Сохраняем семейлое положение
    relation = sq.Column(sq.String, unique=False, nullable=True)
    # Сохраняем возраст
    age = sq.Column(sq.String, unique=False, nullable=True)
    # Сохраняем город
    city = sq.Column(sq.String, unique=False, nullable=True)
    # Сохраняем университет
    univer = sq.Column(sq.String, unique=False, nullable=True)
    # Сохраняем университет
    closed = sq.Column(sq.String, unique=False, nullable=False)
    # Узнаем, имеются ли фото
    has_photo = sq.Column(sq.String, unique=False, nullable=True)
    # Узнаем музыкальные предпочтения
    music = sq.Column(sq.String, unique=False, nullable=True)

    def __str__(self):
        return (f"Вот Ваша информация:\n"
            f"Ваш ID: {self.user_id}\n"
            f"Имя и фамилия: {self.first_name} {self.last_name}\n"
            f"Ваше семейное положение: {self.relation}"
            f"Ваш пол: {self.sex}\n"
            f"Вы учились в университете: {self.univer}\n"
            f"Ваш возраст: {self.age}\n"
            f"Ваш город: {self.city}\n"
            f"Открытый или закрытый профиль: {self.closed}\n"
            f"Есть ли у Вас фотографии: {self.has_photo}\n"
            f"Ваши музыкальные предпочтения: {self.music}")

class MyPreferences(Base):
    
    ''' Функция для создания таблицы в БД для указания
        пользователем критерии, предпочтения, для поиска партнера'''
    
    __tablename__ = "my_preferences"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.BigInteger, unique=True, nullable=True)
    sex = sq.Column(sq.String(length=7), unique=False, nullable=True)
    relation = sq.Column(sq.String, unique=False, nullable=True)
    age_ner = sq.Column(sq.String, unique=False, nullable=True)
    age_up = sq.Column(sq.String, unique=False, nullable=True)
    city = sq.Column(sq.String, unique=False, nullable=True)

    def __str__(self):
        return (f"Вот Ваши критерии поиска:\n"
            f"1. Пол: {self.sex}\n"
            f"2. Семейное положение: {self.relation}\n"
            f"3. Нижний возраст: {self.age_ner}\n"
            f"4. Верхний возраст: {self.age_up}\n"
            f"5. Город(а): {self.city}")


class FavoriteUsers(Base):
    
    ''' Функция для создания таблицы в БД для сохранения
        пользователем понравившихся ему людей и их данные'''
    
    __tablename__ = "favorite_users"

    id = sq.Column(sq.Integer, primary_key=True)
    id_user_id = sq.Column(sq.Integer, sq.ForeignKey("vk_user_info.id"), unique=False, nullable=False)
    favorite_user_id = sq.Column(sq.BigInteger, unique=True, nullable=True)
    first_name = sq.Column(sq.String, unique=False, nullable=False)
    last_name = sq.Column(sq.String, unique=False, nullable=False)
    sex = sq.Column(sq.String(length=7), unique=False, nullable=True)
    relation = sq.Column(sq.String, unique=False, nullable=True)
    age = sq.Column(sq.String, unique=False, nullable=True)
    city = sq.Column(sq.String, unique=False, nullable=True)
    univer = sq.Column(sq.String, unique=False, nullable=True)
    closed = sq.Column(sq.String, unique=False, nullable=False)
    has_photo = sq.Column(sq.String, unique=False, nullable=True)
    music = sq.Column(sq.String, unique=False, nullable=True)
    
    vk_user_info = relationship(VKuserInfo, backref="favorite_users")

    def __str__(self):
        return (f"Вот информация, выбранного Вами пользователя:\n"
            f"ID пользователя: {self.favorite_user_id}\n"
            f"Имя и фамилия: {self.first_name} {self.last_name}\n"
            f"Семейное положение: {self.relation}"
            f"Пол: {self.sex}\n"
            f"Возраст: {self.age}\n"
            f"Город: {self.city}\n"
            f"Университет: {self.univer}\n"
            f"Открытый или закрытый профиль: {self.closed}\n"
            f"Есть ли фотографии: {self.has_photo}\n"
            f"Музыкальные предпочтения: {self.music}\n")
    
class BlackList(Base):
    
    ''' Функция для создания таблицы в БД для сохранения
        пользователем непонравившихся ему людей в черном списке 
        для игнорирования в дальнейшем поиске'''
    
    __tablename__ = "black_list"

    id = sq.Column(sq.Integer, primary_key=True)
    id_user_id = sq.Column(sq.Integer, sq.ForeignKey("vk_user_info.id"), unique=False, nullable=False)
    black_user_id = sq.Column(sq.BigInteger, unique=True, nullable=True)
    first_name = sq.Column(sq.String, unique=False, nullable=False)
    last_name = sq.Column(sq.String, unique=False, nullable=False)
    relation = sq.Column(sq.String, unique=False, nullable=True)
    sex = sq.Column(sq.String(length=7), unique=False, nullable=True)
    age = sq.Column(sq.String, unique=False, nullable=True)
    city = sq.Column(sq.String, unique=False, nullable=True)
    univer = sq.Column(sq.String, unique=False, nullable=True)
    closed = sq.Column(sq.String, unique=False, nullable=False)
    has_photo = sq.Column(sq.String, unique=False, nullable=True)
    music = sq.Column(sq.String, unique=False, nullable=True)
    
    vk_user_info = relationship(VKuserInfo, backref="black_list")

    def __str__(self):
        return (f"Вот информация, выбранного Вами пользователя из черного списка:\n"
            f"ID пользователя: {self.black_user_id}\n"
            f"Имя и фамилия: {self.first_name} {self.last_name}\n"
            f"Семейное положение: {self.relation}"
            f"Пол: {self.sex}\n"
            f"Возраст: {self.age}\n"
            f"Город: {self.city}\n"
            f"Университет: {self.univer}\n"
            f"Открытый или закрытый профиль: {self.closed}\n"
            f"Есть ли фотографии: {self.has_photo}\n"
            f"Музыкальные предпочтения: {self.music}")


def create_tables(engine):
    Base.metadata.create_all(engine)

