@echo off
title VegCare AI - Streamlit Web Application
cd /d "%~dp0"

echo ======================================================================
echo       VegCare AI - ระบบวิเคราะห์โรคพืชและทุเรียนด้วย Streamlit
echo ======================================================================
echo.
echo  กำลังเปิดแอปพลิเคชัน Streamlit...
echo  - เปิดบนเบราว์เซอร์: http://localhost:8501
echo.

python -m streamlit run streamlit_app.py

pause
