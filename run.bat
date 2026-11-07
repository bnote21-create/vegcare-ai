@echo off
title VegCare AI - ระบบวิเคราะห์สุขภาพและโรคผักอัจฉริยะ
cd /d "%~dp0"

echo ======================================================================
echo       VegCare AI - ระบบวิเคราะห์สุขภาพและโรคผักอัจฉริยะ
echo ======================================================================
echo.
echo  กำลังตรวจสอบการติดตั้งและเริ่มต้นระบบเซิร์ฟเวอร์...
echo  - เปิดบนคอมพิวเตอร์: http://127.0.0.1:5000
echo  - เปิดหรือติดตั้งบน Android: http://192.168.1.54:5000
echo.

:: เปิด Browser อัตโนมัติหลังสตาร์ท 2 วินาที
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

python app.py
if errorlevel 1 (
    echo.
    echo เกิดข้อผิดพลาดในการรัน python app.py
    echo กรุณาตรวจสอบว่าติดตั้ง dependencies ครบถ้วนด้วยคำสั่ง:
    echo pip install -r requirements.txt
    echo.
)

pause
