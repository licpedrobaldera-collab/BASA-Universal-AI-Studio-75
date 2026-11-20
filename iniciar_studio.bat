@echo off
title BASA Universal AI Studio - Servidor Local
echo Iniciando BASA Universal AI Studio...
if not exist venv (
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)
streamlit run app.py --server.port 8501
pause
