import telebot
import sqlite3
import random
import os
import time
import logging
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# ========== НАСТРОЙКИ ==========
TOKEN = "8846772231:AAF0As5ZvYgnThdWFQrJEwmk1xKhYsjI-vg"

# Telegram ID двух пользователей (узнать у @userinfobot)
USER_A_ID = 1895554663  # ID первого пользователя
USER_B_ID = 814729344  # ID второго пользователя

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard(user_id):
    """Главная клавиатура (разная для разных пользователей)"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Общие кнопки для всех
    keyboard.row("📝 Добавить идею свидания", "🎲 Хочу свидание")
    keyboard.row("🔐 Так можно меня порадовать", "🔓 Так могу порадовать я")
    keyboard.row("📊 Статистика", "❓ Помощь")
    
    return keyboard

def get_add_keyboard():
    """Клавиатура для выбора куда добавлять"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.row("📝 База свиданий")
    keyboard.row("🔐 База моих радостей")
    keyboard.row("◀️ Назад")
    return keyboard

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.row("❌ Отмена")
    return keyboard

def remove_keyboard(message):
    """Убирает клавиатуру"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("◀️ Вернуться в меню")
    return markup

# ========== СОСТОЯНИЯ ДЛЯ ДИАЛОГОВ ==========
user_states = {}  # Словарь для хранения состояния каждого пользователя

# Состояния:
WAITING_FOR_SHARED_TEXT = 1      # Ждём текст для общей базы
WAITING_FOR_PERSONAL_TEXT = 2     # Ждём текст для личной базы

# ========== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==========
DB_PATH = "shared_database.db"

def init_database():
    """Создаёт все таблицы, если их нет"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shared_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            added_by INTEGER NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_a_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            added_by INTEGER NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_b_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            added_by INTEGER NOT NULL,
            added_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ==========

def add_to_shared(text, user_id, user_name):
    """Добавить в общую базу"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shared_items (text, added_by, added_by_name)
        VALUES (?, ?, ?)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_shared():
    """Получить случайную запись из общей базы"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM shared_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def add_to_personal_a(text, user_id, user_name):
    """Добавить в личную базу А"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO personal_a_items (text, added_by, added_by_name)
        VALUES (?, ?, ?)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_personal_a():
    """Получить случайную запись из личной базы А"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM personal_a_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def add_to_personal_b(text, user_id, user_name):
    """Добавить в личную базу Б"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO personal_b_items (text, added_by, added_by_name)
        VALUES (?, ?, ?)
    ''', (text, user_id, user_name))
    conn.commit()
    conn.close()

def get_random_from_personal_b():
    """Получить случайную запись из личной базы Б"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT text, added_by_name FROM personal_b_items ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result

def get_stats():
    """Получить статистику"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM shared_items')
    shared_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM personal_a_items')
    personal_a_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM personal_b_items')
    personal_b_count = cursor.fetchone()[0]
    
    conn.close()
    return shared_count, personal_a_count, personal_b_count

# ========== ПРОВЕРКА ДОСТУПА ==========

def is_user_a(user_id):
    return user_id == USER_A_ID

def is_user_b(user_id):
    return user_id == USER_B_ID

def is_authorized(user_id):
    return user_id in [USER_A_ID, USER_B_ID]

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Доступ запрещён. Этот бот только для двоих.")
        return
    
    user_name = message.from_user.first_name
    role = "Буб" if is_user_a(message.from_user.id) else "Бесёнок"
    
    # Очищаем состояние пользователя
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    welcome_text = f"""
🤖 *Привет, {user_name}! ({role})*

Я бот для совместного хранения записей. 
Используй кнопки ниже для управления.

📌 *Что можно делать:*
• Добавлять записи в общую базу свиданий
• Добавлять записи в свою личную базу радостей
• Получать случайные записи
• Смотреть статистику

👇 *Просто нажимай на кнопки!*
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda message: message.text == "◀️ Назад" or message.text == "◀️ Вернуться в меню")
def back_to_main(message):
    if not is_authorized(message.from_user.id):
        return
    
    # Очищаем состояние
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    bot.send_message(
        message.chat.id, 
        "🔙 Возврат в главное меню",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda message: message.text == "❌ Отмена")
def cancel_action(message):
    if not is_authorized(message.from_user.id):
        return
    
    # Очищаем состояние
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    bot.send_message(
        message.chat.id, 
        "❌ Действие отменено",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda message: message.text == "📝 Добавить идею свидания")
