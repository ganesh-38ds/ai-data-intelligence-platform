@echo off
setlocal enabledelayedexpansion
title AI Data Intelligence & RAG Platform Launcher
color 0B

echo =====================================================================
echo    AI-Powered Data Intelligence & RAG Evaluation Platform
echo =====================================================================
echo.

cd /d "%~dp0"

:: 1. Locate Python executable in backend venv
set "PYTHON_EXE="
if exist "backend\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=backend\.venv\Scripts\python.exe"
) else if exist "backend\venv\Scripts\python.exe" (
    set "PYTHON_EXE=backend\venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [*] Detected Python: %PYTHON_EXE%

:: 2. Launch FastAPI Backend
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AI Data Platform - Backend (Port 8000)" cmd /k "cd /d "%~dp0backend" && ..\%PYTHON_EXE% -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 3. Brief wait for backend port binding
echo [*] Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

:: 4. Launch Vite Frontend Dev Server
echo [*] Starting Vite Frontend on http://localhost:5173 ...
start "AI Data Platform - Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: 5. Wait and launch browser
echo [*] Waiting 2 seconds then opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo =====================================================================
echo    [SUCCESS] Both Backend & Frontend have been launched!
echo    - Frontend UI:  http://localhost:5173
echo    - Backend API:  http://127.0.0.1:8000
echo    - Swagger Docs: http://127.0.0.1:8000/docs
echo =====================================================================
echo.
echo Leave this launcher window or press any key to exit launcher.
pause >nul
