import os
import requests
from flask import Flask
from threading import Thread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURACIÓN DE SERVIDOR PARA RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Analista Pro V5 - Online y Escuchando"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class SportsAnalystV5:
    def __init__(self):
        # Render leerá esto de tu pestaña 'Environment'
        self.token = os.environ.get('TELEGRAM_TOKEN')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sofascore.com/'
        }

    async def get_h2h_data(self, m_id):
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/h2h", headers=self.headers, timeout=10).json()
            return {"home": r.get('homeWins', 0), "away": r.get('awayWins', 0), "draws": r.get('draws', 0)}
        except: return None

    async def get_real_odds(self, m_id):
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=self.headers, timeout=10).json()
            data = {"1X2": None, "Goles": None}
            for m in r.get('markets', []):
                if m.get('marketName') == 'Full time':
                    c = m.get('choices', [])
                    data["1X2"] = {"1": float(c[0].get('fractionalValue', 1)), "X": float(c[1].get('fractionalValue', 1)), "2": float(c[2].get('fractionalValue', 1))}
                if m.get('marketName') == 'Total':
                    for choice in m.get('choices', []):
                        if choice.get('name') == 'Over 2.5':
                            data["Goles"] = float(choice.get('fractionalValue', 0))
            return data
        except: return None

    def generar_reporte(self, home, away, odds_data, h2h):
        odds = odds_data.get("1X2")
        goles_over = odds_data.get("Goles", "-")
        
        p_home, p_draw, p_away = 0, 0, 0
        if odds:
            # Cálculo de probabilidad real
            p1, pX, p2 = 1/odds['1'], 1/odds['X'], 1/odds['2']
            t = p1 + pX + p2
            p_home, p_draw, p_away = (p1/t)*100, (pX/t)*100, (p2/t)*100

        # DOBLE OPORTUNIDAD
        dc_1x = round(p_home + p_draw)
        dc_x2 = round(p_draw + p_away)

        return (
            f"🏟️ **ANÁLISIS PROFESIONAL**\n"
            f"⚽ {home} vs {away}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🛡️ **DOBLE OPORTUNIDAD:**\n"
            f"• 1X ({home} o E): `{dc_1x}%` ✅\n"
            f"• X2 ({away} o E): `{dc_x2}%` 🚀\n\n"
            f"🥅 **GOLES (Over 2.5):**\n"
            f"• Cuota: `{goles_over}`\n"
            f"• Tendencia: {'Alta 📈' if (isinstance(goles_over, float) and goles_over < 2.0) else 'Moderada 📉'}\n\n"
            f"📊 **PROBABILIDAD 1X2:**\n"
            f"🏠 `{round(p_home)}%` | ➖ `{round(p_draw)}%` | 🚀 `{round(p_away)}%` \n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚀 **¡SISTEMA ACTIVO!**\nUsa `/analisis [equipo]` para obtener datos de SofaScore.")

    async def analisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query:
            return await update.message.reply_text("❌ Escribe el nombre de un equipo.")
        
        msj = await update.message.reply_text(f"📡 Buscando mercados para: {query}...")
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=self.headers, timeout=10).json()
            events = [res for res in r.get('results', []) if res.get('type') == 'event']
            
            if not events:
                return await msj.edit_text(f"❌ No encontré partidos próximos para '{query}'.")
            
            m = events[0]['entity']
            m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
            
            odds_data = await self.get_real_odds(m_id)
            h2h = await self.get_h2h_data(m_id)
            
            texto = self.generar_reporte(home, away, odds_data, h2h)
            await msj.edit_text(texto, parse_mode='Markdown')
            
        except Exception as e:
            await msj.edit_text(f"⚠️ Error de conexión: Inténtalo de nuevo en unos segundos.")

if __name__ == '__main__':
    # 1. Arrancar Servidor Web (Para que Render no mate el proceso)
    Thread(target=run_flask).start()
    
    # 2. Configurar Bot
    bot = SportsAnalystV5()
    
    if not bot.token:
        print("❌ ERROR: No se encontró la variable TELEGRAM_TOKEN")
    else:
        print("🚀 INICIANDO POLLING DE TELEGRAM...")
        application = Application.builder().token(bot.token).build()
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("analisis", bot.analisis))
        
        # 3. Mantener el bot escuchando
        application.run_polling(drop_pending_updates=True)
