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
from finnhub_client import build
