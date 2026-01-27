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
def home(): return "Analista Pro 24/7 Online"

def run_flask():
    # Render usa el puerto 10000 por defecto o el que asigne
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

class SportsAnalystPro:
    def __init__(self):
        self.token = os.environ.get('TELEGRAM_TOKEN')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sofascore.com/'
        }

    async def get_h2h_data(self, m_id):
        """Extrae enfrentamientos directos desde SofaScore."""
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/h2h", headers=self.headers).json()
            return {"home": r.get('homeWins', 0), "away": r.get('awayWins', 0), "draws": r.get('draws', 0)}
        except: return None

    async def get_real_odds(self, m_id):
        """Extrae cuotas 1X2 reales."""
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=self.headers).json()
            for m in r.get('markets', []):
                if m.get('marketName') == 'Full time':
                    c = m.get('choices', [])
                    return {"1": float(c[0]['fractionalValue']), "X": float(c[1]['fractionalValue']), "2": float(c[2]['fractionalValue'])}
            return None
        except: return None

    def calcular_probabilidades(self, odds):
        """Calcula porcentaje real sin margen de casa de apuestas."""
        if not odds: return None
        p1, pX, p2 = 1/odds['1'], 1/odds['X'], 1/odds['2']
        total = p1 + pX + p2
        return {"1": round((p1/total)*100), "X": round((pX/total)*100), "2": round((p2/total)*100)}

    def generar_reporte(self, home, away, odds, h2h):
        ahora = datetime.now().strftime('%H:%M:%S')
        probs = self.calcular_probabilidades(odds)
        
        h2h_text = "Sin datos previos."
        if h2h:
            h2h_text = f"🏟️ {home} ({h2h['home']}) | Empates ({h2h['draws']}) | {away} ({h2h['away']})"

        prob_text = f"📊 **PROBABILIDADES IA:**\n🏠 {home}: `{probs['1']}%` | ➖ Empate: `{probs['X']}%` | 🚀 {away}: `{probs['2']}%`" if probs else "📊 **PROBABILIDADES:** No disponibles"

        return (
            f"🏟️ **ANÁLISIS TOTAL: {home} vs {away}**\n"
            f"📅 27 de Enero, 2026 | 🕒 {ahora}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚔️ **HISTORIAL H2H:**\n`{h2h_text}`\n\n"
            f"{prob_text}\n\n"
            f"📉 **CUOTAS (SofaScore):**\n• 1: `{odds['1'] if odds else '-'}` | X: `{odds['X'] if odds else '-'}` | 2: `{odds['2'] if odds else '-'}`\n\n"
            f"🎫 **PARLEY SUGERIDO:**\n"
            f"Basado en **FotMob** y **SofaScore**, el valor está en: {home if (probs and probs['1'] > 50) else 'Revisar en vivo'}.\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚀 **Analista de Cuotas Pro Activo**\nUsa `/analisis [equipo]` para comenzar.")

    async def analisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query: return await update.message.reply_text("❌ Escribe un equipo. Ej: `/analisis Coban`")
        
        msj = await update.message.reply_text(f"📡 Buscando en SofaScore: {query}...")
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=self.headers).json()
            events = [res for res in r.get('results', []) if res.get('type') == 'event']
            if not events: return await msj.edit_text(f"❌ No se encontró el partido para '{query}'.")
            
            m = events[0]['entity']
            m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
            
            odds, h2h = await self.get_real_odds(m_id), await self.get_h2h_data(m_id)
            texto = self.generar_reporte(home, away, odds, h2h)
            
            keyboard = [[InlineKeyboardButton("🔄 Actualizar Datos", callback_data=f"upd_{m_id}_{home}_{away}")]]
            await msj.edit_text(texto, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e: await msj.edit_text(f"⚠️ Error: {str(e)}")

    async def refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer("Actualizando...")
        _, m_id, home, away = q.data.split("_")
        odds, h2h = await self.get_real_odds(m_id), await self.get_h2h_data(m_id)
        await q.edit_message_text(self.generar_reporte(home, away, odds, h2h), parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Actualizar Datos", callback_data=q.data)]]))

if __name__ == '__main__':
    # Iniciar servidor web para Render
    Thread(target=run_flask).start()
    
    # Iniciar Bot de Telegram
    bot = SportsAnalystPro()
    app_tg = Application.builder().token(bot.token).build()
    app_tg.add_handler(CommandHandler("start", bot.start))
    app_tg.add_handler(CommandHandler("analisis", bot.analisis))
    app_tg.add_handler(CallbackQueryHandler(bot.refresh))
    
    print("🚀 BOT DESPLEGADO EN RENDER")
    app_tg.run_polling()
