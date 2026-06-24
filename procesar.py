name: Procesar Excel a JSON

on:
  push:
    paths:
      - '**.xlsx'
      - '**.xls'

jobs:
  procesar:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependencias
        run: pip install pandas openpyxl

      - name: Convertir Excel a JSON
        run: python procesar.py

      - name: Commit y push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/data.json
          git diff --staged --quiet || git commit -m "Datos actualizados $(date +'%Y-%m-%d')"
          git push
