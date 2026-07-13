# Screener Intradía → Telegram

Escanea una lista de acciones cada ~15 min en horario de mercado, aplica un filtro
técnico, y te manda por Telegram las candidatas con su análisis y gráficas de
1min / 5min / 15min / 1h. No ejecuta ninguna orden — tú decides y operas manualmente
en tu bróker.

## 1. Crear el bot de Telegram

1. Abre Telegram y busca **@BotFather**.
2. Envíale `/newbot`, ponle un nombre y un usuario (debe acabar en `bot`).
3. Te dará un **token** tipo `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Guárdalo.
4. Escríbele cualquier mensaje a tu bot recién creado (para que pueda hablarte).
5. Visita en el navegador:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   y busca el campo `"chat":{"id": ...}` — ese número es tu **chat_id**.

## 2. Crear la API key de Twelve Data

1. Regístrate gratis en https://twelvedata.com
2. Copia tu API key del panel (plan gratuito: ~8 peticiones/min, 800/día).

## 2b. Crear la API key de Finnhub (catalizadores/noticias/analistas)

1. Regístrate gratis en https://finnhub.io/register
2. En el dashboard, copia tu API key (plan gratuito: ~60 peticiones/min).
3. Esto activa el campo "Catalizador" en los mensajes: última noticia relevante de la
   empresa y si la tendencia de recomendaciones de analistas mejora o empeora.
4. Si no quieres darte de alta todavía, simplemente no añadas el secret
   `FINNHUB_API_KEY` — el sistema sigue funcionando, solo que ese campo dirá
   "no disponible".

## 3. Subir este proyecto a GitHub

1. Crea un repositorio nuevo en GitHub (puede ser público — el código no contiene
   tus claves, solo referencias a "secrets").
2. Sube estos archivos (`screener.py`, `requirements.txt`, `.github/workflows/scan.yml`).

## 4. Configurar los Secrets

En el repo: **Settings → Secrets and variables → Actions → New repository secret**.
Añade estos tres:

| Nombre | Valor |
|---|---|
| `TWELVE_DATA_KEY` | tu API key de Twelve Data |
| `TELEGRAM_BOT_TOKEN` | el token de BotFather |
| `TELEGRAM_CHAT_ID` | tu chat_id |
| `FINNHUB_API_KEY` | (opcional) tu API key de Finnhub, para el campo Catalizador |

## 5. Activar y probar

1. Ve a la pestaña **Actions** del repo, acepta activar workflows si lo pide.
2. Entra en "Screener Intradía" → **Run workflow** para probarlo manualmente ya mismo
   (no hace falta esperar al cron).
3. Si todo está bien configurado, te llegará un mensaje a Telegram en 1-2 minutos.

## Personalizar

Puedes ajustar estas variables de entorno en el workflow (`scan.yml`, bajo `env:`)
o dejarlas por defecto:

- `TICKERS` — lista de tickers separados por comas
- `MIN_CHANGE` — % cambio mínimo hoy (default 2)
- `MIN_REL_VOL` — volumen relativo mínimo (default 1.5)
- `MIN_RANGE` — rango del día mínimo % (default 3)
- `MAX_ERRATIC` — máx. ratio rango/cambio, para evitar velas muy "mechudas" (default 3)
- `MAX_CANDIDATES` — cuántas candidatas mandar por escaneo (default 5)

## Los dos sistemas

- **`screener.py`** (cada 15 min, horario de mercado): tu lista curada de tickers volátiles,
  con % cambio, volumen relativo, y ahora también análisis RMS/LMC diario, estrellas,
  entrada/stop/objetivo/RR y sugerencia de apalancamiento según tus propias reglas.
- **`daily_radar.py`** (una vez cada mañana, ~8:15 ET): recorre el universo amplio de
  `universe.py` (~150 tickers repartidos por sector) y manda el ranking de las mejores
  oportunidades del día por estrellas.

## Sobre las "estrellas" y el análisis RMS/LMC

Esto **no es una probabilidad estadística validada** (no hay backtesting detrás). Es un
score de confluencia técnica: cuenta cuántas condiciones de tu propio sistema (RSI
recuperando, MACD mejorando, EMAs, volumen, estructura...) se cumplen hoy, y lo traduce a
estrellas. Trátalo como una preselección para revisar tú, no como una garantía.

## Limitaciones a tener en cuenta

- **GitHub Actions no garantiza el minuto exacto**: en horas de mucho tráfico global,
  un cron de cada 15 min puede retrasarse varios minutos. Es gratis pero no es
  tiempo real garantizado.
- **Plan gratuito de Twelve Data**: con listas grandes de tickers y varias candidatas
  con 4 timeframes cada una, puedes acercarte al límite diario (800 peticiones).
  Si lo superas, ese escaneo simplemente fallará silenciosamente hasta el día siguiente.
- Esta herramienta **no predice** movimientos de x8-x10 ni garantiza nada — solo
  automatiza la detección de condiciones que tú defines y te enseña las velas para
  que decidas.
- El universo de `universe.py` es una selección manual curada, **no** una réplica
  exacta y en vivo del S&P 500 / Nasdaq 100.
- El Radar Diario hace ~150 peticiones en una sola ejecución (una por ticker); con el
  screener intradía corriendo en paralelo, vigila no acercarte al límite de 800/día
  del plan gratuito de Twelve Data.
- El campo "Catalizador" usa Finnhub si has añadido `FINNHUB_API_KEY`; si no, se mostrará
  como "no disponible" pero el resto del sistema sigue funcionando igual.
