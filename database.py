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
        """Инициализация подключения к БД и создание таблиц"""
        self.conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST')
        )
        self.cur = self.conn.cursor(cursor_factory=DictCursor)
        self._create_tables()
        self._create_cache_table()

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
                 age: int, sex: str, city: str) -> None:
        """
        Добавляет пользователя в БД

        Args:
            vk_id: ID пользователя VK
            first_name: Имя
            last_name: Фамилия
            age: Возраст
            sex: Пол
            city: Город
        """
        self.cur.execute("""
            INSERT INTO Users (vk_id, first_name, last_name, age, sex, city)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (vk_id) DO NOTHING;
        """, (vk_id, first_name, last_name, age, sex, city))
        self.conn.commit()

    def add_favorite(self, user_id: int, favorite_vk_id: int) -> bool:
        """
        Добавляет пользователя в избранное

        Args:
            user_id: ID пользователя VK
            favorite_vk_id: ID добавляемого пользователя

        Returns:
            True если добавление успешно, False если пользователь уже в избранном
        """
        try:
            # Проверяем существование пользователя, который добавляет
            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (user_id,))
            if not self.cur.fetchone():
                logger.error(f"User {user_id} not found in database")
                return False

            # Проверяем существование пользователя, которого добавляют
            self.cur.execute("SELECT 1 FROM Users WHERE vk_id = %s", (favorite_vk_id,))
            if not self.cur.fetchone():
                logger.error(f"Favorite user {favorite_vk_id} not found in database")
                return False

            # Пробуем добавить в избранное
            self.cur.execute("""
                    INSERT INTO Favorites (user_id, favorite_vk_id)
                    VALUES (%s, %s)
                """, (user_id, favorite_vk_id))
            self.conn.commit()
            return True

        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.warning(f"User {favorite_vk_id} already in favorites for user {user_id}")
            return False
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
        """
        Проверяет находится ли пользователь в черном списке

        Args:
            user_id: ID пользователя VK
            target_vk_id: ID проверяемого пользователя

        Returns:
            True если пользователь в черном списке, иначе False
        """
        self.cur.execute("""
            SELECT 1 FROM Blacklist
            WHERE user_id = %s AND blocked_vk_id = %s;
        """, (user_id, target_vk_id))
        return self.cur.fetchone() is not None

    def close(self) -> None:
        """Закрывает соединение с БД"""
        self.cur.close()
        self.conn.close()
