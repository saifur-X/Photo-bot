import io
from flask import Flask, request
import telebot
from PIL import Image

app = Flask(__name__)

# Apnar Bot Token sorasori dewa holo
BOT_TOKEN = "8135991995:AAHiHmqR7_JvF2t3aeE2yoFjAwsdwXR6uQU"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/', methods=['GET'])
def index():
    return "Photo Optimizer Bot (@Bot_wife_bot) is Live on Vercel!", 200

# Webhook set korar jonno ei link-ti kaj korbe
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = f"https://{request.host}/"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook successfully connected to: {webhook_url}", 200

# /start command dile ei reply jabe
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **হ্যালো! Photo Optimizer Bot-এ আপনাকে স্বাগতম।**\n\n"
        "📸 আমাকে যেকোনো ছবি (Photo) পাঠান, আমি সেটির কোয়ালিটি নষ্ট না করেই সাইজ কমপ্রেস ও অপ্টিমাইজ করে দেবো!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# User chobi pathale seta optimize korar code
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # User-ke waiting message dewa
        wait_msg = bot.reply_to(message, "⏳ ছবিটি অপ্টিমাইজ করা হচ্ছে, একটু অপেক্ষা করুন...")

        # Original chobir size ber kora
        file_info = bot.get_file(message.photo[-1].file_id)
        orig_size_kb = round(file_info.file_size / 1024, 2)
        downloaded_file = bot.download_file(file_info.file_path)

        # Pillow diye chobi optimize kora
        image = Image.open(io.BytesIO(downloaded_file))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        output = io.BytesIO()
        image.save(output, format="JPEG", optimize=True, quality=70)
        opt_size_kb = round(output.tell() / 1024, 2)
        output.seek(0)

        # Optimized chobi user-ke Document hisebe pathano (jate Telegram abar compress na kore)
        caption_text = (
            f"✅ **ছবি অপ্টিমাইজ সম্পন্ন হয়েছে!**\n"
            f"📉 আগের সাইজ: `{orig_size_kb} KB`\n"
            f"⚡ বর্তমান সাইজ: `{opt_size_kb} KB`"
        )
        bot.send_document(
            message.chat.id, 
            output, 
            visible_file_name="optimized_photo.jpg", 
            caption=caption_text,
            parse_mode="Markdown"
        )
        
        # Waiting message delete kore dewa
        bot.delete_message(message.chat.id, wait_msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ ছবিটি প্রসেস করতে সমস্যা হয়েছে: {str(e)}")
      
