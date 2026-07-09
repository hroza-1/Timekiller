import telebot
import sqlite3
from telebot import types
from flask import Flask, request, jsonify

# Настройки бота
TOKEN = "8818640282:AAG29Y3Vk3utyvF3fjX0Oy4B0CUqZRccyaQ"
bot = telebot.TeleBot(TOKEN)

# Твой адрес на Render
RENDER_URL = "https://timekiller.onrender.com"

# Твой GitHub Pages
WEBAPP_URL = "https://hroza-2.github.io/timekiller/?v=2" 

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("timekiller.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (telegram_id INTEGER PRIMARY KEY, balance INTEGER, energy INTEGER)''')
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect("timekiller.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def save_balance(user_id, added_clicks):
    conn = sqlite3.connect("timekiller.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (added_clicks, user_id))
    else:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, added_clicks, 1000))
    conn.commit()
    conn.close()

# Эндпоинт для приема сообщений от самого Telegram (Webhook)
@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# API Эндпоинты для игры
@app.route('/api/tap', methods=['POST'])
def handle_tap():
    data = request.json
    user_id = data.get('user_id')
    clicks = data.get('clicks', 0)
    if user_id:
        save_balance(user_id, clicks)
        return jsonify({"status": "success", "new_balance": get_user_balance(user_id)})
    return jsonify({"status": "error"}), 400

@app.route('/api/get_profile', methods=['POST'])
def get_profile():
    data = request.json
    user_id = data.get('user_id')
    if user_id:
        return jsonify({"balance": get_user_balance(user_id)})
    return jsonify({"error": "no_user"}), 400

# Обработка команд
@bot.message_handler(commands=['start'])
def start_handler(message):
    save_balance(message.from_user.id, 0)
    inline_markup = types.InlineKeyboardMarkup()
    webapp_info = types.WebAppInfo(WEBAPP_URL)
    btn_apps = types.InlineKeyboardButton(text="🎮 Запустить TimeKiller", web_app=webapp_info)
    inline_markup.add(btn_apps)

    bot.send_message(
        message.chat.id, 
        f"Привет, {message.from_user.first_name}! 🚀\nТвой текущий баланс: {get_user_balance(message.from_user.id)} 💰\n\nНажимай кнопку ниже, чтобы начать убивать время:", 
        reply_markup=inline_markup
    )

# Главная страничка для проверки в браузере
@app.route('/')
def index():
    return "Bot server is running successfully!", 200

# Правильный запуск инициализации базы и вебхука внутри Flask
@app.before_request
def setup():
    init_db()
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
