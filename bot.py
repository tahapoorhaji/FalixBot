import os
import threading
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import websocket

# --- تنظیمات اولیه ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
FALIX_API_KEY = os.getenv('FALIX_API_KEY')
SERVER_ID = "3241406"  # شناسه سرور شما طبق عکس
BASE_URL = "https://client.falixnodes.net/api/client/servers"

bot = telebot.TeleBot(BOT_TOKEN)
headers = {
    "Authorization": f"Bearer {FALIX_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- وب‌سرور Flask برای زنده نگه داشتن ربات در رندر ---
app = Flask(__name__)

@app.route('/')
def home():
    return "FalixBot Is Online and Alive!", 200

def run_flask():
    # رندر پورت را به صورت متغیر محیطی می‌دهد
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --- ساخت منوی دکمه‌های شیشه‌ای (فارسی و شیک) ---
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🟢 روشن کردن", callback_data="power_start"),
        InlineKeyboardButton("🔴 خاموش کردن", callback_data="power_stop"),
        InlineKeyboardButton("🔄 ری‌استارت", callback_data="power_restart"),
        InlineKeyboardButton("⚠️ کیل اجباری (Kill)", callback_data="power_kill")
    )
    markup.add(
        InlineKeyboardButton("📊 وضعیت منابع زنده", callback_data="status"),
        InlineKeyboardButton("🌐 اطلاعات اتصال (IP)", callback_data="connect_info")
    )
    markup.add(
        InlineKeyboardButton("👥 پلیرهای آنلاین", callback_data="players"),
        InlineKeyboardButton("📜 آخرین لاگ‌ها", callback_data="logs")
    )
    markup.add(InlineKeyboardButton("💻 ارسال دستور سریع", callback_data="cmd_menu"))
    return markup

# --- بازگشت به منوی اصلی ---
def back_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main"))
    return markup

