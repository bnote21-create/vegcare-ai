@echo off
title VegCare AI - Public Online Access (เปิดดูได้จากทุกที่ทั่วโลก)
cd /d "%~dp0"

echo ======================================================================
echo    🥬 VegCare AI - ระบบเปิดแอปออนไลน์สาธารณะ (ฟรี 100%%)
echo ======================================================================
echo.
echo  1. กำลังเปิดเซิร์ฟเวอร์ VegCare AI ภายในเครื่อง...
start "" /b python -m streamlit run streamlit_app.py --server.port 8501 --server.headless true

echo  2. กำลังสร้างลิงก์ออนไลน์สาธารณะ HTTPS (เข้าได้จากทุกที่ทั่วโลก)...
echo     (รอประมาณ 3-5 วินาที ลิงก์ https://...lhr.life จะปรากฏด้านล่าง)
echo.
echo ======================================================================
echo.

:: รัน SSH reverse tunnel ผ่าน localhost.run (ฟรี ไม่ต้องลงโปรแกรมเพิ่ม)
ssh -o StrictHostKeyChecking=no -R 80:localhost:8501 nokey@localhost.run

pause
