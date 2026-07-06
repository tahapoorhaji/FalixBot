import os
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

# --- تنظیمات اکانت گیت‌هاب شما ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') # توکن گیت‌هاب برای دسترسی ربات به اکشنز
REPO_OWNER = "tahapoorhaji"              # نام کاربری گیت‌هاب شما
REPO_NAME = "FalixBot"                  # نام ریپازیتوری شما
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Falix Linker is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# تابع فرستادن دستور به گیت‌هاب اکشنز
def trigger_github_action(action_type):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/start.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # فرستادن اینکه استارت بزنه یا استپ
    data = {"ref": "main", "inputs": {"action": action_type}}
    res = requests.post(url, json=data, headers=headers)
    return res.status_code

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🟢 روشن کردن سرور", callback_data="run_start"),
        InlineKeyboardButton("🔴 خاموش کردن سرور", callback_data="run_stop")
    )
    return markup

@bot.message_handler(commands=['start', 'panel'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🕹️ **منوی اصلی کنترل سرور فالیکس:**\n\nبرای کنترل دکمه‌های زیر را بزن:", reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    bot.answer_callback_query(call.id)
    
    if call.data == "run_start":
        bot.edit_message_text("⏳ دستور روشن شدن به GitHub Actions فرستاده شد. مرورگر مجازی داره راه میفته...", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("start")
        if status == 204:
            bot.edit_message_text("✅ گیت‌هاب اکشنز با موفقیت استارت شد! تا ۲ دقیقه دیگه سرور روشنه.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.edit_message_text(f"❌ خطا در اتصال به گیت‌هاب. کد خطا: {status}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
            
    elif call.data == "run_stop":
        bot.edit_message_text("⏳ دستور خاموش شدن فرستاده شد...", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("stop")
        if status == 204:
            bot.edit_message_text("✅ اکشن خاموش کردن فعال شد.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        else:
            bot.edit_message_text(f"❌ خطا: {status}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()