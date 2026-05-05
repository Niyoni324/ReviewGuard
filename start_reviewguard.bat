@echo off
echo ===================================================
echo             Starting ReviewGuard Platform
echo ===================================================
echo.

echo [1/2] Starting FastAPI Backend on port 8000...
start "ReviewGuard Backend" cmd /k "cd backend && title ReviewGuard Backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting React Frontend...
start "ReviewGuard Frontend" cmd /k "cd frontend && title ReviewGuard Frontend && npm run dev"

echo.
echo Both services are starting in separate windows!
echo - Backend API: http://localhost:8000/docs
echo - Frontend UI: Typically http://localhost:5173 (Check the frontend window for exact URL)
echo.
echo Close this window at any time. To stop the servers, close their respective command prompt windows.
