"""
Cliente mínimo para Finnhub (plan gratuito: ~60 peticiones/minuto).

Dos cosas que pide tu documento en "Catalizadores":
- Noticias recientes de la empresa (resultados, contratos, guidance...).
- Cambios de analistas (subida/bajada de recomendaciones).

No cubre: precios objetivo exactos por analista individual, insiders, ni
rotación de capital — esos requieren fuentes más especializadas (de pago).
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "https://finnhub.io/api/v1"


def get_recent_news(symbol, api_key, days=5, timeout=10):
    """Devuelve el titular más reciente (texto corto, tal cual lo da la fuente) o None."""
    today = datetime.utcnow().date()
    frm = today - timedelta(days=days)
    url = f"{BASE_URL}/company-news"
    params = {"symbol": symbol, "from": frm.isoformat(), "to": today.isoformat(), "token": api_key}
    try:
        r = requests.get(url, params=params, timeout=timeout)
        items = r.json()
        if not isinstance(items, list) or not items:
            return None
        items.sort(key=lambda x: x.get("datetime", 0), reverse=True)
        top = items[0]
        return {
            "headline": top.get("headline", "")[:160],
            "source": top.get("source", ""),
            "url": top.get("url", ""),
        }
    except Exception:
        return None


def get_analyst_trend(symbol, api_key, timeout=10):
    """Compara el mes más reciente de recomendaciones con el anterior.
    Devuelve dict con conteos actuales y una señal simple de mejora/empeora."""
    url = f"{BASE_URL}/stock/recommendation"
    params = {"symbol": symbol, "token": api_key}
    try:
        r = requests.get(url, params=params, timeout=timeout)
        items = r.json()
        if not isinstance(items, list) or len(items) < 2:
            return None
        items.sort(key=lambda x: x.get("period", ""), reverse=True)
        latest, previous = items[0], items[1]

        def bullish_ratio(period):
            buy = (period.get("strongBuy", 0) or 0) + (period.get("buy", 0) or 0)
            total = buy + (period.get("hold", 0) or 0) + (period.get("sell", 0) or 0) + (period.get("strongSell", 0) or 0)
            return buy / total if total > 0 else None

        r_latest = bullish_ratio(latest)
        r_prev = bullish_ratio(previous)
        trend = None
        if r_latest is not None and r_prev is not None:
            if r_latest > r_prev + 0.05:
                trend = "mejorando"
            elif r_latest < r_prev - 0.05:
                trend = "empeorando"
            else:
                trend = "estable"

        return {
            "strong_buy": latest.get("strongBuy", 0),
            "buy": latest.get("buy", 0),
            "hold": latest.get("hold", 0),
            "sell": latest.get("sell", 0),
            "strong_sell": latest.get("strongSell", 0),
            "trend": trend,
        }
    except Exception:
        return None


def build_catalyst_summary(symbol, api_key):
    """Texto corto combinando noticia reciente + tendencia de analistas, listo para Telegram."""
    if not api_key:
        return "no disponible (sin FINNHUB_API_KEY configurada)"

    parts = []
    news = get_recent_news(symbol, api_key)
    if news:
        parts.append(f"📰 {news['headline']} ({news['source']})")
    else:
        parts.append("Sin noticias relevantes en los últimos días")

    trend = get_analyst_trend(symbol, api_key)
    if trend and trend["trend"]:
        emoji = {"mejorando": "📈", "empeorando": "📉", "estable": "➖"}.get(trend["trend"], "")
        parts.append(
            f"{emoji} Analistas: {trend['trend']} "
            f"(Buy {trend['strong_buy']+trend['buy']} / Hold {trend['hold']} / Sell {trend['sell']+trend['strong_sell']})"
        )

    return "\n".join(parts)
