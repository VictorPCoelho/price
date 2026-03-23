@echo off
echo ============================================
echo   Precificacao IF — Noir Gold Edition
echo ============================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado.
    pause
    exit /b 1
)

echo Verificando dependencias...
pip install dash plotly pandas openpyxl -q

echo Iniciando o app...
echo Acesse: http://localhost:8050
echo Para encerrar: feche esta janela ou pressione Ctrl+C
echo.
python app_dash.py
pause
