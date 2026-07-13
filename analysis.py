"""
Implementa, de forma heurística y simplificada, las reglas de
PROYECTO INVERSIONES 2026 sobre los setups RMS y LMC.

IMPORTANTE — honestidad sobre lo que esto es y no es:
- Esto NO es una probabilidad estadística validada con backtesting histórico.
  Es un score de confluencia técnica (cuántas condiciones de tu propio sistema
  se cumplen), traducido a un rating de estrellas.
- La detección de patrones de varios días (consolidación, pullback,
  continuación) es una aproximación simplificada, no un reconocimiento visual
  de patrones como haría un trader experimentado.
- Las sugerencias de apalancamiento reflejan literalmente las reglas que TÚ
  escribiste en tu documento (alta convicción → x10, media → x5, etc.), no
  son una recomendación nueva generada por el sistema.
"""

from indicators import ema_series, rsi_series, macd_series, atr_last


def analyze_daily(candles):
    """candles: velas diarias en orden cronológico (>= ~210 para EMA200 fiable)."""
    closes = [c["c"] for c in candles]
    highs = [c["h"] for c in candles]
    lows = [c["l"] for c in candles]
    volumes = [c.get("v", 0) or 0 for c in candles]

    if len(closes) < 60:
        return None  # datos insuficientes para un análisis fiable

    ema9 = ema_series(closes, 9)
    ema20 = ema_series(closes, 20)
    ema50 = ema_series(closes, 50)
    ema200 = ema_series(closes, 200) if len(closes) >= 200 else [None] * len(closes)
    rsi = rsi_series(closes, 14)
    macd_line, signal_line, hist = macd_series(closes)
    atr = atr_last(candles, 14)

    close = closes[-1]
    avg_vol_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None
    vol_today = volumes[-1]
    rel_vol = (vol_today / avg_vol_20) if avg_vol_20 else None

    recent_high_60 = max(highs[-60:])
    drawdown_pct = (recent_high_60 - close) / recent_high_60 * 100

    uptrend = (
        ema50[-1] is not None and ema200[-1] is not None
        and ema50[-1] > ema200[-1]
        and ema50[-1] > (ema50[-6] or ema50[-1])  # EMA50 subiendo últimas ~5 sesiones
    )

    rsi_recovering = (
        rsi[-1] is not None and rsi[-2] is not None
        and 40 <= rsi[-1] <= 55 and rsi[-1] > rsi[-2]
    )
    macd_improving = (
        hist[-1] is not None and hist[-2] is not None and hist[-1] > hist[-2]
    )
    above_ema9 = ema9[-1] is not None and close > ema9[-1]
    above_ema20 = ema20[-1] is not None and close > ema20[-1]
    volume_growing = rel_vol is not None and rel_vol > 1.0 and vol_today > volumes[-2]
    higher_highs_lows = closes[-1] > closes[-4] and lows[-1] > lows[-4]
    correction_in_range = 5 <= drawdown_pct <= 15

    rms_conditions = {
        "corrección 5-15%": correction_in_range,
        "tendencia alcista (EMA50>EMA200)": uptrend,
        "RSI recuperando 40-55": rsi_recovering,
        "MACD mejorando": macd_improving,
        "recuperando EMA9": above_ema9,
        "recuperando EMA20": above_ema20,
        "volumen creciente": volume_growing,
        "máximos/mínimos crecientes": higher_highs_lows,
    }
    rms_score = sum(1 for v in rms_conditions.values() if v)

    # --- LMC simplificado ---
    move_20d = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) > 21 else 0
    strong_move = move_20d > 15
    high_volume = rel_vol is not None and rel_vol > 2.0
    last5_range = (max(highs[-5:]) - min(lows[-5:])) / close * 100
    clean_consolidation = last5_range < 8
    breakout_confirmed = closes[-1] >= max(highs[-6:-1]) if len(highs) > 6 else False

    lmc_conditions = {
        "movimiento fuerte reciente (>15% 20d)": strong_move,
        "volumen > 2x medio": high_volume,
        "consolidación limpia (rango 5d <8%)": clean_consolidation,
        "ruptura confirmada": breakout_confirmed,
    }
    lmc_score = sum(1 for v in lmc_conditions.values() if v)

    total_score = rms_score + lmc_score  # sobre 12 puntos posibles
    stars = star_rating(total_score)

    # Entrada / stop / objetivo / RR
    entry = close
    structural_stop = min(min(lows[-5:]), (ema20[-1] * 0.98) if ema20[-1] else close * 0.95)
    risk = entry - structural_stop
    target = entry + max(risk * 2, entry * 0.02)  # RR mínimo 1:2, objetivo mínimo +2%
    rr = (target - entry) / risk if risk > 0 else None

    conviction, leverage_note = leverage_suggestion(stars, rms_score, lmc_score, high_volume)

    return {
        "close": close,
        "rsi": rsi[-1],
        "rel_vol": rel_vol,
        "atr": atr,
        "drawdown_pct": drawdown_pct,
        "rms_score": rms_score,
        "rms_conditions": rms_conditions,
        "lmc_score": lmc_score,
        "lmc_conditions": lmc_conditions,
        "stars": stars,
        "entry": entry,
        "stop": structural_stop,
        "target": target,
        "rr": rr,
        "conviction": conviction,
        "leverage_note": leverage_note,
    }


def star_rating(total_score, max_score=12):
    pct = total_score / max_score
    if pct >= 0.75:
        return 5
    if pct >= 0.58:
        return 4
    if pct >= 0.42:
        return 3
    if pct >= 0.25:
        return 2
    return 1


def leverage_suggestion(stars, rms_score, lmc_score, high_volume):
    """Traduce tus propias reglas de apalancamiento del documento a texto informativo."""
    if stars >= 5 and high_volume and (rms_score >= 6 or lmc_score >= 3):
        return "Alta (excepcional)", "Multi x12-x15 (según tu regla: excepcional, solo si coinciden catalizador+volumen+RMS/LMC)"
    if stars >= 4:
        return "Alta", "Multi x10 (según tu regla: alta convicción)"
    if stars == 3:
        return "Media", "Multi x5 (según tu regla: convicción media)"
    if stars == 2:
        return "Baja / especulativa", "Multi x3 (según tu regla: convicción baja)"
    return "Descartar", "No operar (según tu regla: descartar)"