# --- دستور /start یا /panel ---
@bot.message_handler(commands=['start', 'panel'])
def send_welcome(message):
    welcome_text = (
        "👑 **به پنل مدیریت پیشرفته سرور ماینکرافت خوش آمدید!**\n\n"
        "بدون نیاز به باز کردن سایت، سرورت را با دکمه‌های زیر کنترل کن:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# --- مدیریت کلیک روی دکمه‌ها ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    bot.answer_callback_query(call.id)
    
    # منوی اصلی
    if call.data == "back_main":
        bot.edit_message_text("👑 **منوی اصلی کنترل سرور:**", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
    
    # کنترل برق سرور
    elif call.data.startswith("power_"):
        action = call.data.split("_")[1]
        action_fa = {"start": "روشن شدن", "stop": "خاموش شدن", "restart": "ری‌استارت", "kill": "خاموشی اجباری"}[action]
        bot.edit_message_text(f"⏳ در حال ارسال دستور {action_fa}...", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        
        try:
            res = requests.post(f"{BASE_URL}/{SERVER_ID}/power", json={"signal": action}, headers=headers)
            if res.status_code == 204:
                bot.edit_message_text(f"✅ دستور **{action_fa}** با موفقیت فرستاده شد.", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
            else:
                bot.edit_message_text(f"❌ خطا از سمت فالیکس. کد خطا: {res.status_code}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {str(e)}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    # منابع سخت‌افزاری
    elif call.data == "status":
        bot.edit_message_text("⏳ در حال دریافت آمار زنده سخت‌افزار...", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        try:
            res = requests.get(f"{BASE_URL}/{SERVER_ID}/resources", headers=headers)
            if res.status_code == 200:
                data = res.json()['attributes']
                state = data['current_state']
                state_fa = {"running": "🟢 آنلاین", "offline": "🔴 خاموش", "starting": "🟡 در حال روشن شدن", "stopping": "🟠 در حال خاموش شدن"}.get(state, state)
                
                ram = round(data['resources']['memory_bytes'] / (1024 * 1024), 1)
                cpu = round(data['resources']['cpu_absolute'], 1)
                disk = round(data['resources']['disk_bytes'] / (1024 * 1024), 1)
                
                status_text = (
                    f"📊 **وضعیت لحظه‌ای سخت‌افزار:**\n\n"
                    f"🔹 وضعیت: {state_fa}\n"
                    f"💻 مصرف سی‌پی‌یو: {cpu}%\n"
                    f"💾 مصرف رم: {ram} مگابایت\n"
                    f"🗄️ فضای دیسک: {disk} مگابایت\n"
                )
                bot.edit_message_text(status_text, call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        except:
            bot.edit_message_text("❌ خطا در دریافت اطلاعات سخت‌افزار.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    # اطلاعات اتصال
    elif call.data == "connect_info":
        try:
            res = requests.get(f"{BASE_URL}/{SERVER_ID}", headers=headers)
            if res.status_code == 200:
                allocations = res.json()['attributes']['relationships']['allocations']['data']
                ip_info = "🎮 **اطلاعات اتصال به سرور:**\n\n"
                for i, alloc in enumerate(allocations):
                    # اگر سرور چند پورت داشته باشد همه را نشان می‌دهد (مثل جاوا و پورت Geyser بدراک)
                    ip_info += f"🔗 آدرس {i+1}: `{alloc['attributes']['ip_alias'] if alloc['attributes']['ip_alias'] else alloc['attributes']['ip']}:{alloc['attributes']['port']}`\n"
                bot.edit_message_text(ip_info, call.message.chat.id, call.message.message_id, reply_markup=back_menu(), parse_mode="Markdown")
        except:
            # اگر دریافت خودکار خطا داد، آدرس پیش‌فرض عکس شما را نشان می‌دهد
            bot.edit_message_text("🎮 **اطلاعات اتصال (پیش‌فرض):**\n\n🔗 آی‌پی: `zedkaf.falixsrv.me`\n🔹 پورت بدراک (Geyser): `56011`", call.message.chat.id, call.message.message_id, reply_markup=back_menu(), parse_mode="Markdown")

    # دریافت توکن وب‌سوکت برای لاگ زنده و پلیرها (سیستم پیشرفته Pterodactyl)
    elif call.data in ["logs", "players", "cmd_menu"]:
        bot.edit_message_text("⏳ در حال برقراری ارتباط امن با کنسول سرور...", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        try:
            token_res = requests.get(f"{BASE_URL}/{SERVER_ID}/websocket", headers=headers)
            if token_res.status_code == 200:
                ws_data = token_res.json()['data']
                ws_url = ws_data['socket']
                token = ws_data['token']
                
                # اجرای یک وب‌سوکت موقت برای گرفتن داتا
                ws = websocket.create_connection(ws_url)
                # احراز هویت در وب‌سوکت فالیکس
                ws.send(json.dumps({"event": "auth", "args": [token]}))
                
                if call.data == "logs":
                    # دریافت لاگ‌های آخر سرور
                    logs = ""
                    ws.settimeout(2.0)
                    try:
                        for _ in range(15): # خواندن ۱۵ خط آخر لاگ
                            msg = json.loads(ws.recv())
                            if msg['event'] == 'console output':
                                logs += msg['args'][0] + "\n"
                    except:
                        pass
                    ws.close()
                    clean_logs = logs[-300:] if logs else "لاگی یافت نشد یا سرور خاموش است."
                    bot.edit_message_text(f"📜 **آخرین لاگ‌های کنسول:**\n\n`{clean_logs}`", call.message.chat.id, call.message.message_id, reply_markup=back_menu(), parse_mode="Markdown")
                
                elif call.data == "players":
                    # ارسال دستور list برای گرفتن پلیرها
                    ws.send(json.dumps({"event": "send command", "args": ["list"]}))
                    players_output = "سرور در حال پاسخگویی نیست."
                    ws.settimeout(2.0)
                    try:
                        for _ in range(10):
                            msg = json.loads(ws.recv())
                            if msg['event'] == 'console output' and "players online" in msg['args'][0].lower():
                                players_output = msg['args'][0]
                                break
                    except:
                        pass
                    ws.close()
                    bot.edit_message_text(f"👥 **وضعیت پلیرها:**\n\n`{players_output}`", call.message.chat.id, call.message.message_id, reply_markup=back_menu(), parse_mode="Markdown")
                
                elif call.data == "cmd_menu":
                    ws.close()
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("📢 بگو سلام (say Hello)", callback_data="run_cmd_hello"))
                    markup.add(InlineKeyboardButton("☀️ روز کردن هوا (time set day)", callback_data="run_cmd_day"))
                    markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
                    bot.edit_message_text("💻 **منوی دستورات سریع کنسول:**\nیکی از دستورات زیر را انتخاب کن:", call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ سرور خاموش است یا وب‌سوکت پنل پاسخ نمی‌دهد.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        except Exception as e:
            bot.edit_message_text(f"❌ خطا در اتصال به وب‌سوکت: {str(e)}", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    # اجرای دستورات سریع
    elif call.data.startswith("run_cmd_"):
        cmd_type = call.data.split("_")[2]
        command = "say Hello from Telegram Bot!" if cmd_type == "hello" else "time set day"
        try:
            requests.post(f"{BASE_URL}/{SERVER_ID}/command", json={"command": command}, headers=headers)
            bot.edit_message_text(f"✅ دستور `{command}` با موفقیت به کنسول ارسال شد.", call.message.chat.id, call.message.message_id, reply_markup=back_menu(), parse_mode="Markdown")
        except:
            bot.edit_message_text("❌ خطا در ارسال دستور.", call.message.chat.id, call.message.message_id, reply_markup=back_menu())

if __name__ == "__main__":
    # اجرای وب‌سرور فلسک در یک ترد پس‌زمینه
    threading.Thread(target=run_flask, daemon=True).start()
    # اجرای ربات تلگرام
    bot.infinity_polling()