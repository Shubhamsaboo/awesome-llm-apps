@echo off
setlocal
set "APP_DIR=%~dp0"
set "VENV_PYTHON=%APP_DIR%.venv\Scripts\python.exe"
cd /d "%APP_DIR%"
echo Cleaning up old program on port 8501 ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo ============================================
echo   Starting AI Travel Agent...
echo   Browser will open at: http://127.0.0.1:8501
echo   If browser does not open, visit that address manually
echo   Close this window to stop the program
echo ============================================
echo.
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -m streamlit run my_travel_agent.py --server.port 8501
) else (
    echo Virtual environment not found. Run setup first:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements-langgraph.txt
    pause
    exit /b 1
)
echo.
echo [Program stopped. Press any key to close this window]
pause
