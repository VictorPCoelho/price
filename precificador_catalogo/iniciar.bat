@echo off
rem Inicia o Precificador de Catalogos no navegador.
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python -m streamlit run app.py
pause
