@echo off
echo ==========================================
echo Healthcare Authentication System Launcher
echo ==========================================
echo.

echo Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing FastAPI and Uvicorn...
    pip install fastapi uvicorn python-multipart
)

python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing Flask...
    pip install flask requests
)

echo All dependencies installed!
echo.

echo Starting services...
echo.

start "Registration Center" python rc.py
timeout /t 2 /nobreak >nul

start "Healthcare Server" python server1.py
timeout /t 2 /nobreak >nul

start "Middleware & UI" uvicorn middleware:app --host 0.0.0.0 --port 8000 --reload
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo All services are starting!
echo ==========================================
echo.
echo   Registration Center: http://localhost:5000
echo   Healthcare Server:   http://localhost:5001
echo   UI and Middleware:     http://localhost:8000
echo.
echo Open http://localhost:8000 in your browser
echo.
echo Press Ctrl+C in each window to stop services
echo ==========================================
echo.

pause
