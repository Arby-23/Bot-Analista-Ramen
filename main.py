import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask('')
@app.route('/')
def home(): return "Analista Pro V6 - Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Función de limpieza extrema para tu Token
def get_clean_token():
    raw_token = os.environ.get('TELEGRAM_TOKEN', '')
    # Quitamos saltos de línea, retornos, espacios y tabulaciones
    clean = "".join(raw_token.split())
    return clean

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡POR FIN CONECTADO!\nEl bot está listo. Usa /analisis [equipo]")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("❌ Escribe el equipo.")
    await update.message.reply_text(f"📡 Buscando datos para {query}...")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    TOKEN = get_clean_token()
    
    if not TOKEN:
        print("❌ ERROR: No se detectó ningún Token.")
    else:
        try:
            # Imprimimos los extremos para verificar que se unió bien
            print(f"🚀 Intentando conexión con: {TOKEN[:5]}...{TOKEN[-5:]}")
            application = Application.builder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("analisis", analisis))
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"❌ ERROR DE TELEGRAM: {e}")
