@echo off
echo ================================================
echo PRISM-AD Demo Server Starting
echo ================================================
echo.
echo Activating virtual environment...
call prism_env\Scripts\activate

echo.
echo Starting FastAPI server...
echo.
echo Once the server starts:
echo   - Open your browser to: http://127.0.0.1:8000
echo   - API documentation: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ================================================
echo.

python run_server.py
