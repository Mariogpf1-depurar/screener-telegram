"""Indicadores técnicos calculados a partir de listas de velas [{'o','h','l','c','v','t'}, ...]
en orden cronológico (la última es la más reciente).
"""

def ema_series(values, period):
    if len(values) < period:
        return [None] * len(values)
    k = 2 / (period + 1)
    out = [None] * (period - 1)
    sma = sum(values[:period]) / period
    out.append(sma)
    prev = sma
    for v in values[period:]:
        prev = v * k + prev * (1 - k)
        out.append(prev)
    return out


def ema_last(values, period):
    s = ema_series(values, period)
    return s[-1] if s else None


def rsi_series(closes, period=14):
    if len(closes) < period + 1:
        return [None] * len(closes)
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    out = [None] * period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
    out.append(100 - (100 / (1 + rs)))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss > 0 else float("inf")
        out.append(100 - (100 / (1 + rs)))
    return out


def macd_series(closes, fast=12, slow=26, signal=9):
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    macd_line = [
        (f - s) if (f is not None and s is not None) else None
        for f, s in zip(ema_fast, ema_slow)
    ]
    valid = [m for m in macd_line if m is not None]
    signal_valid = ema_series(valid, signal) if len(valid) >= signal else [None] * len(valid)
    signal_line = [None] * (len(macd_line) - len(signal_valid)) + signal_valid
    hist = [
        (m - s) if (m is not None and s is not None) else None
        for m, s in zip(macd_line, signal_line)
    ]
    return macd_line, signal_line, hist


def atr_last(candles, period=14):
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l, prev_c = candles[i]["h"], candles[i]["l"], candles[i - 1]["c"]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    return sum(trs[-period:]) / period


def session_vwap(intraday_candles):
    """VWAP de la sesión actual a partir de velas intradía con volumen."""
    cum_pv, cum_v = 0.0, 0.0
    for c in intraday_candles:
        typical = (c["h"] + c["l"] + c["c"]) / 3
        vol = c.get("v", 0) or 0
        cum_pv += typical * vol
        cum_v += vol
    return cum_pv / cum_v if cum_v > 0 else None
