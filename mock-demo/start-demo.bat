@echo off
echo Starting AI Governance Dashboard Mock Demo...
echo.
echo This will start both the mock API server and the frontend.
echo.
echo Press Ctrl+C to stop both servers.
echo.

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

REM Start both servers concurrently
npm start
