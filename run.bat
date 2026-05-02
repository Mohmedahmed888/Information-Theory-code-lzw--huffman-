@echo off
setlocal EnableExtensions

REM ECU Compression Tool launcher (Windows)
REM - Web app (Flask):  http://localhost:5000
REM - GUI app (Tkinter)
REM - Tests (CLI)

cd /d "%~dp0"

echo.
echo ================================
echo   ECU Compression Tool (Run)
echo ================================
echo   [1] Run WEB app (Flask)
echo   [2] Run GUI app (Tkinter)
echo   [3] Run test suite (CLI)
echo   [4] Exit
echo.

set /p choice=Choose an option (1-4): 

if "%choice%"=="1" goto web
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto tests
goto end

:web
echo.
echo Starting WEB server...
echo Open this in your browser: http://localhost:5000
echo.
python app.py
goto end

:gui
echo.
echo Starting GUI...
echo.
python gui\app.py
goto end

:tests
echo.
echo Running tests...
echo.
python test_all.py
goto end

:end
echo.
echo Done.
endlocal
