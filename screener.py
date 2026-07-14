import os
import io
import time
from datetime import datetime, timezone

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from analysis import analyze_daily, evaluate_entry_signal
from finnhub_client import build_catalyst_summary

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# ---------- Configuración (viene de variables de entorno / GitHub Secrets) ----------

TWELVE_DATA_KEY = os.environ["TWELVE_DATA_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

DEFAULT_TICKERS_USA = "TSLA,NVDA,AMD,PLTR,COIN,MARA,RIOT,MSTR,SOFI,SMCI,RIVN,LCID,SNAP,DKNG,CVNA,AI,F,NIO,PYPL,BABA"
DEFAULT_TICKERS_EUROPE = "SAN.MC,BBVA.MC,ITX.MC,IBE.MC,TEF.MC,SAP.DE,SIE.DE,MC.PA,OR.PA,TTE.PA,AIR.PA,ASML.AS"

REGION = os.environ.get("REGION", "usa")  # "usa" o "europe"
WATCHLIST_FILE = "watchlist_today.txt" if REGION == "usa" else "watchlist_today_europe.txt"
DEFAULT_TICKERS = DEFAULT_TICKERS_USA if REGION == "usa" else DEFAULT_TICKERS_EUROPE


def load_tickers():
    """Prioridad: watchlist generada por el Radar Diario > variable TICKERS > lista fija de la región."""
    try:
        with open(WATCHLIST_FILE) as f:
            content = f.read().strip()
            if content:
                tickers = [t.strip() for t in content.split(",") if t.strip()]
                if tickers:
                    print(f"Usando watchlist del Radar Diario ({REGION}): {tickers}")
                    return tickers
    except FileNotFoundError:
        pass
    print(f"Sin watchlist del Radar Diario ({REGION}), usando lista por defecto / TICKERS")
    return os.environ.get("TICKERS", DE
