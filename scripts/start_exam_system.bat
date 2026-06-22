@echo off
setlocal EnableExtensions

title Exam System Launcher

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "BACKEND_PY=%ROOT%\backend\.venv\Scripts\python.exe"
set "FRONTEND_DIR=%ROOT%\frontend"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

echo.
echo ============================================
echo   Exam System Launcher
echo ============================================
echo.

if not exist "%ROOT%\" goto missing_root
if not exist "%BACKEND_PY%" goto missing_python
if not exist "%FRONTEND_DIR%\package.json" goto missing_frontend
if not exist "%FRONTEND_DIR%\node_modules\" goto missing_node_modules

echo [1/4] Stop old services on ports %BACKEND_PORT% and %FRONTEND_PORT%...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort %BACKEND_PORT%,%FRONTEND_PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
timeout /t 1 /nobreak >nul

echo [2/4] Start backend...
cd /d "%ROOT%"
start "exam-backend" cmd.exe /s /k ""%BACKEND_PY%" -m uvicorn backend.main:app --host 0.0.0.0 --port %BACKEND_PORT%"

echo [3/4] Start frontend...
cd /d "%FRONTEND_DIR%"
start "exam-frontend" cmd.exe /s /k "npm.cmd run dev -- --host 0.0.0.0 --port %FRONTEND_PORT%"

echo [4/4] Waiting for startup...
timeout /t 5 /nobreak >nul

set "LAN_IP="
for /f "usebackq delims=" %%i in (`powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254*' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1 -ExpandProperty IPAddress; if ($ip) { $ip }"`) do set "LAN_IP=%%i"

echo.
echo ============================================
echo   Started.
echo.
echo   PC:       http://localhost:%FRONTEND_PORT%
if defined LAN_IP echo   Phone:    http://%LAN_IP%:%FRONTEND_PORT%
echo   AI check: http://localhost:%BACKEND_PORT%/health/ai
echo.
start "" "http://localhost:%BACKEND_PORT%/health/ai"

echo   Two new windows were opened:
echo   - exam-backend
echo   - exam-frontend
echo.
echo   To stop: close those two windows.
echo ============================================
echo.
pause
exit /b 0

:missing_root
echo [ERROR] Project folder not found:
echo %ROOT%
pause
exit /b 1

:missing_python
echo [ERROR] Backend virtualenv python not found:
echo %BACKEND_PY%
echo.
echo Please install backend dependencies first.
pause
exit /b 1

:missing_frontend
echo [ERROR] Frontend folder is incomplete:
echo %FRONTEND_DIR%
pause
exit /b 1

:missing_node_modules
echo [ERROR] Frontend node_modules not found.
echo.
echo Run this first:
echo cd /d "%FRONTEND_DIR%"
echo npm.cmd install
pause
exit /b 1
