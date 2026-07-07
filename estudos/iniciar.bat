@echo off
echo ============================================
echo   Maestro de Estudos - Iniciando...
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
    echo ERRO: Python nao encontrado.
    echo Instale em: https://www.python.org/downloads/
    pause
    exit /b 1
)

cd /d "%~dp0"

echo Verificando dependencias...
pip install -q -r requirements.txt

echo Iniciando o app...
echo Acesse: http://localhost:8600
echo Para encerrar: pressione Ctrl+C
echo.
python -m uvicorn app.web.main:app --port 8600
