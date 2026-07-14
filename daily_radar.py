"""
Radar Diario — versión automatizada del "RADAR DIARIO" de tu documento.

Se ejecuta una vez al día (antes de apertura). Recorre el universo definido
en universe.py, calcula el análisis RMS/LMC + estrellas para cada ticker
usando solo velas diarias (1 petición por ticker), y manda por Telegram
el ranking de mejores oportunidades.

No cubre todavía: futuros, noticias, rotación sectorial de dinero, ni
comparativa Acción vs Multi vs Turbo con precios reales de derivados
(estos requieren fuentes de datos adicionales, p.ej. Finnhub para noticias).
"""

import os
import time

import requests

from analysis import analyze_daily
from universe import flat_universe
from finnhub_client import build_catalyst_summary

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "").strip()

TWELVE_DATA_KEY = os.environ["TWELVE_DATA_KEY"].strip()
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()

MAX_RESULTS = int(os.environ.get("RADAR_MAX_RESULTS", 10))
MIN_STARS = int(os.environ.get("RADAR_MIN_STARS", 1))
REQUEST_DELAY = float(os.environ.get("RADAR_REQUEST_DELAY", 7.5))  # respeta ~8 req/min
REGION = os.environ.get("REGION", "usa")  # "usa" o "europe"
WATCHLIST_FILE = "watchlist_today.txt" if REGION == "usa" else "watchlist_today_europe.txt"
REGION_LABEL = "🇺🇸 EEUU" if REGION == "usa" else "🇪🇺 Europa"


def fetch_daily_series(symbol, outputsize=260):
    url = (f"https://api.twelvedata.com/time_series?symbol={symbol}"
           f"&interval=1day&outputsize={outputsize}&apikey={TWELVE_DATA_KEY}")
    r = requests.get(url, timeout=15)
    data = r.json()
    if data.get("status") == "error" or "values" not in data:
        return None
    values = list(reversed(data["values"]))
    return [
        {"t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]),
         "l": float(v["low"]), "c": float(v["close"]), "v": float(v.get("volume") or 0)}
        for v in values
    ]


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=15)
        if not r.ok:
            print(f"Error enviando a Telegram ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"Excepción enviando a Telegram: {e}")


def select_priority_tickers(results, max_count=5):
    """
    De entre las candidatas del día, selecciona las que destacan de verdad
    para que el Screener Intradía las vigile cada 15 min, según:
    - Volumen relativo >= 1.0x (confirmación real de que entra dinero)
    -
