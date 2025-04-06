import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self) -> None:
        """Инициализация подключения к БД с проверкой"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST')
            )
            self.cur = self.conn.cursor(cursor_factory=DictCursor)

            # Проверка подключения
            self.cur.execute("SELECT 1")
            self.conn.commit()

            logger.info("✅ Успешное подключение к PostgreSQL (версия: %s)",
                        self.conn.server_version)

            self._create_tables()
            self._create_cache_table()
            self._create_likes_table()  # Добавляем таблицу для лайков

        except Exception as e:
            logger.critical("❌ Ошибка подключения к PostgreSQL: %s", e)
            raise RuntimeError(f"Database connection failed: {e}")

    def _create_likes_table(self) -> None:
        """Создает таблицу для хранения информации о лайках"""
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS Likes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES Users(vk_id),
                liked_user_id INTEGER NOT NULL,
                photo_id INTEGER NOT NULL,
                liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, photo_id)  -- Один лайк на фото от пользователя
            );
        """)
        self.conn.commit()

    def add_like(self, user_id: int, liked_user_id: int, photo_id: int) -> bool:
        """
        Добавляет информацию о лайке в базу данных

        Args:
            user_id: ID пользователя, который поставил лайк
            liked_user_id: ID пользователя, которому поставили лайк
            photo_id: ID фотографии, которой поставили лайк

        Returns:
            True если лайк успешно добавлен, False если уже существует
        """
        try:
            # Проверяем существование пользователей
            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (user_id,))
            if not self.cur.fetchone():
                logger.error(f"User {user_id} not found")
                return False

            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (liked_user_id,))
            if not self.cur.fetchone():
                logger.error(f"Liked user {liked_user_id} not found")
                return False

            # Добавляем лайк
            self.cur.execute("""
                INSERT INTO Likes (user_id, liked_user_id, photo_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, photo_id) DO NOTHING
                RETURNING 1;
            """, (user_id, liked_user_id, photo_id))

            self.conn.commit()
            return bool(self.cur.fetchone())

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding like: {e}")
            return False

    def get_user_likes(self, user_id: int) -> List[Dict]:
        """
        Получает список лайков пользователя

        Args:
            user_id: ID пользователя VK

        Returns:
            Список словарей с информацией о лайках
        """
        try:
            self.cur.execute("""
                SELECT liked_user_id, photo_id, liked_at 
                FROM Likes 
                WHERE user_id = %s
                ORDER BY liked_at DESC;
            """, (user_id,))

            return [
                {
                    'liked_user_id': row['liked_user_id'],
                    'photo_id': row['photo_id'],
                    'liked_at': row['liked_at']
                }
                for row in self.cur.fetchall()
            ]
        except Exception as e:
            logger.error(f"Error getting user likes: {e}")
            return []

    def has_liked_photo(self, user_id: int, photo_id: int) -> bool:
        """
        Проверяет, лайкал ли пользователь данную фотографию

        Args:
            user_id: ID пользователя VK
            photo_id: ID фотографии

        Returns:
            True если лайк уже был поставлен, иначе False
        """
        try:
            self.cur.execute("""
                SELECT 1 FROM Likes 
                WHERE user_id = %s AND photo_id = %s;
            """, (user_id, photo_id))

            return bool(self.cur.fetchone())
        except Exception as e:
            logger.error(f"Error checking like: {e}")
            return False

    def check_connection(self) -> bool:
        """Проверяет активность подключения к БД"""
        try:
            self.cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("Соединение с PostgreSQL разорвано: %s", e)
            return False

    def _create_tables(self) -> None:
        """Создает необходимые таблицы в БД если они не существуют"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS Users (
                id SERIAL PRIMARY KEY,
                vk_id INTEGER UNIQUE NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                age INTEGER,
                sex VARCHAR(10),
                city VARCHAR(50)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Favorites (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES Users(vk_id),
                favorite_vk_id INTEGER NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, favorite_vk_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Blacklist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES Users(vk_id),
            blocked_vk_id INTEGER NOT NULL,
            blocked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, blocked_vk_id)
        );
            """
        ]

        for table in tables:
            self.cur.execute(table)
        self.conn.commit()

    def _create_cache_table(self) -> None:
        """Создает таблицу для кэширования результатов поиска"""
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                search_params JSONB NOT NULL,
                results JSONB NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, search_params)
            );
        """)
        self.conn.commit()

    def get_cached_results(self, user_id: int, search_params: Dict) -> Optional[List[Dict]]:
        """
        Получает закэшированные результаты поиска
        Args:
            user_id: ID пользователя VK
            search_params: Параметры поиска
        Returns:
            Список пользователей или None если кэш устарел
        """
        try:
            self.cur.execute("""
                SELECT results::text FROM search_cache
                WHERE user_id = %s AND search_params = %s AND expires_at > NOW()
                LIMIT 1;
            """, (user_id, json.dumps(search_params)))
            result = self.cur.fetchone()
            if result:
                return json.loads(result[0])
            return None
        except Exception as e:
            logger.error(f"Error getting cached results: {e}")
            return None

    def cache_results(self, user_id: int, search_params: Dict, results: List[Dict], ttl_hours: int = 24) -> None:
        """
        Сохраняет результаты поиска в кэш
        Args:
            user_id: ID пользователя VK
            search_params: Параметры поиска
            results: Найденные пользователи
            ttl_hours: Время жизни кэша в часах
        """
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        try:
            # Сериализуем данные в JSON строку
            serialized_results = json.dumps(results, ensure_ascii=False)
            self.cur.execute("""
                INSERT INTO search_cache (user_id, search_params, results, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, search_params) 
                DO UPDATE SET results = EXCLUDED.results, expires_at = EXCLUDED.expires_at;
            """, (user_id, json.dumps(search_params), serialized_results, expires_at))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error caching results: {e}")

    def add_user(self, vk_id: int, first_name: str, last_name: str,
                 age: Optional[int] = None, sex: Optional[str] = None,
                 city: Optional[str] = None) -> bool:
        """
        Добавляет пользователя в БД или обновляет существующего

        Returns:
            True если пользователь добавлен/обновлен, False при ошибке
        """
        try:
            self.cur.execute("""
                INSERT INTO Users (vk_id, first_name, last_name, age, sex, city)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (vk_id) 
                DO UPDATE SET 
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    age = COALESCE(EXCLUDED.age, Users.age),
                    sex = COALESCE(EXCLUDED.sex, Users.sex),
                    city = COALESCE(EXCLUDED.city, Users.city)
                RETURNING 1;
            """, (vk_id, first_name, last_name, age, sex, city))
            self.conn.commit()
            return bool(self.cur.fetchone())
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding user {vk_id}: {e}")
            return False

    def user_exists(self, vk_id: int) -> bool:
        """Проверяет существует ли пользователь в БД"""
        try:
            self.cur.execute("""
                SELECT 1 FROM Users WHERE vk_id = %s
            """, (vk_id,))
            return bool(self.cur.fetchone())
        except Exception as e:
            logger.error(f"Error checking user {vk_id}: {e}")
            return False

    def add_favorite(self, user_id: int, favorite_vk_id: int) -> bool:
        """
        Добавляет пользователя в избранное

        Args:
            user_id: ID пользователя VK
            favorite_vk_id: ID добавляемого пользователя

        Returns:
            True если добавление успешно, False если пользователь уже в избранном
            или произошла ошибка
        """
        try:
            # Проверяем существование пользователей
            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (user_id,))
            if not self.cur.fetchone():
                logger.error(f"User {user_id} not found in database")
                return False

            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (favorite_vk_id,))
            if not self.cur.fetchone():
                logger.error(f"Favorite user {favorite_vk_id} not found in database")
                return False

            # Проверяем, есть ли уже в избранном
            self.cur.execute("""
                SELECT 1 FROM Favorites 
                WHERE user_id = %s AND favorite_vk_id = %s
            """, (user_id, favorite_vk_id))

            if self.cur.fetchone():
                logger.info(f"User {favorite_vk_id} already in favorites for user {user_id}")
                return False

            # Добавляем в избранное
            self.cur.execute("""
                INSERT INTO Favorites (user_id, favorite_vk_id)
                VALUES (%s, %s)
            """, (user_id, favorite_vk_id))

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding favorite: {e}")
            return False

    def add_to_blacklist(self, user_id: int, blocked_vk_id: int) -> bool:
        """
        Добавляет пользователя в черный список

        Args:
            user_id: ID пользователя VK
            blocked_vk_id: ID блокируемого пользователя

        Returns:
            True если добавление успешно, False если пользователь уже в черном списке
        """
        try:
            # Проверяем существование пользователей
            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (user_id,))
            if not self.cur.fetchone():
                logger.error(f"User {user_id} not found")
                return False

            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (blocked_vk_id,))
            if not self.cur.fetchone():
                logger.error(f"Blocked user {blocked_vk_id} not found")
                return False

            # Проверяем, не добавлен ли уже пользователь в ЧС
            if self.check_blacklist(user_id, blocked_vk_id):
                return False

            # Добавляем в черный список
            self.cur.execute("""
                    INSERT INTO Blacklist (user_id, blocked_vk_id)
                    VALUES (%s, %s)
                """, (user_id, blocked_vk_id))
            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error adding to blacklist: {e}")
            return False

    def get_favorites(self, user_id: int) -> List[int]:
        """
        Получает список избранных пользователей

        Args:
            user_id: ID пользователя VK

        Returns:
            Список ID избранных пользователей
        """
        try:
            self.cur.execute("""
                    SELECT favorite_vk_id FROM Favorites
                    WHERE user_id = %s
                    ORDER BY added_date DESC
                """, (user_id,))
            return [row['favorite_vk_id'] for row in self.cur.fetchall()]
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return []

    def check_blacklist(self, user_id: int, target_vk_id: int) -> bool:
        """Проверяет наличие пользователя в ЧС"""
        try:
            # Автоматически создаем записи если пользователей нет
            if not self.user_exists(user_id):
                self.add_user(user_id, "", "", None, None, None)

            if not self.user_exists(target_vk_id):
                self.add_user(target_vk_id, "", "", None, None, None)

            self.cur.execute("""
                SELECT 1 FROM Blacklist
                WHERE user_id = %s AND blocked_vk_id = %s
            """, (user_id, target_vk_id))
            return bool(self.cur.fetchone())
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

    def close(self) -> None:
        """Закрывает соединение с БД"""
        self.cur.close()
        self.conn.close()
