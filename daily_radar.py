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

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

TWELVE_DATA_KEY = os.environ["TWELVE_DATA_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

MAX_RESULTS = int(os.environ.get("RADAR_MAX_RESULTS", 10))
MIN_STARS = int(os.environ.get("RADAR_MIN_STARS", 3))
REQUEST_DELAY = float(os.environ.get("RADAR_REQUEST_DELAY", 7.5))  # respeta ~8 req/min


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
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)


def main():
    universe = flat_universe()
    results = []

    for i, (ticker, sector) in enumerate(universe):
        try:
            candles = fetch_daily_series(ticker)
            if candles:
                a = analyze_daily(candles)
                if a and a["stars"] >= MIN_STARS:
                    a["ticker"] = ticker
                    a["sector"] = sector
                    results.append(a)
        except Exception as e:
            print(f"Error con {ticker}: {e}")
        time.sleep(REQUEST_DELAY)

    results.sort(key=lambda r: (r["stars"], r["rms_score"] + r["lmc_score"]), reverse=True)
    top = results[:MAX_RESULTS]

    if not top:
        send_telegram_message("🌅 <b>Radar Diario</b>\nNinguna oportunidad por encima del mínimo de estrellas hoy.")
        return

    header = f"🌅 <b>Radar Diario</b> — {len(top)} oportunidad(es) (de {len(universe)} analizadas)\n"
    send_telegram_message(header)

    for r in top:
        stars_txt = "★" * r["stars"] + "☆" * (5 - r["stars"])
        msg = (
            f"<b>{r['ticker']}</b> · {r['sector']}\n"
            f"{stars_txt}  ({r['conviction']})\n"
            f"Precio: ${r['close']:.2f}  |  RSI: {r['rsi']:.0f}  |  Vol rel: "
            f"{(r['rel_vol'] or 0):.2f}x\n"
            f"RMS: {r['rms_score']}/8  ·  LMC: {r['lmc_score']}/4  ·  "
            f"Corrección desde máximo: {r['drawdown_pct']:.1f}%\n"
            f"Entrada: ${r['entry']:.2f}  |  Stop: ${r['stop']:.2f}  |  "
            f"Objetivo: ${r['target']:.2f}  |  RR: {r['rr']:.2f}\n"
            f"{r['leverage_note']}\n"
            f"Catalizador: {build_catalyst_summary(r['ticker'], FINNHUB_API_KEY)}"
        )
        send_telegram_message(msg)
        time.sleep(1)


if __name__ == "__main__":
    main()
