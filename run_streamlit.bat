@echo off
title VegCare AI - Streamlit Web Application
cd /d "%~dp0"

echo ======================================================================
echo       VegCare AI - ระบบวิเคราะห์โรคพืชและทุเรียนด้วย Streamlit
echo ======================================================================
echo.
echo  กำลังเปิดแอปพลิเคชัน Streamlit...
echo  - เปิดบนคอมพิวเตอร์: http://localhost:8501
echo  - เปิดบนมือถือ (Wi-Fi เดียวกัน): http://192.168.1.54:8501
echo.

python -m streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501

pause
