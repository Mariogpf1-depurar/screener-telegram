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

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "").strip()

# ---------- Configuración (viene de variables de entorno / GitHub Secrets) ----------

TWELVE_DATA_KEY = os.environ["TWELVE_DATA_KEY"].strip()
TELEGRAM_TOKEN = os.environ["TELEGRA
