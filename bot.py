import telebot
import sqlite3
import json
from telebot import types
from flask import Flask, request, jsonify
from threading import Thread

# Настройки бота
TOKEN = "8818640282:AAG29Y3Vk3utyvF3fjX0Oy4B0CUqZRccyaQ"
bot = telebot.TeleBot(TOKEN)

# Ссылка на твой GitHub Pages (Параметр ?v=2 сбивает кэш)
# НЕ ЗАБУДЬ поменять 'твой-никнейм' на свой ник на Гитхабе!
WEBAPP_URL = "https://твой-никнейм.github.io/timekiller/?v=2" 

# Создаем Flask-сервер прямо внутри бота для приема тапов
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

# API Эндпоинт: сюда игра будет отправлять натапанное
@app.route('/api/tap', methods=['POST'])
def handle_tap():
    data = request.json
    user_id = data.get('user_id')
    clicks = data.get('clicks', 0)
    
    if user_id:
        save_balance(user_id, clicks)
        new_balance = get_user_balance(user_id)
        return jsonify({"status": "success", "new_balance": new_balance})
    return jsonify({"status": "error"}), 400

# API Эндпоинт: получение баланса при старте игры
@app.route('/api/get_profile', methods=['POST'])
def get_profile():
    data = request.json
    user_id = data.get('user_id')
    if user_id:
        balance = get_user_balance(user_id)
        return jsonify({"balance": balance})
    return jsonify({"error": "no_user"}), 400

@bot.message_handler(commands=['start'])
def start_handler(message):
    # Регистрируем в базе при старте
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

# Функция для запуска Flask в отдельном потоке
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    init_db()
    # Запускаем веб-сервер для связи с игрой
    Thread(target=run_flask).start()
    print("Бот и сервер синхронизации успешно запущены!")
    bot.infinity_polling()
