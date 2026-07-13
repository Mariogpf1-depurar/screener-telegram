import os
import io
import time
from datetime import datetime, timezone

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analysis import analyze_daily
from finnhub_client import build_catalyst_summary

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# ---------- Configuración (viene de variables de entorno / GitHub Secrets) ----------

TWELVE_DATA_KEY = os.environ["TWELVE_DATA_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TICKERS = os.environ.get(
    "TICKERS",
    "TSLA,NVDA,AMD,PLTR,COIN,MARA,RIOT,MSTR,SOFI,SMCI,RIVN,LCID,SNAP,DKNG,CVNA,AI,F,NIO,PYPL,BABA"
).split(",")

MIN_CHANGE = float(os.environ.get("MIN_CHANGE", 2))       # % cambio mínimo hoy (abs)
MIN_REL_VOL = float(os.environ.get("MIN_REL_VOL", 1.5))   # volumen relativo mínimo
MIN_RANGE = float(os.environ.get("MIN_RANGE", 3))         # rango del día mínimo (%)
MAX_ERRATIC = float(os.environ.get("MAX_ERRATIC", 3))     # rango/cambio máximo permitido
MAX_CANDIDATES = int(os.environ.get("MAX_CANDIDATES", 5)) # cuántas mandar por escaneo

TIMEFRAMES = [("1min", 60), ("5min", 60), ("15min", 60), ("1h", 48)]

BATCH_SIZE = 6           # símbolos por petición de quote
BATCH_DELAY_SECONDS = 8  # respeta el límite ~8 peticiones/min del plan gratuito


# ---------- Twelve Data ----------

def fetch_quotes_batch(symbols):
    url = f"https://api.twelvedata.com/quote?symbol={','.join(symbols)}&apikey={TWELVE_DATA_KEY}"
    r = requests.get(url, timeout=15)
    data = r.json()
    if len(symbols) == 1:
        return {symbols[0]: data}
    return data


def fetch_time_series(symbol, interval, outputsize):
    url = (f"https://api.twelvedata.com/time_series?symbol={symbol}"
           f"&interval={interval}&outputsize={outputsize}&apikey={TWELVE_DATA_KEY}")
    r = requests.get(url, timeout=15)
    data = r.json()
    if data.get("status") == "error" or "values" not in data:
        return None
    values = list(reversed(data["values"]))
    return [
        {"t": v["datetime"], "o": float(v["open"]), "h": float(v["high"]),
         "l": float(v["low"]), "c": float(v["close"])}
        for v in values
    ]


# ---------- Filtro ----------

def is_market_hours():
    """Comprobación aproximada del horario NYSE (13:30-20:00 UTC, ignora ajustes DST puntuales)."""
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return 13 * 60 + 30 <= minutes <= 20 * 60


def scan():
    all_quotes = {}
    for i in range(0, len(TICKERS), BATCH_SIZE):
        batch = TICKERS[i:i + BATCH_SIZE]
        all_quotes.update(fetch_quotes_batch(batch))
        if i + BATCH_SIZE < len(TICKERS):
            time.sleep(BATCH_DELAY_SECONDS)

    candidates = []
    for t in TICKERS:
        q = all_quotes.get(t)
        if not q or q.get("status") == "error" or "close" not in q:
            continue
        try:
            close = float(q["close"])
            high = float(q["high"])
            low = float(q["low"])
            pct_change = float(q["percent_change"])
            volume = float(q.get("volume") or 0)
            avg_volume = float(q.get("average_volume") or 0)
        except (TypeError, ValueError):
            continue

        rel_vol = volume / avg_volume if avg_volume > 0 else 0
        range_pct = (high - low) / close * 100 if close > 0 else 0
        erratic = range_pct / abs(pct_change) if abs(pct_change) > 0.01 else 999

        if (abs(pct_change) >= MIN_CHANGE and rel_vol >= MIN_REL_VOL
                and range_pct >= MIN_RANGE and erratic <= MAX_ERRATIC):
            candidates.append({
                "ticker": t, "close": close, "pct_change": pct_change,
                "rel_vol": rel_vol, "range_pct": range_pct, "erratic": erratic,
            })

    candidates.sort(key=lambda c: abs(c["pct_change"]), reverse=True)
    return candidates[:MAX_CANDIDATES]


