import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Строка подключения к PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не найден в .env файле!")

# ID пользователей (можно тоже хранить в .env)
USER_A_ID = int(os.getenv('USER_A_ID', 1895554663))
USER_B_ID = int(os.getenv('USER_B_ID', 814729344))