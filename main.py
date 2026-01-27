import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- SERVIDOR WEB PARA RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Analista Pro V5 - Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- LÓGICA DEL ANALISTA ---
async def get_data(query):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # 1. Buscar Partido
        r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=headers).json()
        m = r['results'][0]['entity']
        m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
        
        # 2. Obtener Cuotas (1X2 y Goles)
        o = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=headers).json()
        p_h, p_d, p_a, g_ov = 0, 0, 0, "-"
        
        for market in o.get('markets', []):
            if market['marketName'] == 'Full time':
                c = market['choices']
                v1, vX, v2 = 1/float(c[0]['fractionalValue']), 1/float(c[1]['fractionalValue']), 1/float(c[2]['fractionalValue'])
                total = v1 + vX + v2
                p_h, p_d, p_a = (v1/total)*100, (vX/total)*100, (v2/total)*100
            if market['marketName'] == 'Total':
                for choice in market['choices']:
                    if choice['name'] == 'Over 2.5': g_ov = choice['fractionalValue']

        return (f"🏟️ **{home} vs {away}**\n"
                f"━━━━━━━━━━━━━━\n"
                f"🛡️ **DOBLE OPORTUNIDAD:**\n"
                f"• 1X: `{round(p_h + p_d)}%` | X2: `{round(p_d + p_a)}%` \n\n"
                f"⚽ **GOLES (>2.5):** `{g_ov}`\n\n"
                f"📊 **PROBABILIDAD 1X2:**\n"
                f"🏠 `{round(p_h)}%` | ➖ `{round(p_d)}%` | 🚀 `{round(p_a)}%` \n"
                f"━━━━━━━━━━━━━━")
    except: return "❌ No encontré datos para ese equipo."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Analista V5 Activo**\nUsa `/analisis [equipo]`")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query: return await update.message.reply_text("❌ Escribe el equipo.")
    res = await get_data(query)
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask).start()
    # .strip() elimina el espacio que vimos en tu captura
    TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
    
    print("🚀 INICIANDO BOT...")
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("analisis", analisis))
    app_tg.run_polling(drop_pending_updates=True)
