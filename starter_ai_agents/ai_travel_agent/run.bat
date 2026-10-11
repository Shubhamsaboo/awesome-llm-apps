@echo off
cd /d "D:\AgentDev\repos\starter_ai_agents\ai_travel_agent"
echo Cleaning up old program on port 8501 ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8501 " ^| findstr "LISTENING"') do taskkill /f /pid %%a >nul 2>&1
echo ============================================
echo   Starting AI Travel Agent...
echo   Browser will open at: http://127.0.0.1:8501
echo   If browser does not open, visit that address manually
echo   Close this window to stop the program
echo ============================================
echo.
"D:\Python312\python.exe" -m streamlit run my_travel_agent.py --server.port 8501
echo.
echo [Program stopped. Press any key to close this window]
pause
