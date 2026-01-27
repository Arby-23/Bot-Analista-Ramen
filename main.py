import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Servidor Web básico para Render
app = Flask('')
@app.route('/')
def home(): return "Bot Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Lógica del Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡SISTEMA ACTIVO! Usa /analisis [equipo]")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("❌ Escribe un equipo.")
    await update.message.reply_text(f"📡 Buscando datos para {query}...")
    # Aquí va el resto de tu lógica de análisis...

if __name__ == '__main__':
    # 1. Iniciar Web
    Thread(target=run_flask).start()
    
    # 2. Iniciar Telegram
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TOKEN:
        print("❌ ERROR: No hay Token en Environment")
    else:
        print("🚀 INICIANDO BOT DE TELEGRAM...")
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("analisis", analisis))
        application.run_polling(drop_pending_updates=True)
