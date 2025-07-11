from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes,
)

TOKEN = "8088509339:AAGtA8bAN4pLKilOKZjBT7scuLm6GIj4_h8"  # заменяй на свой

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здарова, я твой бот! Чем помочь?")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
