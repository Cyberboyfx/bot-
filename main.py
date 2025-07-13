from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import aiohttp
import os

# 🔐 Tokenlaringizni joylashtiring
BOT_TOKEN = ""
OPENAI_API_KEY = ""
openai.api_key = OPENAI_API_KEY

# 💬 Userdan grafik kelganda so‘raladigan so‘rovlar uchun holat
user_states = {}

# ✅ /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_text = f"""👋 Salom, {user_first_name}!

🤖 Bu bot sizga grafiklar asosida texnik tahlil qilishda yordam beradi. Quyidagilardan birini tanlang:"""

    keyboard = [
        ["🖼 Grafik yuborish"],
        ["ℹ️ Bot haqida", "⚠️ Ogohlantirish"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# 📥 Rasm kelganda ishlovchi funksiya
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # Eng yuqori sifatdagi rasmni olish

    file = await context.bot.get_file(photo.file_id)
    image_url = file.file_path  # Telegram CDN'dagi rasm URL

    # Foydalanuvchidan narx, bozor va timeframe so‘rash
    await update.message.reply_text(
        "✅ Rasm qabul qilindi!\n\n📊 Endi iltimos quyidagi formatda ma'lumot yuboring:\n\n`XAUUSD, M5, 1330.00`",
        parse_mode='Markdown'
    )
    user_states[user_id] = {"image_url": image_url}

# 🧾 Matnli xabarlar (masalan: XAUUSD, M5, 1330.00)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # Foydalanuvchi grafik yuborgan bo‘lsa
    if user_id in user_states and "image_url" in user_states[user_id]:
        image_url = user_states[user_id]["image_url"]

        prompt_text = f"Bu grafik uchun texnik tahlil qil:\n\nMa'lumotlar: {text}\n\nTrend, kirish/chiqish nuqtalari, signal (BUY/SELL), TP/SL haqida taxlil ber."

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            answer = response["choices"][0]["message"]["content"]
            await update.message.reply_text(f"📊 Texnik tahlil:\n\n{answer}")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik yuz berdi:\n{e}")
        finally:
            user_states.pop(user_id, None)

    elif text == "🖼 Grafik yuborish":
        await update.message.reply_text("📷 Iltimos, grafik skrinshotini yuboring.")
    elif text == "ℹ️ Bot haqida":
        await update.message.reply_text(
            "📊 Bu bot texnik tahlil uchun yaratilgan. Grafik asosida trend, signal, TP/SL nuqtalarini aniqlab beradi."
        )
    elif text == "⚠️ Ogohlantirish":
        await update.message.reply_text(
            "⚠️ Diqqat: Bu bot AI asosida maslahat beradi. Har qanday moliyaviy qaror faqat sizning javobgarligingizda!"
        )
    else:
        await update.message.reply_text("Iltimos, grafik yuboring yoki menyudan birini tanlang.")

# 🚀 Botni ishga tushirish
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot ishga tushdi...")
app.run_polling()
