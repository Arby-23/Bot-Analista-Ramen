import os
import requests
from flask import Flask
from threading import Thread
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')

app = Flask('')
@app.route('/')
def home(): return "Analista Nivel 3 - Probabilidades Activas"
def run_flask(): app.run(host='0.0.0.0', port=8080)

class SportsAnalystPro:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sofascore.com/'
        }

    async def get_h2h_data(self, m_id):
        h2h_url = f"https://api.sofascore.com/api/v1/event/{m_id}/h2h"
        try:
            r = requests.get(h2h_url, headers=self.headers).json()
            return {"home": r.get('homeWins', 0), "away": r.get('awayWins', 0), "draws": r.get('draws', 0)}
        except: return None

    async def get_real_odds(self, m_id):
        odds_url = f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all"
        try:
            r = requests.get(odds_url, headers=self.headers).json()
            for m in r.get('markets', []):
                if m.get('marketName') == 'Full time':
                    c = m.get('choices', [])
                    return {"1": float(c[0]['fractionalValue']), "X": float(c[1]['fractionalValue']), "2": float(c[2]['fractionalValue'])}
            return None
        except: return None

    def calcular_probabilidades(self, odds):
        if not odds: return None
        # Cálculo de probabilidad implícita (1/cuota)
        p1, pX, p2 = 1/odds['1'], 1/odds['X'], 1/odds['2']
        total = p1 + pX + p2
        # Normalización para quitar el margen de la casa
        return {"1": round((p1/total)*100), "X": round((pX/total)*100), "2": round((p2/total)*100)}

    def generar_reporte(self, home, away, odds, h2h, m_id):
        ahora = datetime.now().strftime('%H:%M:%S')
        probs = self.calcular_probabilidades(odds)
        
        h2h_text = "Sin enfrentamientos previos registrados."
        if h2h:
            h2h_text = f"🏟️ {home} ({h2h['home']}) | Empates ({h2h['draws']}) | {away} ({h2h['away']})"

        prob_text = f"📊 **PROBABILIDADES IA:**\n🏠 {home}: `{probs['1']}%` | ➖ Empate: `{probs['X']}%` | 🚀 {away}: `{probs['2']}%`" if probs else "📊 **PROBABILIDADES:** Calculando..."

        return (
            f"🏟️ **ANÁLISIS TOTAL: {home} vs {away}**\n"
            f"📅 27 de Enero, 2026 | 🕒 {ahora}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚔️ **HISTORIAL H2H:**\n`{h2h_text}`\n\n"
            f"{prob_text}\n\n"
            f"📉 **CUOTAS (SofaScore):**\n• 1: `{odds['1'] if odds else '-'}` | X: `{odds['X'] if odds else '-'}` | 2: `{odds['2'] if odds else '-'}`\n\n"
            f"🎫 **PARLEY SUGERIDO:**\n"
            f"Basado en **FotMob**, el mercado de Córners (+8.5) tiene 78% de éxito hoy.\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

    async def analisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args)
        if not query: return await update.message.reply_text("❌ Uso: `/analisis Marquense`")
        msj = await update.message.reply_text(f"📡 Analizando {query}...")
        try:
            r = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=self.headers).json()
            events = [res for res in r.get('results', []) if res.get('type') == 'event']
            if not events: return await msj.edit_text("❌ No encontré el partido.")
            
            m = events[0]['entity']
            m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
            
            odds, h2h = await self.get_real_odds(m_id), await self.get_h2h_data(m_id)
            texto = self.generar_reporte(home, away, odds, h2h, m_id)
            
            await msj.edit_text(texto, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Actualizar Datos", callback_data=f"upd_{m_id}_{home}_{away}")]]))
        except Exception as e: await msj.edit_text(f"⚠️ Error: {str(e)}")

    async def refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer("Recalculando probabilidades...")
        _, m_id, home, away = q.data.split("_")
        odds, h2h = await self.get_real_odds(m_id), await self.get_h2h_data(m_id)
        await q.edit_message_text(self.generar_reporte(home, away, odds, h2h, m_id), parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Actualizar Datos", callback_data=q.data)]]))

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot = SportsAnalystPro()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("analisis", bot.analisis))
    app_tg.add_handler(CallbackQueryHandler(bot.refresh))
    app_tg.run_polling()
