@echo off
title VegCare AI - ส่งโค้ดขึ้น GitHub สำหรับ bnote21-create
cd /d "%~dp0"

echo ======================================================================
echo    🥬 VegCare AI - กำลังดันโค้ดขึ้น GitHub: bnote21-create/vegcare-ai
echo ======================================================================
echo.

git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ======================================================================
    echo  [แจ้งเตือน]
    echo  หากเกิดข้อผิดพลาด ให้ตรวจสอบ 2 ข้อนี้ครับ:
    echo  1. คุณได้กดสร้าง Repository ชื่อ "vegcare-ai" บน GitHub แล้วหรือยัง?
    echo     (ถ้ายัง ให้คลิกสร้างที่: https://github.com/new?name=vegcare-ai)
    echo  2. หากมีหน้าต่าง Git เด้งขึ้นมาถามล็อกอิน ให้กด "Sign in with your browser"
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo  [สำเร็จเรียบร้อย!] โค้ดทั้งหมดขึ้น GitHub bnote21-create/vegcare-ai แล้ว
    echo.
    echo  กำลังเปิดหน้า Streamlit Cloud เพื่อให้คุณกด Deploy...
    echo ======================================================================
    echo.
    start "" "https://share.streamlit.io/deploy?repository=bnote21-create/vegcare-ai&branch=main&mainModule=streamlit_app.py"
)

pause
