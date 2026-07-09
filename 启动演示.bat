@echo off
title Contract System
cd /d "%~dp0backend"

echo.
echo ========================================
echo   Contract Management System
echo ========================================
echo.

echo [1/2] Checking demo data...

if not exist "data\store.json" (
    echo   Creating demo data...
    python -m app.demo_seed
    if errorlevel 1 (
        echo   FAILED to create demo data!
        pause
        exit /b 1
    )
) else (
    echo   Demo data exists, skipping
)

echo.
echo [2/2] Starting server...
echo.
echo   Opening http://localhost:8000
echo.
echo   Demo accounts (password: demo123456):
echo     admin        - Administrator
echo     zhangsan     - Handler
echo     lizhuguan    - Approver L1
echo     wangfawu     - Approver L2
echo.
echo   Press Ctrl+C to stop
echo ========================================
echo.

timeout /t 3 /nobreak >nul
start "" http://localhost:8000

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
