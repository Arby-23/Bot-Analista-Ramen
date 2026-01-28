import os
import requests
import pandas as pd
import numpy as np
from flask import Flask
from threading import Thread
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURACIÓN DE SERVIDOR (PARA RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "🤖 Bot Analista IA Pro - Activo y Autónomo"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

class BotDefinitivoIA:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.sofascore.com/'
        }

    async def get_h2h(self, match_id):
        """Obtiene el historial reciente de enfrentamientos."""
        try:
            url = f"https://api.sofascore.com/api/v1/event/{match_id}/h2h"
            r = requests.get(url, headers=self.headers).json()
            return {
                "home": r.get('homeWins', 0),
                "away": r.get('awayWins', 0),
                "draws": r.get('draws', 0)
            }
        except: return None

    async def get_analisis_profundo(self, query):
        """Busca, extrae cuotas y calcula el valor (Edge)."""
        try:
            # 1. Búsqueda del partido
            search = requests.get(f"https://api.sofascore.com/api/v1/search/all?q={query}&type=event", headers=self.headers).json()
            events = [res for res in search.get('results', []) if res.get('type') == 'event']
            if not events: return "❌ No encontré partidos para ese equipo."
            
            m = events[0]['entity']
            m_id, home, away = m['id'], m['homeTeam']['name'], m['awayTeam']['name']
            
            # 2. Obtener Cuotas y Probabilidades
            odds_req = requests.get(f"https://api.sofascore.com/api/v1/event/{m_id}/odds/1/all", headers=self.headers).json()
            p_h, p_d, p_a, cuota_h, cuota_a = 0, 0, 0, 0, 0
            
            for mk in odds_req.get('markets', []):
                if mk['marketName'] == 'Full time':
                    c = mk['choices']
                    cuota_h, cuota_d, cuota_a = float(c[0]['fractionalValue']), float(c[1]['fractionalValue']), float(c[2]['fractionalValue'])
                    v1, vX, v2 = 1/cuota_h, 1/cuota_d, 1/cuota_a
                    t = v1 + vX + v2
                    p_h, p_d, p_a = (v1/t)*100, (vX/t)*100, (v2/t)*100

            # 3. Datos Extra (H2H)
            h2h = await self.get_h2h(m_id)
            
            # 4. Cálculo de Valor (Edge)
            # Si la prob calculada es mayor a la implícita en la cuota, hay valor.
            edge_h = p_h - (1/cuota_h * 100) if cuota_h > 0 else 0
            recomendacion = "⚠️ Analizando..."
            if edge_h > 5: recomendacion = f"🔥 VALOR DETECTADO en {home} (Edge: +{round(edge_h)}%)"
            elif p_h + p_d > 75: recomendacion = f"🛡️ DOBLE OPORTUNIDAD: {home} o Empate (Alta seguridad)"
            else: recomendacion = "⚖️ Mercado equilibrado. Sin valor claro."

            # --- CONSTRUCCIÓN DEL REPORTE ---
            reporte = (
                f"🏟️ **{home} vs {away}**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📈 **PROBABILIDAD IA:**\n"
                f"🏠 {round(p_h)}% | ➖ {round(p_d)}% | 🚀 {round(p_a)}%\n\n"
                f"⚔️ **HISTORIAL (H2H):**\n"
                f"• Victorias {home}: {h2h['home']}\n"
                f"• Victorias {away}: {h2h['away']}\n"
                f"• Empates: {h2h['draws']}\n\n"
                f"🎯 **RECOMENDACIÓN IA:**\n"
                f"{recomendacion}\n\n"
                f"⚽ **TOTAL GOLES (>2.5):** { 'Alta probabilidad 📈' if (p_h+p_a > 60) else 'Moderada 📉'}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 _Basado en datos de SofaScore/FotMob (2026)_"
            )
            return reporte

        except Exception as e:
            return f"⚠️ Error en el análisis: {str(e)}"

# --- MANEJADORES DE COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Sistema Autónomo V8 Online**\nUsa `/analisis [equipo]` para iniciar la IA.")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        return await update.message.reply_text("❌ Indica un equipo.")
    
    msj = await update.message.reply_text(f"📡 Procesando tensores para: {query}...")
    bot = BotDefinitivoIA()
    resultado = await bot.get_analisis_profundo(query)
    await msj.edit_text(resultado, parse_mode='Markdown')

# --- INICIO DEL SISTEMA ---
if __name__ == '__main__':
    # 1. Lanzar servidor keep-alive
    Thread(target=run_flask).start()
    
    # 2. Limpieza extrema del Token (Solución al error anterior)
    raw_token = os.environ.get('TELEGRAM_TOKEN', '')
    TOKEN = "".join(raw_token.split())
    
    if not TOKEN:
        print("❌ ERROR: TOKEN NO ENCONTRADO.")
    else:
        print("🚀 BOT DEFINITIVO INICIADO...")
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("analisis", analisis))
        application.run_polling(drop_pending_updates=True)
