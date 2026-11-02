import io
import re
from flask import Flask, request
import telebot
from PIL import Image

app = Flask(__name__)

BOT_TOKEN = "8135991995:AAHiHmqR7_JvF2t3aeE2yoFjAwsdwXR6uQU"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# User-er target KB temporary store korar jonno
user_targets = {}

def compress_to_target_kb(image_bytes, target_kb):
    """Chobir quality ebong resolution adjust kore exact target KB-er niche anar function"""
    target_bytes = target_kb * 1024
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    output = io.BytesIO()
    
    # Step 1: Quality komiye check kora (95 theke 10 porjonto)
    for q in range(95, 5, -5):
        output.seek(0)
        output.truncate()
        img.save(output, format="JPEG", optimize=True, quality=q)
        if output.tell() <= target_bytes:
            output.seek(0)
            return output, round(output.tell() / 1024, 2)
            
    # Step 2: Jodi khub choto KB (jemon 10KB-20KB) chay, tahole dimension resize kora
    width, height = img.size
    while output.tell() > target_bytes and width > 100 and height > 100:
        width = int(width * 0.85)
        height = int(height * 0.85)
        resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        output.seek(0)
        output.truncate()
        resized_img.save(output, format="JPEG", optimize=True, quality=25)
        
    output.seek(0)
    return output, round(output.tell() / 1024, 2)


def process_and_send_photo(chat_id, file_id, target_kb, reply_to_id):
    wait_msg = bot.send_message(
        chat_id, 
        f"⏳ ছবিটি **{target_kb} KB**-তে তৈরি করা হচ্ছে, একটু অপেক্ষা করুন...", 
        reply_to_message_id=reply_to_id,
        parse_mode="Markdown"
    )
    try:
        file_info = bot.get_file(file_id)
        orig_kb = round(file_info.file_size / 1024, 2)
        downloaded_file = bot.download_file(file_info.file_path)

        output, final_kb = compress_to_target_kb(downloaded_file, target_kb)

        caption = (
            f"✅ **Done! Target: {target_kb} KB**\n"
            f"📉 আগের সাইজ: `{orig_kb} KB`\n"
            f"⚡ বর্তমান সাইজ: `{final_kb} KB`"
        )
        
        # Preview-er jonno Photo hisebe pathano
        bot.send_photo(chat_id, output, caption=caption, parse_mode="Markdown")
        
        # Exact KB thik rakhar jonno Document/File hisebeo pathano
        output.seek(0)
        bot.send_document(
            chat_id, 
            output, 
            visible_file_name=f"photo_{int(final_kb)}kb.jpg",
            caption=f"📁 আসল ফাইল ({final_kb} KB) — ডাউনলোড করে ব্যবহার করুন।"
        )
        bot.delete_message(chat_id, wait_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ সমস্যা হয়েছে: {str(e)}", chat_id, wait_msg.message_id)


# Vercel-er sob URL route handle korar jonno
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            return str(e), 500

    if 'set_webhook' in path:
        webhook_url = f"https://{request.host}/"
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return f"Webhook successfully connected to: {webhook_url}", 200

    return "Photo Optimizer Bot is Running!", 200


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **হ্যালো! Photo Optimizer Bot-এ স্বাগতম।**\n\n"
        "আপনি যেকোনো ছবি আপনার পছন্দমতো সাইজে (KB) ছোট করতে পারবেন:\n\n"
        "১️⃣ প্রথমে কত KB চান তা লিখুন (যেমন: `50` বা `50kb`), তারপর ছবি পাঠান।\n"
        "২️⃣ অথবা সরাসরি ছবি পাঠান, বট আপনাকে সাইজ জিজ্ঞেস করবে!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")


# User jokhon KB likhe message pathabe (jemon: "50", "50kb", "100 KB")
@bot.message_handler(func=lambda message: message.content_type == 'text' and not message.text.startswith('/'))
def handle_text_kb(message):
    match = re.search(r'(\d+)', message.text)
    if not match:
        bot.reply_to(message, "⚠️ দয়া করে কত KB চান তা সংখ্যায় লিখুন (যেমন: `50` বা `100kb`) অথবা সরাসরি একটি ছবি পাঠান।", parse_mode="Markdown")
        return

    target_kb = int(match.group(1))
    if target_kb < 5 or target_kb > 5000:
        bot.reply_to(message, "⚠️ দয়া করে 5 KB থেকে 5000 KB-এর মধ্যে যেকোনো সংখ্যা লিখুন।")
        return

    user_targets[message.chat.id] = target_kb

    # Case 1: User age chobi pathiyeche, ekhon bot-er proshner reply-te KB likhlo
    if message.reply_to_message and message.reply_to_message.reply_to_message:
        orig_msg = message.reply_to_message.reply_to_message
        if orig_msg.content_type == 'photo':
            process_and_send_photo(message.chat.id, orig_msg.photo[-1].file_id, target_kb, orig_msg.message_id)
            return

    # Case 2: User shudhu target KB set korlo
    bot.reply_to(
        message, 
        f"✅ **Target Set: {target_kb} KB**\nএখন আপনার ছবি (Photo) পাঠান, আমি সেটি {target_kb} KB-এর মধ্যে করে দিচ্ছি!", 
        parse_mode="Markdown"
    )


# User jokhon Photo pathabe
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    target_kb = None
    
    # Chobir caption-e KB lekha ache kina check kora
    if message.caption:
        match = re.search(r'(\d+)', message.caption)
        if match:
            target_kb = int(match.group(1))
            user_targets[message.chat.id] = target_kb

    # Age theke KB bolle seta neবে
    if not target_kb:
        target_kb = user_targets.get(message.chat.id)

    # Jodi KB bola thake, sorasori optimize kore debe
    if target_kb:
        process_and_send_photo(message.chat.id, message.photo[-1].file_id, target_kb, message.message_id)
    else:
        # Jodi KB bola na thake, tahole ForceReply diye user-ke jiggesh korbe
        markup = telebot.types.ForceReply(selective=False, input_field_placeholder="যেমন: 50 বা 100")
        bot.reply_to(
            message, 
            "📏 **ছবিটি কত KB করতে চান?**\nসংখ্যাটি লিখে সেন্ড করুন (যেমন: `50`):", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
        