def add_shared_prompt(message):
    if not is_authorized(message.from_user.id):
        return
    
    # Устанавливаем состояние ожидания текста для общей базы
    user_states[message.from_user.id] = WAITING_FOR_SHARED_TEXT
    
    bot.send_message(
        message.chat.id,
        "📝 *Введи текст для добавления в общую базу:*\n\n(Напиши сообщение или отправь /cancel для отмены)",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🔐 Добавить радость для меня")
def add_personal_prompt(message):
    if not is_authorized(message.from_user.id):
        return
    
    # Устанавливаем состояние ожидания текста для личной базы
    user_states[message.from_user.id] = WAITING_FOR_PERSONAL_TEXT
    
    bot.send_message(
        message.chat.id,
        "🔐 *Введи текст для добавления в свою личную базу:*\n\n(Только ты сможешь добавлять сюда, другой пользователь сможет только читать)",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🎲 Идея свидания")
def get_shared(message):
    if not is_authorized(message.from_user.id):
        return
    
    result = get_random_from_shared()
    
    if result:
        text, added_by = result
        bot.send_message(
            message.chat.id,
            f"🎲 *Случайная запись из базы свиданий:*\n\n📝 {text}\n\n👤 Добавил: {added_by}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        bot.send_message(
            message.chat.id,
            "📭 Общая база пока пуста. Добавьте что-нибудь через кнопку \"📝 Добавить идею свидания\"",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

@bot.message_handler(func=lambda message: message.text == "🔓 Взять вариант порадовать")
def get_others_personal(message):
    if not is_authorized(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    if is_user_a(user_id):
        result = get_random_from_personal_b()
        owner = "Пользователя Б"
    else:
        result = get_random_from_personal_a()
        owner = "Пользователя А"
    
    if result:
        text, added_by = result
        bot.send_message(
            message.chat.id,
            f"🎲 *Случайная запись из личной базы {owner}:*\n\n📝 {text}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        bot.send_message(
            message.chat.id,
            f"📭 Личная база {owner} пока пуста.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def stats(message):
    if not is_authorized(message.from_user.id):
        return
    
    shared_count, personal_a_count, personal_b_count = get_stats()
    
    stats_text = f"""
📊 *Статистика базы данных*

📁 *База свидания:* {shared_count} записей
🔐 *База радостей Буба:* {personal_a_count} записей
🔐 *База радостей Бесёнка:* {personal_b_count} записей

━━━━━━━━━━━━━━━━
💡 *Всего записей:* {shared_count + personal_a_count + personal_b_count}
    """
    
    bot.send_message(
        message.chat.id, 
        stats_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def help_command(message):
    if not is_authorized(message.from_user.id):
        return
    
    help_text = """
❓ *Как пользоваться ботом*

📝 *Добавление записей:*
• Нажми "Добавить идею свидания" - все увидят
• Нажми "Добавить радость" - только ты добавляешь

🎲 *Получение записей:*
• "Взять идею свидания" - случайная из общего
• "Взять радость" - случайная из базы напарника

📊 *Статистика:* Показывает количество записей

💡 *Советы:*
• Записи нельзя удалить (пока)
• Нельзя посмотреть все записи
• Только случайный выбор!

⚡️ *Команды тоже работают:*
/add, /addmy, /get, /getother, /stats
    """
    
    bot.send_message(
        message.chat.id, 
        help_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# Обработка текстовых сообщений (для добавления записей)
@bot.message_handler(func=lambda message: message.chat.id in [USER_A_ID, USER_B_ID] and message.text and not message.text.startswith('/'))
def handle_text(message):
    user_id = message.from_user.id
    
    # Проверяем, есть ли пользователь в состоянии ожидания
    if user_id not in user_states:
        # Если нет состояния, просто игнорируем или показываем меню
        bot.send_message(
            message.chat.id,
            "🤔 Используй кнопки меню для работы с ботом",
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    state = user_states[user_id]
    text = message.text.strip()
    
    if state == WAITING_FOR_SHARED_TEXT:
        # Добавляем в общую базу
        add_to_shared(text, user_id, message.from_user.first_name)
        bot.send_message(
            message.chat.id,
            f"✅ Добавлено в *общую базу*!\n\n📝 {text}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )
        # Очищаем состояние
        del user_states[user_id]
        
    elif state == WAITING_FOR_PERSONAL_TEXT:
        # Добавляем в личную базу
        if is_user_a(user_id):
            add_to_personal_a(text, user_id, message.from_user.first_name)
        else:
            add_to_personal_b(text, user_id, message.from_user.first_name)
        
        bot.send_message(
            message.chat.id,
            f"✅ Добавлено в *твою личную базу*!\n\n📝 {text}\n\n(Другой пользователь сможет это получить через кнопку \"Взять радость\")",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )
        # Очищаем состояние
        del user_states[user_id]

@bot.message_handler(commands=['cancel'])
def cancel(message):
    if not is_authorized(message.from_user.id):
        return
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    bot.send_message(
        message.chat.id,
        "❌ Действие отменено",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# ========== ЗАПУСК С ОБРАБОТКОЙ ОШИБОК ==========
if __name__ == "__main__":
    init_database()
    
    logger.info("=" * 50)
    logger.info("Бот запущен и работает!")
    logger.info(f"Буб ID: {USER_A_ID}")
    logger.info(f"Бесёнок ID: {USER_B_ID}")
    logger.info("=" * 50)
    
    # Запускаем с автоматическим переподключением
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except KeyboardInterrupt:
            logger.info("Бот остановлен вручную")
            break
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            logger.info("Переподключение через 30 секунд...")
            time.sleep(30)