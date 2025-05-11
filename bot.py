import os
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.environ["BOT_TOKEN"]           # токен зададим позже в настройках

async def start(update, ctx):
    await update.message.reply_text("Бот жив!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()