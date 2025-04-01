import psycopg2
import sqlalchemy
import sqlalchemy as sq
from sqlalchemy import BigInteger
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
from environs import env

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


db_name = env('DB_NAME')
db_pass = env('DB_PASS')
db_user = env('DB_USER')
db_user = env('DB_USER')
vk_token = env('VK_API_TOKEN')


Base = declarative_base()


DSN = f'postgresql://{db_user}:{db_pass}@localhost:5432/{db_name}'
engine = sqlalchemy.create_engine(DSN)

create_tables(engine)

Session = sessionmaker(bind=engine)

session = Session()

vk_user = VK(vk_token)


conn = psycopg2.connect(database=data_base, user=login, password=postgres_pass)
cur = conn.cursor()

# Функция для добавления пользователя в БД
def add_user(user_id):

    ''' Функция для добавления пользователя в БД'''
    
    f_name = vk_user.get_first_name(user_id)
    l_name = vk_user.get_last_name(user_id)
    get_sex = vk_user.get_sex(user_id)
    get_relation = vk_user.get_relation(user_id)
    get_age = vk_user.get_age(user_id)
    get_city = vk_user.get_city(user_id)
    get_univer = vk_user.get_univer(user_id)
    is_closed = vk_user.get_is_closed(user_id)
    get_has_photo = vk_user.get_has_photo(user_id)
    get_music = vk_user.get_music(user_id)
    
    try:
        cur.execute(
            '''INSERT INTO vk_user_info (user_id, first_name, last_name,
                                         sex, relation, age, city,
                                         univer, closed, has_photo, music)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING''', 
            (user_id, f_name, l_name, get_sex, get_relation,
             get_age, get_city, get_univer, is_closed,
             get_has_photo, get_music,))
        conn.commit()
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()


# Функция для сообщения пользователю его инфы
def get_my_info(user_id):

    '''Функция для сообщения пользователю его инфы'''
    get_my_info = session.query(VKuserInfo).filter(VKuserInfo.user_id==user_id).first()
    msg = get_my_info  # Сообщение для отправки пользователю 
    print(get_my_info)

    
def rel():

    ''' Функция для использования в функциях add_my_prefer и change_my_prefer
        для ввода и изменения предпочтений в семейном положении, у полльзователя
        для поиска ему партнеров. Запрос производится через
        сообщения пользователю. Получение имени и фамилии должно
        происходить через запрос бота и ввод сообщения пользователя'''
    
    rel = int(input('''Введите цифру предпочтительного семейного положения партнера из следующих вариантов:
                0: "Статус отношений не задан",
                1: "Не женат/Не замужем",
                2: "Есть друг/подруга",
                3: "Помолвлен(-а)",
                4: "Женат/Замужем",
                5: "Всё сложно",
                6: "В активном поиске",
                7: "Влюблён(-а)",
                8: "В гражданском браке": '''))
    relation = ''
    if rel == 0:
        relation = "Статус отношений не задан"
    elif rel == 1:
        relation = "Не женат/Не замужем"
    elif rel == 2:
        relation = "Есть друг/подруга"
    elif rel == 3:
        relation = "Помолвлен(-а)"
    elif rel == 4:
        relation = "Женат/Замужем"
    elif rel == 5:
        relation = "Всё сложно"
    elif rel == 6:
        relation = "В активном поиске"
    elif rel == 7:
        relation = "Влюблён(-а)"
    elif rel == 8:
        relation = "В гражданском браке"
    return relation


def add_my_prefer(user_id):

    ''' Функция для запроса критериев, предпочтений, у полльзователя
        для поиска ему партнеров. Запрос производится через
        сообщения пользователю. Получение имени и фамилии должно
        происходить через через запрос бота и ввод сообщения пользователя'''
    
    sex = input('Введите предпочтительный пол партнера (мужский/женский): ')
    relation = rel()
    age_ner = input('Введите нижний предел возраста предполагаемого парнера: ')
    age_up = input('Введите верхний предел возраста предполагаемого парнера: ')
    city = input('Введите предпочтительный город парнера: ')
    
    try:
        cur.execute(
            '''INSERT INTO my_preferences (user_id, sex, relation,
                                         age_ner, age_up, city)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING''', 
            (user_id, sex, relation, age_ner, age_up, city,))
        conn.commit()
        msg = "Ваши предпочтения сохраненый" # Сообщение для отправки пользователю 
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()


