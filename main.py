import os
import requests
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime
import schedule
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURACIÓN DE SERVIDOR PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "🤖 IA Analista Pro - V10 Activa"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

class BotAnalistaIA:
    def __init__(self):
        # Headers para evitar bloqueos de SofaScore y FotMob
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        self.token = "".join(os.environ.get('TELEGRAM_TOKEN', '').split())
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    async def buscar_partido(self, query):
        """Lógica de búsqueda flexible para encontrar eventos."""
        try:
            # Buscamos directamente en la categoría de eventos (partidos)
            url = f"https://api.sofascore.com/api/v1/search/all?q={query}&type=events"
            r = requests.get(url, headers=self.headers).json()
            results = r.get('results', [])
            
            # Filtramos para obtener la entidad del evento
            for res in results:
                if res.get('type') == 'event':
                    return res['entity']
            return None
        except:
            return None

    async def obtener_reporte(self, match):
        """Extrae cuotas y genera el análisis de probabilidad."""
        m_id = match['id']
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        
        try:
            # Obtenemos cuotas desde SofaScore
            odds_url = f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all"
            o_data = requests.get(odds_url, headers=self.headers).json()
            
            if 'markets' not in o_data:
                return f"🏟️ **{home} vs {away}**\n⚠️ No hay cuotas disponibles para analizar este partido todavía."

            # Extraemos cuotas del mercado 1X2 (Win/Draw/Win)
            m_1x2 = o_data['markets'][0]['choices']
            # Fracción decimal: 1 / cuota = Probabilidad implícita
            prob_h = (1 / float(m_1x2[0]['fractionalValue'].split('/')[0]) if '/' in m_1x2[0]['fractionalValue'] else 1/float(m_1x2[0]['decimalValue'])) * 100
            
            return (f"📊 **ANÁLISIS IA: {home} vs {away}**\n\n"
                    f"🏠 Victoria {home}: {round(prob_h, 1)}%\n"
                    f"🤝 Empate: {m_1x2[1]['decimalValue']}\n"
                    f"🚀 Victoria {away}: {m_1x2[2]['decimalValue']}\n\n"
                    f"💡 **Sugerencia:** Revisar valor en {'Local' if prob_h > 50 else 'Visitante/Empate'}.")
        except:
            return f"🏟️ **{home} vs {away}**\n⚠️ Error al procesar las cuotas en tiempo real."

# --- COMANDOS DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **Sistema V10 Online**\nUsa `/analisis [equipo]` para analizar un partido de hoy.")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ Escribe el nombre de un equipo. Ejemplo: `/analisis Tucuman`")
        return

    bot_ia = BotAnalistaIA()
    msj = await update.message.reply_text(f"🔍 Buscando partido para: {query}...")
    
    match = await bot_ia.buscar_partido(query)
    if match:
        reporte = await bot_ia.obtener_reporte(match)
        await msj.edit_text(reporte, parse_mode='Markdown')
    else:
        await msj.edit_text("❌ No encontré partidos programados. Prueba con un nombre más corto.")

# --- PLANIFICADOR (PARLEY AUTOMÁTICO) ---
def parley_job():
    # Esta función se puede expandir para enviar el parley a tu TELEGRAM_CHAT_ID
    print("Ejecutando escaneo de Parley diario...")

def run_scheduler():
    schedule.every().day.at("09:00").do(parley_job)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Hilos secundarios
    Thread(target=run_flask).start()
    Thread(target=run_scheduler).start()
    
    # Iniciar Telegram
    TOKEN = "".join(os.environ.get('TELEGRAM_TOKEN', '').split())
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analisis", analisis))
    
    print("🚀 Bot iniciado exitosamente...")
    application.run_polling()
