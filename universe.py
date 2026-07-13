"""
Universo curado para el Radar Diario.

NOTA IMPORTANTE: esto NO es una réplica exacta y en vivo de la composición del
S&P 500 / Nasdaq 100 (eso requeriría una fuente de datos de constituyentes de
índice, normalmente de pago, y se descuadra con el tiempo por altas/bajas).
Es una selección amplia y líquida de ~150 acciones conocidas, repartida entre
los sectores que marca tu documento para mantener diversificación. Puedes
editar libremente estas listas.
"""

UNIVERSE = {
    "Tecnología": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "CRM", "ORCL", "ADBE", "NOW",
        "SHOP", "UBER", "ABNB", "SNOW", "NET", "DDOG", "CRWD", "PANW", "ZS",
    ],
    "IA": [
        "NVDA", "PLTR", "AI", "SOUN", "BBAI", "MSFT", "GOOGL", "META", "IONQ",
    ],
    "Semiconductores": [
        "AMD", "INTC", "TSM", "AVGO", "QCOM", "MU", "SMCI", "ARM", "TXN",
        "ASML", "LRCX", "KLAC", "MRVL",
    ],
    "Defensa": [
        "LMT", "RTX", "NOC", "GD", "LHX", "HII", "BAH", "KTOS",
    ],
    "Industria": [
        "CAT", "DE", "HON", "GE", "MMM", "UPS", "BA", "UNP",
    ],
    "Energía": [
        "XOM", "CVX", "COP", "SLB", "OXY", "EOG", "PXD",
    ],
    "Financieras": [
        "JPM", "BAC", "GS", "MS", "WFC", "SCHW", "V", "MA", "SOFI",
    ],
    "Salud": [
        "LLY", "UNH", "JNJ", "PFE", "ABBV", "MRK", "ISRG", "VRTX",
    ],
    "Infraestructuras": [
        "VMC", "MLM", "PWR", "NEE", "DUK",
    ],
    "Consumo / otros volátiles": [
        "TSLA", "RIVN", "LCID", "COIN", "MARA", "RIOT", "MSTR", "DKNG",
        "CVNA", "SNAP", "F", "NIO", "PYPL", "BABA",
    ],
}


def flat_universe():
    """Devuelve lista de (ticker, sector) sin duplicados (se queda con el primer sector visto)."""
    seen = {}
    for sector, tickers in UNIVERSE.items():
        for t in tickers:
            if t not in seen:
                seen[t] = sector
    return list(seen.items())