# Функция для сообщения пользователю его предпочтений
def get_my_prefer(user_id):

    ''' Функция для сообщения пользователю его предпочтений'''
    
    get_my_prefer = session.query(MyPreferences).filter(MyPreferences.user_id==user_id).first()
    msg = get_my_info  # Сообщение для отправки пользователю 
    print(get_my_info)


# Функция изменения предпочтений пользователя
def change_my_prefer(user_id):
    
    ''' Функция для изменения критериев, предпочтений, полльзователя.
        Получение имени и фамилии должно происходить через
        через запрос бота и ввод сообщения пользователя'''
    
    sex = input('Введите предпочтительный пол партнера (мужский/женский): ')
    relation = rel()
    age_ner = input('Введите нижний предел возраста предполагаемого парнера: ')
    age_up = input('Введите верхний предел возраста предполагаемого парнера: ')
    city = input('Введите предпочтительный город парнера: ')
    try:
        cur.execute(
            '''UPDATE my_preferences
               SET sex = %s, relation = %s,
               age_ner = %s, age_up = %s, city = %s
               WHERE user_id = %s''', 
            (sex, relation, age_ner, age_up, city, user_id,))
        conn.commit()
        msg = "Ваши предпочтения изменены" # Сообщение для отправки пользователю 
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()


# Функция для добавления человека в избранное
def add_to_favorite(user_id, favorite_user_id):

    ''' Функция для добавления человека в избранное'''
    
    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    f_name = vk_user.get_first_name(favorite_user_id)
    l_name = vk_user.get_last_name(favorite_user_id)
    get_sex = vk_user.get_sex(favorite_user_id)
    get_relation = vk_user.get_relation(favorite_user_id)
    get_age = vk_user.get_age(favorite_user_id)
    get_city = vk_user.get_city(favorite_user_id)
    get_univer = vk_user.get_univer(favorite_user_id)
    is_closed = vk_user.get_is_closed(favorite_user_id)
    get_has_photo = vk_user.get_has_photo(favorite_user_id)
    get_music = vk_user.get_music(favorite_user_id)
    
    try:
        cur.execute(
            '''INSERT INTO favorite_users (id_user_id, favorite_user_id,
               first_name, last_name, sex, relation, age, city,
               univer, closed, has_photo, music)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (favorite_user_id) DO NOTHING''', 
            (my_user_id, favorite_user_id, f_name, l_name, get_sex, get_relation,
             get_age, get_city, get_univer, is_closed,
             get_has_photo, get_music,))
        conn.commit()
        
        # Посылается сообщение пользователю
        msg = f"Пользователь {f_name} {l_name} добавлен в избранные."
        print(msg)
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()


# Функция для получения информации о человеке, добавленном в избранное
# по имени и фамилии
def get_my_favorite_info(user_id):

    ''' Функция для получения информации о человеке, добавленном в избранное,
        по имени и фамилии. Получение имени и фамилии должно происходить через
        через запрос бота и ввод сообщения пользователя'''
    
    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    f_name = str(input('Введите имя: '))
    l_name = str(input('Введите фамилию: '))
    get_my_favorite_info = session.query(FavoriteUsers).filter(FavoriteUsers.id_user_id==my_user_id,
                                                               FavoriteUsers.first_name==f_name,
                                                               FavoriteUsers.last_name==l_name).first()
    # Проверяем наличение этого человека в таблице
    if get_my_favorite_info:
        # Выводим информацию сообщением пользователю
        msg = get_my_favorite_info
        print(msg)
    else:
        # Выводим информацию сообщением пользователю
        msg = "Такого пользователя нет в избранных"
        print(msg)


# Функция для получения списка всех людей, добавленных в избранное, выведенных
# по имени и фамилии
def get_list_favorite_info(user_id):

    ''' Функция для получения списка всех людей, добавленных в избранное, выведенных
        по имени и фамилии'''
    
    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    first_name = session.query(FavoriteUsers.first_name, FavoriteUsers.last_name).filter(
                               FavoriteUsers.id_user_id==my_user_id).all()
    result = []
    for names in first_name:
        name = f'{names[0]} {names[1]}'
        result.append(name)
    # Выводим информацию сообщением пользователю
    msg = result
    print(result)


