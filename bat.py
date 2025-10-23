import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== SOZLAMALAR ====================
BOT_TOKEN = "7689583739:AAEjv-It0EICEVYP48lR7toBnvP8Ba2iwOU"
HF_API_KEY = "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"
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

BOT_CONFIG = {
    "max_length": 300,
    "temperature": 0.7,
    "timeout": 30
}
# ====================================================

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🤖 Assalomu alaykum {user.first_name}!

Men Hugging Face AI asosida ishlaydigan chatbotman. 
Sizga qanday yordam bera olaman?

📝 Istalgan savolingizni yozib yuboring!
    """
    await update.message.reply_text(welcome_text)

# /help komandasi
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆗 **Buyruqlar ro'yxati:**

/start - Botni ishga tushirish
/help - Yordam olish
/about - Bot haqida ma'lumot

💬 **Faqat matn yuboring** - Men sizga AI javobini qaytaraman!
    """
    await update.message.reply_text(help_text)

# /about komandasi
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """
🤖 **AI Chat Bot**

📚 **Texnologiyalar:**
- Telegram Bot API
- Hugging Face AI Models
- Python

🔧 **Developer:** AI Assistant
    """
    await update.message.reply_text(about_text)

# Hugging Face API ga so'rov yuborish
def get_hf_response(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": BOT_CONFIG["max_length"],
            "temperature": BOT_CONFIG["temperature"],
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(
            HF_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=BOT_CONFIG["timeout"]
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Turli formatdagi javoblarni qayta ishlash
        if isinstance(result, list) and len(result) > 0:
            if 'generated_text' in result[0]:
                return result[0]['generated_text']
            else:
                return str(result[0])
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
        else:
            return "🤔 Javob tushunarsiz formatda keldi. Qaytadan urinib ko'ring."
            
    except requests.exceptions.Timeout:
        return "⏰ API javob bermadi. Iltimos, keyinroq urinib ko'ring."
    except requests.exceptions.RequestException as e:
        logger.error(f"API so'rov xatosi: {e}")
        return f"🔧 Texnik xatolik: {str(e)}"
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")
        return "❌ Kutilmagan xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."

# Asinxron tarzda API chaqiruv
async def get_ai_response_async(prompt):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, get_hf_response, prompt)
    return response

# Foydalanuvchi xabarlarini qayta ishlash
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # Bo'sh xabarni tekshirish
    if not user_message.strip():
        await update.message.reply_text("📝 Iltimos, matn yuboring!")
        return
    
    # Kutish xabarini yuborish
    waiting_msg = await update.message.reply_text("⏳ AI javob tayyorlanmoqda...")
    
    try:
        # AI dan javob olish
        ai_response = await get_ai_response_async(user_message)
        
        # Xabarni kesish (Telegram limiti 4096 belgi)
        if len(ai_response) > 4000:
            ai_response = ai_response[:4000] + "..."
        
        # Kutish xabarini o'chirish va javobni yuborish
        await waiting_msg.delete()
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        # Xatolik yuz berganda
        await waiting_msg.delete()
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("❌ Javob olishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

# Xatolik handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Xatolik: {context.error}")
    
    if update and update.message:
        await update.message.reply_text("❌ Botda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

# Asosiy funksiya
def main():
    try:
        # Bot ilovasini yaratish
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Handlerlarni qo'shish
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Xatolik handler
        application.add_error_handler(error_handler)
        
        logger.info("Bot ishga tushdi...")
        print("🤖 Bot muvaffaqiyatli ishga tushdi!")
        print("🔑 Token:", BOT_TOKEN[:10] + "..." + BOT_TOKEN[-5:])
        print("🔑 HF Key:", HF_API_KEY[:10] + "..." + HF_API_KEY[-5:])
        print("📍 Model:", HF_API_URL.split('/')[-1])
        print("⏳ Bot ishlayapti...")
        
        # Botni ishga tushirish
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    main()