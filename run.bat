@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title Information Theory — Huffman & LZW Toolkit

REM Prefer project venv if present (pip install -r requirements.txt in .venv)
set "PYEXE=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PYEXE=%~dp0.venv\Scripts\python.exe"

where %PYEXE% >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.8+ and ensure it is on PATH.
  echo Tip:   python -m venv .venv
  echo        .venv\Scripts\activate
  echo        pip install -r requirements.txt
  pause
  exit /b 1
)

:menu
cls
echo.
echo  ============================================================
echo    Huffman ^& LZW — Compression Toolkit
echo  ============================================================
echo    [1]  Web app  (Flask)  ^> http://127.0.0.1:5000
echo    [2]  Desktop GUI (Tkinter^)
echo    [3]  Run automated tests
echo    [4]  Exit
echo  ============================================================
echo.
set "choice="
set /p choice=  Select option (1-4): 

if "%choice%"=="1" goto web
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto tests
if "%choice%"=="4" goto bye
goto menu

:web
echo.
echo  Starting Flask (development server). Press Ctrl+C to stop.
echo  URL: http://127.0.0.1:5000
echo.
%PYEXE% app.py
goto menu

:gui
echo.
%PYEXE% gui\app.py
goto menu

:tests
echo.
%PYEXE% test_all.py
echo.
pause
goto menu

:bye
echo  Goodbye.
endlocal