def add_to_black_list(user_id, black_user_id):

    ''' Функция для добавления человека в черный список
        и его удаление из избранных, если он там сохранен'''
    
    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    f_name = vk_user.get_first_name(black_user_id)
    l_name = vk_user.get_last_name(black_user_id)
    get_sex = vk_user.get_sex(black_user_id)
    get_relation = vk_user.get_relation(black_user_id)
    get_age = vk_user.get_age(black_user_id)
    get_city = vk_user.get_city(black_user_id)
    get_univer = vk_user.get_univer(black_user_id)
    is_closed = vk_user.get_is_closed(black_user_id)
    get_has_photo = vk_user.get_has_photo(black_user_id)
    get_music = vk_user.get_music(black_user_id)
    
    try:
        cur.execute(
            '''INSERT INTO black_list (id_user_id, black_user_id,
               first_name, last_name, sex, relation, age, city,
               univer, closed, has_photo, music)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (black_user_id) DO NOTHING''', 
            (my_user_id, black_user_id, f_name, l_name, get_sex, get_relation,
             get_age, get_city, get_univer, is_closed,
             get_has_photo, get_music,))
        conn.commit()
        
        # Посылается сообщение пользователю
        msg = f"Пользователь {f_name} {l_name} добавлен в черный список."
        print(msg)
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()

    try:
       get_my_favorite_info = session.query(FavoriteUsers).filter(
            FavoriteUsers.id_user_id == my_user_id,
            FavoriteUsers.favorite_user_id == black_user_id).first()
       if get_my_favorite_info:
           session.query(FavoriteUsers).filter(
                FavoriteUsers.id_user_id == my_user_id,
                FavoriteUsers.favorite_user_id == black_user_id).delete()
           session.commit()
           # Посылается сообщение пользователю
           msg = f"Пользователь {f_name} {l_name} удален из избранного."
           print(f"Пользователь {f_name} {l_name} удален из избранного.")
    except Exception as e:
        print(f"Ошибка при удалении из избранного: {e}")
        session.rollback()


def get_from_black_list(user_id):

    ''' Функция для просмотра информации человека из черного списка
        по имени и фамилии. Получение имени и фамилии должно происходить через
        через запрос бота и ввод сообщения пользователя'''

    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    f_name = str(input('Введите имя человека из черного списка, информацио о котором хотите узнать: '))
    l_name = str(input('''Введите фамилию человека из черного списка,
                        информацио о котором хотите узнать: '''))
    get_from_black_list = session.query(BlackList).filter(
            BlackList.id_user_id == my_user_id,
            BlackList.first_name == f_name,
            BlackList.last_name == l_name).first()

    # Проверяем наличение этого человека в таблице
    if get_from_black_list:
        # Выводим информацию сообщением пользователю
        msg = get_from_black_list
        print(msg)
    else:
        # Выводим информацию сообщением пользователю
        msg = "Такого пользователя нет в избранных"
        print(msg)


# Функция для получения списка всех людей, добавленных в черный список, выведенных
# по имени и фамилии
def get_list_black_list(user_id):

    ''' Функция для получения списка всех людей, добавленных в черный список,
        выведенных по имени и фамилии'''
    
    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    first_name = session.query(BlackList.first_name, BlackList.last_name).filter(
                               BlackList.id_user_id==my_user_id).all()
    result = []
    for names in first_name:
        name = f'{names[0]} {names[1]}'
        result.append(name)
    # Выводим информацию сообщением пользователю
    msg = result
    print(result)


def del_from_black_list(user_id):

    ''' Функция для удаления человека из черного списка'''

    my_user_id = session.query(VKuserInfo.id).filter(VKuserInfo.user_id==user_id).scalar()
    f_name = str(input('Введите имя, кого хотите удалить из черного списка: '))
    l_name = str(input('Введите фамилию, кого хотите удалить из черного списка: '))

    try:
        interval = session.query(BlackList).filter(
            BlackList.id_user_id == my_user_id,
            BlackList.first_name == f_name,
            BlackList.last_name == l_name).first()
        if interval:
            cur.execute(
            '''DELETE FROM black_list
               WHERE id_user_id = %s and first_name = %s and last_name = %s''', 
             (my_user_id, f_name, l_name,))
            conn.commit()
            # Посылается сообщение пользователю
            msg = f"Пользователь {f_name} {l_name} удален(а) их черного списока."
            print(f"Пользователь {f_name} {l_name} удален(а) их черного списока.")
        else:
            # Посылается сообщение пользователю
            msg = f"Пользователя {f_name} {l_name} нет в черном списке."
            print(f"Пользователя {f_name} {l_name} нет в черном списке.")
    except Exception as e:
        print(f"Ошибка при удалении из черного списка: {e}")
        session.rollback()


session.close()


if __name__ == '__main__':
    add_user(user_id)
    


