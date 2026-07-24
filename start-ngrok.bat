@echo off
REM ============================================================
REM  Ngrok Tunnel Script untuk Actuarial Engine
REM  Menjalankan 2 tunnel: Backend (8000) + Frontend (3000)
REM ============================================================
echo.
echo ============================================================
echo   ACTUARIAL ENGINE - NGROK TUNNEL
echo ============================================================
echo.

REM --- Pastikan ngrok sudah terinstall ---
where ngrok >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] ngrok tidak ditemukan!
    echo.
    echo Install ngrok:
    echo   1. Download dari https://ngrok.com/download
    echo   2. Atau: choco install ngrok
    echo   3. Lalu: ngrok config add-authtoken YOUR_TOKEN
    echo.
    pause
    exit /b 1
)

echo [INFO] Pastikan backend (port 8000) dan frontend (port 3000) sudah berjalan.
echo.
echo Memulai ngrok tunnel...
echo.

REM --- Jalankan ngrok dengan 2 tunnel ---
ngrok start --all --config ngrok.yml

pause
