#!/bin/bash
echo "============================================"
echo "  Maestro de Estudos - Iniciando..."
echo "============================================"

if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 nao encontrado."
    echo "Instale em: https://www.python.org/downloads/"
    exit 1
fi

cd "$(dirname "$0")"

echo "Verificando dependencias..."
pip3 install -q -r requirements.txt

echo "Iniciando o app..."
echo "Acesse: http://localhost:8600"
echo "Para encerrar: pressione Ctrl+C"
echo ""
python3 -m uvicorn app.web.main:app --port 8600
