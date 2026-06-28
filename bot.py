import telebot
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN, USER_A_ID, USER_B_ID
from database import (
    init_database,
    add_to_shared,
    get_random_from_shared,
    add_to_personal_a,
    get_random_from_personal_a,
    add_to_personal_b,
    get_random_from_personal_b,
    get_stats
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard(user_id):
    """Главная клавиатура"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.row("📝 Добавить идею", "🎲 Взять идею")
    keyboard.row("🔐 Добавить приятность", "🔓 Сделать приятность")
    keyboard.row("📊 Статистика", "❓ Помощь")
    return keyboard

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    keyboard.row("❌ Отмена")
    return keyboard

# ========== СОСТОЯНИЯ ==========
user_states = {}
WAITING_FOR_SHARED_TEXT = 1
WAITING_FOR_PERSONAL_TEXT = 2

# ========== ПРОВЕРКА ДОСТУПА ==========

def is_user_a(user_id):
    return user_id == USER_A_ID

def is_user_b(user_id):
    return user_id == USER_B_ID

def is_authorized(user_id):
    return user_id in [USER_A_ID, USER_B_ID]

# ========== HTTP СЕРВЕР ДЛЯ "БУДИЛЬНИКА" ==========

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP-запросов для health check"""
    
    def do_GET(self):
        """Обрабатываем GET-запросы"""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            logger.info("Health check ping received")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Подавляем лишние логи HTTP-сервера"""
        pass

def run_health_server(port=10000):
    """Запускает HTTP-сервер для health check"""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health check server error: {e}")

# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def start(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Доступ запрещён. Этот бот только для двоих.")
        return
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    user_name = message.from_user.first_name
    role = "Буб" if is_user_a(message.from_user.id) else "Бесёнок"
    
    welcome_text = f"""
🤖 *Привет, {user_name}! ({role})*

Я бот для совместного хранения записей. 
Используй кнопки ниже для управления.

📌 *Что можно делать:*
• Добавлять идеи
• Добавлять приятности
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
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]
    
    bot.send_message(
        message.chat.id, 
        "❌ Действие отменено",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@bot.message_handler(func=lambda message: message.text == "📝 Добавить идею")
def add_shared_prompt(message):
    if not is_authorized(message.from_user.id):
        return
    
    user_states[message.from_user.id] = WAITING_FOR_SHARED_TEXT
    
    bot.send_message(
        message.chat.id,
        "📝 *Введи текст для добавления идеи:*\n\n(Напиши сообщение или нажми Отмена)",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🔐 Добавить приятность")
def add_personal_prompt(message):
    if not is_authorized(message.from_user.id):
        return
    
    user_states[message.from_user.id] = WAITING_FOR_PERSONAL_TEXT
    
    bot.send_message(
        message.chat.id,
        "🔐 *Введи текст для добавления приятность:*\n\n(Только ты сможешь добавлять сюда, другой пользователь сможет только читать)",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🎲 Взять идею")
def get_shared(message):
    if not is_authorized(message.from_user.id):
        return
    
    result = get_random_from_shared()
    
    if result:
        text, added_by = result
        bot.send_message(
            message.chat.id,
            f"🎲 *Случайная идея:*\n\n📝 {text}\n\n👤 Добавил: {added_by}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        bot.send_message(
            message.chat.id,
            "📭 Общая база пока пуста. Добавьте что-нибудь через кнопку \"📝 Добавить идею\"",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

@bot.message_handler(func=lambda message: message.text == "🔓 Сделать приятность")
def get_others_personal(message):
    if not is_authorized(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    if is_user_a(user_id):
        result = get_random_from_personal_b()
        owner = "Бесёнок"
    else:
        result = get_random_from_personal_a()
        owner = "Буб"
    
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

📁 *Общая база:* {shared_count} записей
🔐 *Личная база Буба:* {personal_a_count} записей
🔐 *Личная база Бесёнка:* {personal_b_count} записей

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
• Нажми "Добавить идею" - все увидят
• Нажми "Добавить приятность" - только ты добавляешь

🎲 *Получение записей:*
• "Взять идеб" - случайная из общего
• "Сделать приятность" - случайная из базы напарника

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

@bot.message_handler(func=lambda message: message.chat.id in [USER_A_ID, USER_B_ID] and message.text and not message.text.startswith('/'))
def handle_text(message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        bot.send_message(
            message.chat.id,
            "🤔 Используй кнопки меню для работы с ботом",
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    state = user_states[user_id]
    text = message.text.strip()
    
    if state == WAITING_FOR_SHARED_TEXT:
        add_to_shared(text, user_id, message.from_user.first_name)
        bot.send_message(
            message.chat.id,
            f"✅ Добавлено в *общую базу идей*!\n\n📝 {text}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )
        del user_states[user_id]
        
    elif state == WAITING_FOR_PERSONAL_TEXT:
        if is_user_a(user_id):
            add_to_personal_a(text, user_id, message.from_user.first_name)
        else:
            add_to_personal_b(text, user_id, message.from_user.first_name)
        
        bot.send_message(
            message.chat.id,
            f"✅ Добавлено в *твою личную базу приятностей*!\n\n📝 {text}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )
        del user_states[user_id]

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    # Инициализация базы данных
    init_database()
    
    logger.info("=" * 50)
    logger.info("Бот запущен и работает с PostgreSQL!")
    logger.info(f"Буб: {USER_A_ID}")
    logger.info(f"Бесёнок: {USER_B_ID}")
    logger.info("=" * 50)
    
    # Запускаем HTTP-сервер для health check в отдельном потоке
    health_thread = threading.Thread(target=run_health_server, args=(10000,), daemon=True)
    health_thread.start()
    
    # Запускаем бота (в основном потоке)
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