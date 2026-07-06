import os
import telebot
import requests

# دریافت اطلاعات حساس از محیط برنامه
BOT_TOKEN = os.getenv('BOT_TOKEN')
FALIX_API_KEY = os.getenv('FALIX_API_KEY')
SERVER_ID = "3241406"  # شناسه سرور شما
BASE_URL = "https://client.falixnodes.net/api/client/servers"

bot = telebot.TeleBot(BOT_TOKEN)
headers = {
    "Authorization": f"Bearer {FALIX_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! به ربات مدیریت سرور فالیکس خوش آمدید.\n\nدستورات:\n/power_start - روشن کردن سرور\n/status - وضعیت سرور")

@bot.message_handler(commands=['power_start'])
def start_server(message):
    url = f"{BASE_URL}/{SERVER_ID}/power"
    data = {"signal": "start"}
    
    bot.reply_to(message, "⏳ در حال ارسال دستور روشن شدن...")
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 204:
            bot.reply_to(message, "✅ دستور روشن شدن با موفقیت ارسال شد!")
        else:
            bot.reply_to(message, f"❌ خطا در ارتباط با فالیکس. کد خطا: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ خطای نامشخص: {str(e)}")

@bot.message_handler(commands=['status'])
def server_status(message):
    url = f"{BASE_URL}/{SERVER_ID}/resources"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            status = response.json()['attributes']['current_state']
            bot.reply_to(message, f"📊 وضعیت فعلی سرور: **{status}**")
        else:
            bot.reply_to(message, "❌ نتوانستم وضعیت سرور را دریافت کنم.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
