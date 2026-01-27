import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask('')
@app.route('/')
def home(): return "Bot Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡SISTEMA ACTIVO! Todo funciona correctamente.")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("❌ Escribe el equipo.")
    await update.message.reply_text(f"📡 Buscando datos para {query}...")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip() # Limpia espacios accidentales
    
    if not TOKEN:
        print("❌ ERROR: No hay Token configurado en Render.")
    else:
        try:
            print(f"🚀 Intentando conectar con Token: {TOKEN[:10]}...")
            application = Application.builder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("analisis", analisis))
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"❌ ERROR CRÍTICO DE TELEGRAM: {e}")
