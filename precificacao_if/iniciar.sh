#!/bin/bash
echo "============================================"
echo "  Precificacao IF - Iniciando..."
echo "============================================"

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 nao encontrado."
    echo "Instale em: https://www.python.org/downloads/"
    exit 1
fi

# Instala dependencias
echo "Verificando dependencias..."
pip3 install streamlit pandas openpyxl -q

# Sobe o app
echo "Iniciando o app..."
echo "Acesse: http://localhost:8501"
echo "Para encerrar: pressione Ctrl+C"
echo ""
streamlit run app.py --server.port 8501
