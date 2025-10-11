@echo off
echo 🚀 Starting ML Service in development mode...
echo.

REM Переходим в папку скрипта (на случай если запускаем из другой директории)
cd /d "%~dp0"

REM Проверяем наличие Python 3.10
echo 🔍 Checking for Python 3.10...

REM Метод 1: Пробуем python3.10
python3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3.10
    goto found_python
)

REM Метод 2: Пробуем py -3.10 (Windows Python launcher)
py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.10
    goto found_python
)

REM Метод 3: Пробуем python с проверкой версии
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set CURRENT_VERSION=%%i
    for /f "tokens=1,2 delims=." %%a in ("%CURRENT_VERSION%") do (
        if "%%a"=="3" if "%%b"=="10" (
            set PYTHON_CMD=python
            goto found_python
        )
    )
)

echo ❌ Python 3.10 not found!
echo.
echo 💡 Please install Python 3.10 from:
echo    https://www.python.org/downloads/release/python-31011/
echo.
echo 📋 Installation options:
echo    1. Download from python.org
echo    2. Use Windows Package Manager: winget install Python.Python.3.10
echo    3. Or use chocolatey: choco install python310
echo.
pause
exit /b 1

:found_python
%PYTHON_CMD% --version
echo ✅ Using: %PYTHON_CMD%

REM Создаем виртуальное окружение если его нет
if not exist "venv" (
    echo.
    echo 📦 Creating virtual environment with Python 3.10...
    %PYTHON_CMD% -m venv venv
)

REM Активируем виртуальное окружение
echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Обновляем pip
echo.
echo 📥 Upgrading pip...
python -m pip install --upgrade pip

REM Пытаемся установить все зависимости
echo.
echo 📥 Installing dependencies from requirements.txt...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Some dependencies failed, installing core packages...
    pip install flask opencv-python numpy scipy scikit-image pillow requests
    echo.
    echo 💡 Running in fallback mode without MediaPipe
    echo    Install Python 3.10 for full MediaPipe functionality
)

REM Проверяем установленные пакеты
echo.
echo 📋 Checking installed packages...
python -c "import flask; print('✅ Flask:', flask.__version__)" 2>nul || echo ❌ Flask not installed
python -c "import cv2; print('✅ OpenCV:', cv2.__version__)" 2>nul || echo ❌ OpenCV not installed
python -c "import numpy; print('✅ NumPy:', numpy.__version__)" 2>nul || echo ❌ NumPy not installed

REM Проверяем наличие app.py в текущей директории
if not exist "app.py" (
    echo.
    echo ❌ ERROR: app.py not found in current directory!
    echo 📍 Current directory: %CD%
    echo 💡 Make sure you're running the script from the ML folder
    echo.
    pause
    exit /b 1
)

echo.
echo 🤖 Starting ML service on http://localhost:5000
echo 📍 Running from: %CD%
echo 💡 Press Ctrl+C to stop the service
echo.

REM Запускаем приложение из текущей директории
python app.py

pause