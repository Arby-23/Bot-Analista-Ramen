import os
import requests
from flask import Flask
from threading import Thread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURACIÓN DE SERVIDOR ---
app = Flask('')
@app.route('/')
def home(): return "Analista Pro V4 Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class SportsAnalystProV4:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_TOKEN')
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.sofascore.com/'
        }

    async def get_h2h_data(self, m_id):
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/h2h", headers=self.headers).json()
            return {"home": r.get('homeWins', 0), "away": r.get('awayWins', 0), "draws": r.get('draws', 0)}
        except: return None

    async def get_real_odds(self, m_id):
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=self.headers).json()
            data = {"1X2": None, "Goles": None}
            for m in r.get('markets', []):
                if m.get('marketName') == 'Full time':
                    c = m.get('choices', [])
                    data["1X2"] = {"1": float(c[0]['fractionalValue']), "X": float(c[1]['fractionalValue']), "2": float(c[2]['fractionalValue'])}
                if m.get('marketName') == 'Total':
                    for choice in m.get('choices', []):
                        if choice.get('name') == 'Over 2.5':
                            data["Goles"] = float(choice.get('fractionalValue'))
            return data
        except: return None

    def generar_reporte(self, home, away, odds_data, h2h):
        odds = odds_data.get("1X2")
        goles_over = odds_data.get("Goles", "-")
        p_home, p_draw, p_away = 0, 0, 0
        if odds:
            p1, pX, p2 = 1/odds['1'], 1/odds['X'], 1/odds['2']
            t = p1 + pX + p2
            p_home, p_draw, p_away = (p1/t)*100, (pX/t)*100, (p2/t)*100

        dc_1x = round(p_home + p_draw)
        dc_x2 = round(p_draw + p_away)

        return (
            f"🏟️ **ANÁLISIS PRO: {home} vs {away}**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🛡️ **DOBLE OPORTUNIDAD:**\n"
            f"• 1X: `{dc_1x}%` | • X2: `{dc_x2}%` \n\n"
            f"⚽ **GOLES (Over 2.5):** `{goles_over}`\n\n"
            f"📊 **1X2 REAL:**\n"
            f"🏠 `{round(p_home)}%` | ➖ `{round(p_draw)}%` | 🚀 `{round(p_away)}%` \n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚀 **¡BOT ACTIVO!**\nUsa `/analisis [equipo]` para empezar.")

    async def analisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query: return await update.message.reply_text("❌ Escribe un equipo.")
        msj = await update.message.reply_text(f"📡 Analizando {query}...")
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=self.headers).json()
            m = r['results'][0]['entity']
            m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
            odds_data = await self.get_real_odds(m_id)
            h2h = await self.get_h2h_data(m_id)
            await msj.edit_text(self.generar_reporte(home, away, odds_data, h2h), parse_mode='Markdown')
        except: await msj.edit_text("❌ No encontré el partido.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot = SportsAnalystProV4()
    app_tg = Application.builder().token(bot.token).build()
    app_tg.add_handler(CommandHandler("start", bot.start))
    app_tg.add_handler(CommandHandler("analisis", bot.analisis))
    app_tg.run_polling()
