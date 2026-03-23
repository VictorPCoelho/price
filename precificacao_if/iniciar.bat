@echo off
echo ============================================
echo   Precificacao IF - Iniciando...
echo ============================================

REM Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado.
    echo Instale Python em: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Instala dependencias se necessario
echo Verificando dependencias...
pip install streamlit pandas openpyxl -q

REM Sobe o app
echo Iniciando o app...
echo Acesse: http://localhost:8501
echo Para encerrar: feche esta janela ou pressione Ctrl+C
echo.
streamlit run app.py --server.port 8501 --server.headless false
pause
