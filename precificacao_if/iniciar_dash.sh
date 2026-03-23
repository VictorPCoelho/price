#!/bin/bash
echo "============================================"
echo "  Precificacao IF — Noir Gold Edition"
echo "============================================"
pip3 install dash plotly pandas openpyxl -q
echo "Acesse: http://localhost:8050"
python3 app_dash.py
