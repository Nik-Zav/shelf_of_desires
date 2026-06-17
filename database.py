import psycopg
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def get_connection():
    """Создаёт подключение к PostgreSQL с использованием psycopg (v3)"""
    # psycopg v3 использует функцию connect напрямую
    return psycopg.connect(DATABASE_URL)

def init_database():
    """Инициализирует таблицы в PostgreSQL"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_items (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            added_by BIGINT NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Личная таблица пользователя А
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_a_items (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            added_by BIGINT NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Личная таблица пользователя Б
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_b_items (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            added_by BIGINT NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных PostgreSQL инициализирована")

def add_to_shared(text, user_id, user_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shared_items (text, added_by, added_by_name)
        VALUES (%s, %s, %s)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_shared():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM shared_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def add_to_personal_a(text, user_id, user_name):
    """Добавить в личную базу А"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO personal_a_items (text, added_by, added_by_name)
        VALUES (%s, %s, %s)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_personal_a():
    """Получить случайную запись из личной базы А"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM personal_a_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def add_to_personal_b(text, user_id, user_name):
    """Добавить в личную базу Б"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO personal_b_items (text, added_by, added_by_name)
        VALUES (%s, %s, %s)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_personal_b():
    """Получить случайную запись из личной базы Б"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM personal_b_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def get_stats():
    """Получить статистику"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM shared_items')
    shared_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM personal_a_items')
    personal_a_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM personal_b_items')
    personal_b_count = cursor.fetchone()[0]
    
    conn.close()
    return shared_count, personal_a_count, personal_b_count