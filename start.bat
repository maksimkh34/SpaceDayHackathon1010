@echo off
echo 🔧 Docker Compose Fix for Windows
echo =================================
echo.

echo 📋 Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not found or not running!
    echo.
    echo 💡 Please ensure:
    echo   1. Docker Desktop is installed
    echo   2. Docker Desktop is running
    echo   3. WSL2 is enabled (if using WSL2 backend)
    echo.
    echo 📥 Download Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is available

echo.
echo 🐳 Starting database container...
docker-compose up db -d

echo.
echo ⏳ Waiting for database to start...
timeout /t 5 /nobreak >nul

echo ✅ Database should be running on localhost:5432
echo 💡 If there are errors, check Docker Desktop is running
echo.
pause