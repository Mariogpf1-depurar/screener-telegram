name: Radar Diario

on:
  schedule:
    # 12:15 UTC ≈ 8:15 ET (antes de apertura NYSE 9:30 ET). Ajusta si prefieres otra hora.
    - cron: '15 12 * * 1-5'
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  radar:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install -r requirements.txt

      - run: python daily_radar.py
        env:
          TWELVE_DATA_KEY: ${{ secrets.TWELVE_DATA_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}

      - name: Guardar watchlist en el repo
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add watchlist_today.txt
          git diff --quiet && git diff --staged --quiet || git commit -m "Actualizar watchlist del día"
          git pull --rebase origin main
          git push
