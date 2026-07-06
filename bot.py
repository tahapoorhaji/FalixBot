import os
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# --- تنظیمات اکانت گیت‌هاب شما ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') 
REPO_OWNER = "tahapoorhaji"              
REPO_NAME = "FalixBot"                  
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# دیکشنری برای ذخیره پیام‌های وضعیت لاگ کاربران جهت متوقف کردن اختیاری
user_logging_state = {}

@app.route('/')
def home():
    return "Falix Linker is running!", 200

@app.route('/stop_log', methods=['POST'])
def stop_log():
    # این مسیر به گیت‌هاب اجازه می‌دهد بفهمد کاربر دکمه توقف را زده است یا خیر
    data = request.json
    chat_id = str(data.get("chat_id"))
    return {"stop": user_logging_state.get(chat_id) == "stop"}, 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def trigger_github_action(action_type, chat_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/start.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    # ارسال نوع عملیات و شناسه چت کاربر به گیت‌هاب
    data = {
        "ref": "main", 
        "inputs": {
            "action": action_type,
            "chat_id": str(chat_id)
        }
    }
    res = requests.post(url, json=data, headers=headers)
    return res.status_code

def main_menu():
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(
        InlineKeyboardButton("🟢 روشن کردن", callback_data="run_start"),
        InlineKeyboardButton("🔴 خاموش کردن", callback_data="run_stop"),
        InlineKeyboardButton("🔄 ری‌استارت", callback_data="run_restart")
    )
    markup.add(
        InlineKeyboardButton("📋 مشاهده زنده لاگ و وضعیت", callback_data="run_logs")
    )
    return markup

@bot.message_handler(commands=['start', 'panel', 'menu'])
def send_welcome(message):
    text = (
        "🖥️ **پنل پیشرفته کنترل سرور فالیکس** 🖥️\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 جهت مدیریت سرور و دریافت گزارش زنده، دکمه‌های زیر را لمس کنید:"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if call.data == "run_start":
        bot.edit_message_text("⏳ دستور **روشن شدن** به GitHub Actions فرستاده شد. مرورگر در حال آماده‌سازی است...", chat_id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("start", chat_id)
        if status == 204:
            bot.send_message(chat_id, "✅ عملیات گیت‌هاب با موفقیت آغاز شد! تا چند لحظه دیگر وضعیت اعمال می‌شود.")
        else:
            bot.send_message(chat_id, f"❌ خطا در اتصال به گیت‌هاب. کد خطا: {status}")
            
    elif call.data == "run_stop":
        bot.edit_message_text("⏳ دستور **خاموش شدن** فرستاده شد...", chat_id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("stop", chat_id)
        if status == 204:
            bot.send_message(chat_id, "✅ عملیات خاموش کردن با موفقیت آغاز شد.")
        else:
            bot.send_message(chat_id, f"❌ خطا: {status}")

    elif call.data == "run_restart":
        bot.edit_message_text("⏳ دستور **ری‌استارت سرور** فرستاده شد...", chat_id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("restart", chat_id)
        if status == 204:
            bot.send_message(chat_id, "✅ عملیات ری‌استارت سرور با موفقیت آغاز شد.")
        else:
            bot.send_message(chat_id, f"❌ خطا: {status}")

    elif call.data == "run_logs":
        user_logging_state[str(chat_id)] = "run"
        bot.edit_message_text("⏳ دستور استخراج **وضعیت سیستم و لاگ زنده** به گیت‌هاب ارسال شد. لطفاً صبور باشید...", chat_id, call.message.message_id, reply_markup=main_menu())
        status = trigger_github_action("logs", chat_id)
        if status != 204:
            bot.send_message(chat_id, f"❌ خطا در درخواست لاگ: {status}")

    elif call.data == "stop_current_stream":
        user_logging_state[str(chat_id)] = "stop"
        bot.send_message(chat_id, "⏹️ دستور توقف نمایش لاگ صادر شد. گیت‌هاب در دور بعدی متوقف می‌شود.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
