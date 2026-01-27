import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask('')
@app.route('/')
def home(): return "Analista Multi-Fuente Online"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def get_sofascore_data(query):
    h = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=h).json()
        m = next((res['entity'] for res in r.get('results', []) if res.get('type') == 'event'), None)
        if not m: return None
        
        m_id = m['id']
        o = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=h).json()
        p_h, p_d, p_a, g = 0, 0, 0, "N/A"
        
        for mk in o.get('markets', []):
            if mk['marketName'] == 'Full time':
                c = mk['choices']
                v1, vX, v2 = 1/float(c[0]['fractionalValue']), 1/float(c[1]['fractionalValue']), 1/float(c[2]['fractionalValue'])
                t = v1 + vX + v2
                p_h, p_d, p_a = (v1/t)*100, (vX/t)*100, (v2/t)*100
            if mk['marketName'] == 'Total':
                for ch in mk['choices']:
                    if ch['name'] == 'Over 2.5': g = ch['fractionalValue']
        
        return (f"🏟️ **{m['homeTeam']['name']} vs {m['awayTeam']['name']}** (vía SofaScore)\n"
                f"🛡️ Doble Op: 1X: {round(p_h+p_d)}% | X2: {round(p_d+p_a)}%\n"
                f"⚽ Goles (>2.5): {g}\n"
                f"📊 Prob: 🏠{round(p_h)}% ➖{round(p_d)}% 🚀{round(p_a)}%")
    except: return None

async def get_fotmob_data(query):
    try:
        # FotMob es excelente para nombres más informales
        r = requests.get(f"https://www.fotmob.com/api/search?term={query}").json()
        match = r.get('match', [])
        if not match: return None
        m = match[0]
        return (f"🏟️ **{m['homeName']} vs {m['awayName']}** (vía FotMob)\n"
                f"📅 Fecha: {m['status']['utcTime']}\n"
                f"⚠️ FotMob no provee cuotas directamente, pero el partido está programado.")
    except: return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ **Analista Inteligente V8**\nUsa `/analisis [equipo]`")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args)
    if not q: return await update.message.reply_text("Escribe un equipo.")
    
    await update.message.reply_text(f"📡 Buscando `{q}` en SofaScore y FotMob...")
    
    # Intentar SofaScore primero (tiene las cuotas)
    res = await get_sofascore_data(q)
    
    # Si falla, intentar FotMob (para confirmar el partido)
    if not res:
        res = await get_fotmob_data(q)
        
    if not res:
        res = "❌ No encontré datos en ninguna fuente. Prueba con un nombre más genérico (ej: 'Tucuman' en vez de 'Atlético Tucumán')."
        
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    Thread(target=run_flask).start()
    TOKEN = "".join(os.environ.get('TELEGRAM_TOKEN', '').split())
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("analisis", analisis))
    app_tg.run_polling(drop_pending_updates=True)
