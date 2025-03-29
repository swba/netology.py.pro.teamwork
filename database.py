import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST')
        )
        self.cur = self.conn.cursor(cursor_factory=DictCursor)
        self.create_tables()

    def create_tables(self):
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id SERIAL PRIMARY KEY,
                vk_id INTEGER UNIQUE NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                age INTEGER,
                sex VARCHAR(10),
                city VARCHAR(50)
            );
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS Favorites (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES Users(vk_id),
                favorite_vk_id INTEGER NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS Blacklist (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES Users(vk_id),
                blocked_vk_id INTEGER NOT NULL,
                blocked_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        self.conn.commit()

    def add_user(self, vk_id, first_name, last_name, age, sex, city):
        self.cur.execute('''
            INSERT INTO Users (vk_id, first_name, last_name, age, sex, city)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (vk_id) DO NOTHING;
        ''', (vk_id, first_name, last_name, age, sex, city))
        self.conn.commit()

    def add_favorite(self, user_id, favorite_vk_id):
        self.cur.execute('''
            INSERT INTO Favorites (user_id, favorite_vk_id)
            VALUES (%s, %s);
        ''', (user_id, favorite_vk_id))
        self.conn.commit()

    def add_to_blacklist(self, user_id, blocked_vk_id):
        self.cur.execute('''
            INSERT INTO Blacklist (user_id, blocked_vk_id)
            VALUES (%s, %s);
        ''', (user_id, blocked_vk_id))
        self.conn.commit()

    def get_favorites(self, user_id):
        self.cur.execute('''
            SELECT favorite_vk_id FROM Favorites
            WHERE user_id = %s;
        ''', (user_id,))
        return [row['favorite_vk_id'] for row in self.cur.fetchall()]

    def check_blacklist(self, user_id, target_vk_id):
        self.cur.execute('''
            SELECT 1 FROM Blacklist
            WHERE user_id = %s AND blocked_vk_id = %s;
        ''', (user_id, target_vk_id))
        return self.cur.fetchone() is not None

    def close(self):
        self.cur.close()
        self.conn.close()
