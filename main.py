import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SERVER PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Analista Pro V6 - Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- LÓGICA DE CÁLCULO ---
async def obtener_analisis(query):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Búsqueda
        r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=headers).json()
        m = r['results'][0]['entity']
        m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
        
        # Cuotas
        o = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=headers).json()
        p_h, p_d, p_a, g_ov = 0, 0, 0, "-"
        
        for market in o.get('markets', []):
            if market['marketName'] == 'Full time':
                c = market['choices']
                v1, vX, v2 = 1/float(c[0]['fractionalValue']), 1/float(c[1]['fractionalValue']), 1/float(c[2]['fractionalValue'])
                t = v1 + vX + v2
                p_h, p_d, p_a = (v1/t)*100, (vX/t)*100, (v2/t)*100
            if market['marketName'] == 'Total':
                for choice in market['choices']:
                    if choice['name'] == 'Over 2.5': g_ov = choice['fractionalValue']

        return (f"🏟️ **{home} vs {away}**\n"
                f"━━━━━━━━━━━━━━\n"
                f"🛡️ **DOBLE OPORTUNIDAD:**\n"
                f"• 1X: `{round(p_h + p_d)}%` | X2: `{round(p_d + p_a)}%` \n\n"
                f"⚽ **GOLES (>2.5):** `{g_ov}`\n\n"
                f"📊 **1X2 REAL:**\n"
                f"🏠 `{round(p_h)}%` | ➖ `{round(p_d)}%` | 🚀 `{round(p_a)}%` \n"
                f"━━━━━━━━━━━━━━")
    except: return "❌ No se encontraron datos para este equipo."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **¡BOT CONECTADO!**\nUsa `/analisis [equipo]`")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("❌ Escribe el nombre del equipo.")
    res = await obtener_analisis(query)
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # --- LIMPIEZA DE TOKEN (SOLUCIONA EL SALTO DE LÍNEA) ---
    raw_token = os.environ.get('TELEGRAM_TOKEN', '')
    # Quitamos espacios, saltos de línea y retornos de carro
    TOKEN = raw_token.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    
    if not TOKEN:
        print("❌ ERROR: No hay Token en Render.")
    else:
        try:
            print(f"🚀 Iniciando Bot con Token: {TOKEN[:10]}...")
            app_tg = Application.builder().token(TOKEN).build()
            app_tg.add_handler(CommandHandler("start", start))
            app_tg.add_handler(CommandHandler("analisis", analisis))
            app_tg.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"❌ FALLO DE CONEXIÓN: {e}")
