@echo off
cd /d %~dp0
echo 🚀 Starting Frontend in development mode...

REM Check and install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
)

echo ✅ Starting dev server...
npm run dev
pause
