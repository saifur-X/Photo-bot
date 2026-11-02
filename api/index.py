import io
from flask import Flask, request
import telebot
from PIL import Image

app = Flask(__name__)

BOT_TOKEN = "8135991995:AAHiHmqR7_JvF2t3aeE2yoFjAwsdwXR6uQU"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Jekono URL path handle korar jonno catch-all route
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    # Telegram theke message (POST request) asle
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            return str(e), 500

    # Browser theke /set_webhook visit korle
    if 'set_webhook' in path:
        webhook_url = f"https://{request.host}/"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return f"Webhook successfully connected to: {webhook_url}", 200

    return "Photo Optimizer Bot is Live and Running!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 হ্যালো! Photo Optimizer Bot-এ আপনাকে স্বাগতম।\n\n"
        "📸 আমাকে যেকোনো ছবি (Photo) পাঠান, আমি সেটির কোয়ালিটি ঠিক রেখে সাইজ অপ্টিমাইজ করে দেবো!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        wait_msg = bot.reply_to(message, "⏳ ছবিটি অপ্টিমাইজ করা হচ্ছে, একটু অপেক্ষা করুন...")

        file_info = bot.get_file(message.photo[-1].file_id)
        orig_size_kb = round(file_info.file_size / 1024, 2)
        downloaded_file = bot.download_file(file_info.file_path)

        image = Image.open(io.BytesIO(downloaded_file))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        output = io.BytesIO()
        image.save(output, format="JPEG", optimize=True, quality=70)
        opt_size_kb = round(output.tell() / 1024, 2)
        output.seek(0)

        caption_text = (
            f"✅ ছবি অপ্টিমাইজ সম্পন্ন হয়েছে!\n"
            f"📉 আগের সাইজ: {orig_size_kb} KB\n"
            f"⚡ বর্তমান সাইজ: {opt_size_kb} KB"
        )
        bot.send_document(
            message.chat.id, 
            output, 
            visible_file_name="optimized_photo.jpg", 
            caption=caption_text
        )
        bot.delete_message(message.chat.id, wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ ছবিটি প্রসেস করতে সমস্যা হয়েছে: {str(e)}")
        
