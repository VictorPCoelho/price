#!/usr/bin/env bash
# Inicia o Precificador de Catálogos no navegador.
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt
python3 -m streamlit run app.py
