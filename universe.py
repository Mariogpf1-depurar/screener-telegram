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


EUROPE_UNIVERSE = {
    "IBEX 35": [
        "SAN.MC", "BBVA.MC", "ITX.MC", "IBE.MC", "TEF.MC", "REP.MC", "FER.MC",
        "AENA.MC", "AMS.MC", "CLNX.MC", "NTGY.MC", "ELE.MC", "GRF.MC", "ACS.MC",
        "IAG.MC", "ANA.MC", "SAB.MC", "CABK.MC", "MAP.MC", "ENG.MC",
    ],
    "DAX (Alemania)": [
        "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "BAS.DE", "BMW.DE", "MBG.DE",
        "VOW3.DE", "MUV2.DE", "ADS.DE", "DBK.DE", "IFX.DE", "RWE.DE",
    ],
    "CAC 40 (Francia)": [
        "MC.PA", "OR.PA", "TTE.PA", "SAN.PA", "AIR.PA", "BNP.PA", "SU.PA",
        "AI.PA", "DG.PA", "CS.PA", "BN.PA", "KER.PA",
    ],
    "Otros Europa": [
        "NESN.SW", "NOVN.SW", "ROG.SW", "ASML.AS", "SHEL.L", "AZN.L", "ULVR.L",
    ],
}


def flat_universe(region="usa"):
    """region: 'usa' (por defecto) o 'europe'."""
    source = EUROPE_UNIVERSE if region == "europe" else UNIVERSE
    seen = {}
    for sector, tickers in source.items():
        for t in tickers:
            if t not in seen:
                seen[t] = sector
    return list(seen.items())