# ---------- Gráficas ----------

def draw_chart(candles, title):
    fig, ax = plt.subplots(figsize=(6, 2.6), dpi=140)
    for i, c in enumerate(candles):
        color = "#3ecf8e" if c["c"] >= c["o"] else "#e8654f"
        ax.plot([i, i], [c["l"], c["h"]], color=color, linewidth=0.8)
        ax.add_patch(plt.Rectangle(
            (i - 0.3, min(c["o"], c["c"])), 0.6,
            max(abs(c["c"] - c["o"]), 0.001), color=color
        ))
    ax.set_title(title, fontsize=9, loc="left", color="#333333")
    ax.set_xticks([])
    ax.set_facecolor("#f7f7f5")
    fig.patch.set_facecolor("white")
    ax.margins(x=0.02)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------- Telegram ----------

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=15)


def send_telegram_photo(photo_buf, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(
        url,
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
        files={"photo": ("chart.png", photo_buf, "image/png")},
        timeout=30,
    )


# ---------- Main ----------

def main():
    if not is_market_hours():
        print("Fuera de horario de mercado, no se escanea.")
        return

    candidates = scan()
    if not candidates:
        print("Sin candidatas en este escaneo.")
        return

    send_telegram_message(f"📊 <b>Screener intradía</b> — {len(candidates)} candidata(s) encontradas")

    for c in candidates:
        flag = "⚠️ mecha alta / poco limpio" if c["erratic"] > 4 else "✅ tendencia relativamente limpia"

        # Análisis RMS/LMC sobre datos diarios (para estrellas, entrada/stop/objetivo, RR, leverage)
        analysis_txt = ""
        try:
            daily_candles = fetch_time_series(c["ticker"], "1day", 260)
            if daily_candles and len(daily_candles) >= 60:
                a = analyze_daily(daily_candles)
                if a:
                    stars_txt = "★" * a["stars"] + "☆" * (5 - a["stars"])
                    analysis_txt = (
                        f"\n{stars_txt}  ({a['conviction']})\n"
                        f"RMS: {a['rms_score']}/8  ·  LMC: {a['lmc_score']}/4\n"
                        f"Entrada: ${a['entry']:.2f}  |  Stop: ${a['stop']:.2f}  |  "
                        f"Objetivo: ${a['target']:.2f}  |  RR: {a['rr']:.2f}\n"
                        f"{a['leverage_note']}\n"
                        f"Catalizador: {build_catalyst_summary(c['ticker'], FINNHUB_API_KEY)}"
                    )
        except Exception:
            analysis_txt = "\n(No se pudo completar el análisis RMS/LMC para este ticker)"

        caption = (
            f"<b>{c['ticker']}</b>  ${c['close']:.2f}\n"
            f"Cambio hoy: {c['pct_change']:+.2f}%  |  Vol. relativo: {c['rel_vol']:.2f}x  |  "
            f"Rango día: {c['range_pct']:.2f}%\n"
            f"{flag}"
            f"{analysis_txt}\n"
            f"Recuerda: esto es solo información de apoyo, no una recomendación de entrada."
        )
        send_telegram_message(caption)

        for interval, size in TIMEFRAMES:
            candles = fetch_time_series(c["ticker"], interval, size)
            if not candles:
                continue
            buf = draw_chart(candles, f"{c['ticker']} · {interval}")
            send_telegram_photo(buf, f"{c['ticker']} — {interval}")
            time.sleep(1.5)


if __name__ == "__main__":
    main()
