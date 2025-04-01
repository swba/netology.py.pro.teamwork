import pytest
from database import Database
from dotenv import load_dotenv
import os

load_dotenv()


@pytest.fixture
def db():
    db = Database()
    yield db
    # Очистка после тестов
    db.cur.execute("TRUNCATE TABLE Users, Favorites, Blacklist, search_cache RESTART IDENTITY;")
    db.conn.commit()
    db.close()


def test_add_and_get_user(db):
    db.add_user(123, "Test", "User", 25, "male", "Moscow")
    db.cur.execute("SELECT * FROM Users WHERE vk_id = 123;")
    user = db.cur.fetchone()
    assert user['first_name'] == "Test"
    assert user['age'] == 25


def test_add_favorite(db):
    # Сначала очистим таблицы для чистого теста
    db.cur.execute("TRUNCATE TABLE Users, Favorites RESTART IDENTITY CASCADE")
    db.conn.commit()

    # Добавляем тестовых пользователей
    db.add_user(1, "Test", "User", 25, "male", "Moscow")
    db.add_user(100, "Favorite", "User", 30, "female", "Moscow")

    # Проверяем что избранное пустое
    assert db.get_favorites(1) == []

    # Первое добавление - должно вернуть True
    result = db.add_favorite(1, 100)
    assert result is True, f"Expected True, got {result}"

    # Проверяем что пользователь добавился
    favorites = db.get_favorites(1)
    assert 100 in favorites, f"Expected [100], got {favorites}"

    # Проверяем содержимое таблицы напрямую
    db.cur.execute("SELECT * FROM Favorites")
    records = db.cur.fetchall()
    assert len(records) == 1
    assert records[0]['user_id'] == 1
    assert records[0]['favorite_vk_id'] == 100


def test_blacklist(db):
    # Очищаем таблицы
    db.cur.execute("TRUNCATE TABLE Users, Blacklist RESTART IDENTITY CASCADE")
    db.conn.commit()

    # Добавляем тестовых пользователей
    db.add_user(1, "Test", "User", 25, "male", "Moscow")
    db.add_user(200, "Blocked", "User", 30, "female", "Moscow")
    db.add_user(300, "Other", "User", 35, "female", "Moscow")

    # Проверяем что черный список пуст
    assert db.check_blacklist(1, 200) is False

    # Первое добавление - должно быть True
    assert db.add_to_blacklist(1, 200) is True

    # Проверяем что пользователь добавлен
    assert db.check_blacklist(1, 200) is True
    assert db.check_blacklist(1, 300) is False

    # Проверяем содержимое таблицы напрямую
    db.cur.execute("SELECT * FROM Blacklist WHERE user_id = 1 AND blocked_vk_id = 200")
    assert db.cur.fetchone() is not None

    # Повторное добавление - должно быть False
    assert db.add_to_blacklist(1, 200) is False

    # Проверяем что не добавился дубликат
    db.cur.execute("SELECT COUNT(*) FROM Blacklist WHERE user_id = 1 AND blocked_vk_id = 200")
    assert db.cur.fetchone()[0] == 1


def test_cache(db):
    # Очищаем кэш перед тестом
    db.cur.execute("TRUNCATE TABLE search_cache")
    db.conn.commit()

    test_data = [{"id": 1, "name": "Test"}]

    # Кэшируем данные
    db.cache_results(1, {"param": "value"}, test_data)

    # Получаем из кэша
    cached = db.get_cached_results(1, {"param": "value"})

    # Проверяем что данные совпадают
    assert cached == test_data

    # Проверяем что для других параметров кэш пустой
    assert db.get_cached_results(1, {"param": "other"}) is None

    # Проверяем что данные правильно хранятся в БД
    db.cur.execute("SELECT results::text FROM search_cache")
    raw_result = db.cur.fetchone()[0]
    assert '"name": "Test"' in raw_result
