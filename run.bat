@echo off
REM ============================================================
REM  Symptom Buddy - Windows launcher
REM  Double-click this file. It will:
REM    1. Create a Python virtual environment (.venv) if needed
REM    2. Install dependencies from requirements.txt
REM    3. Launch the Streamlit app at http://localhost:8501
REM  To stop the app, press Ctrl+C in this window.
REM  NOTE: This app is local-first and for general information
REM  only. It does not diagnose, prescribe a personal dose, or
REM  guarantee pharmacy stock. See README.md for details.
REM ============================================================
setlocal
cd /d "%~dp0"

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Trying the Python launcher...
    py -3 --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ERROR: Python 3.11 or newer is not installed.
        echo Please install it from https://www.python.org/downloads/
        echo and tick "Add python.exe to PATH" during setup, then run this file again.
        echo.
        pause
        exit /b 1
    )
    set "PY=py -3"
) else (
    set "PY=python"
)

if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment (.venv)...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo Installing dependencies (first run may take a minute)...
%PY% -m pip install --upgrade pip
if exist "requirements.txt" (
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Dependency install failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found. Installing Streamlit directly...
    %PY% -m pip install streamlit
)

echo.
echo Starting Symptom Buddy...
echo Open http://localhost:8501 in your browser if it does not open automatically.
echo Press Ctrl+C to stop.
echo.
%PY% -m streamlit run app.py --server.port 8501

echo.
echo The app has stopped.
pause
endlocal
