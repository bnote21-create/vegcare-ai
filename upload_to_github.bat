@echo off
title VegCare AI - อัปโหลดขึ้น GitHub อัตโนมัติ
cd /d "%~dp0"

echo ======================================================================
echo    🥬 VegCare AI - ตัวช่วยส่งโค้ดขึ้น GitHub เพื่อเปิดเว็บฟรี 24 ชม.
echo ======================================================================
echo.
echo  ขั้นตอนง่ายๆ:
echo  1. ไปที่ https://github.com/new แล้วกดสร้าง Repository ใหม่ (เช่น ตั้งชื่อว่า vegcare-ai)
echo  2. คัดลอกลิงก์ Repository ที่ได้ (เช่น https://github.com/ชื่อคุณ/vegcare-ai.git)
echo.
set /p REPO_URL="วางลิงก์ GitHub Repository ที่นี่แล้วกด Enter: "

if "%REPO_URL%"=="" (
    echo.
    echo คุณไม่ได้ระบุลิงก์ กรุณารันไฟล์นี้ใหม่อีกครั้ง
    pause
    exit /b
)

echo.
echo กำลังเชื่อมต่อและอัปโหลดโค้ดไปยัง: %REPO_URL% ...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ======================================================================
    echo  เกิดข้อผิดพลาดในการ Push หรือต้องการให้คุณล็อกอิน GitHub
    echo  หากระบบถาม Username/Password ให้ทำตามที่ GitHub แจ้งบนหน้าจอ
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo  สำเร็จ! อัปโหลดโค้ดขึ้น GitHub เรียบร้อยแล้ว
    echo.
    echo  ขั้นตอนสุดท้าย:
    echo  1. ไปที่ https://share.streamlit.io
    echo  2. กดปุ่ม "New app"
    echo  3. เลือก Repository ที่เพิ่งอัปโหลด
    echo  4. ช่อง Main file path ใส่: streamlit_app.py
    echo  5. กด Deploy!
    echo ======================================================================
    echo.
    start https://share.streamlit.io/
)

pause
