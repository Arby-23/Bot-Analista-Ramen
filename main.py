import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Servidor para que Render no se apague
app = Flask('')
@app.route('/')
def home(): return "Servidor Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Análisis de Fútbol (Doble Oportunidad y Goles)
async def get_analisis(query):
    h = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=h).json()
        m = r['results'][0]['entity']
        m_id, n_h, n_a = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
        
        o = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=h).json()
        p_h, p_d, p_a, g = 0, 0, 0, "-"
        
        for mk in o.get('markets', []):
            if mk['marketName'] == 'Full time':
                c = mk['choices']
                v1, vX, v2 = 1/float(c[0]['fractionalValue']), 1/float(c[1]['fractionalValue']), 1/float(c[2]['fractionalValue'])
                t = v1 + vX + v2
                p_h, p_d, p_a = (v1/t)*100, (vX/t)*100, (v2/t)*100
            if mk['marketName'] == 'Total' and not g != "-":
                for ch in mk['choices']:
                    if ch['name'] == 'Over 2.5': g = ch['fractionalValue']

        return (f"🏟️ **{n_h} vs {n_a}**\n"
                f"🛡️ Doble Op: 1X: {round(p_h+p_d)}% | X2: {round(p_d+p_a)}%\n"
                f"⚽ Goles (>2.5): {g}\n"
                f"📊 Prob: 🏠{round(p_h)}% ➖{round(p_d)}% 🚀{round(p_a)}%")
    except: return "❌ No encontré datos."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **¡CONECTADO!** Usa /analisis [equipo]")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args)
    if not q: return await update.message.reply_text("Escribe un equipo.")
    res = await get_analisis(q)
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask).start()
    # Limpieza total del token
    TOKEN = "".join(os.environ.get('TELEGRAM_TOKEN', '').split())
    
    if TOKEN:
        print(f"DEBUG: Intentando con {TOKEN[:10]}...")
        app_tg = Application.builder().token(TOKEN).build()
        app_tg.add_handler(CommandHandler("start", start))
        app_tg.add_handler(CommandHandler("analisis", analisis))
        app_tg.run_polling(drop_pending_updates=True)
