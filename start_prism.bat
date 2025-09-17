@echo off
title PRISM Server - Always Running
color 0A

echo ==========================================
echo    PRISM-AD Server Auto-Restart
echo ==========================================
echo.

cd /d "C:\Users\ITBlangeGi\prism"

:restart
echo [%date% %time%] Starting PRISM server...
venv\Scripts\python.exe prism_webapp.py

echo.
echo [%date% %time%] Server stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto restart
