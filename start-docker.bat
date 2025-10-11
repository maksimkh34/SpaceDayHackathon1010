@echo off
echo 🚀 Starting ML Service in development mode...
echo.

REM Set Python command options in order of preference
set PYTHON_OPTIONS=python3.10 python3.10.exe py -3.10 python

echo 🔍 Searching for Python 3.10...
set FOUND_PYTHON=
for %%P in (%PYTHON_OPTIONS%) do (
    if not defined FOUND_PYTHON (
        %%P --version >nul 2>&1
        if !errorlevel! == 0 (
            for /f "tokens=2" %%V in ('%%P --version 2^>^&1') do (
                echo %%V | findstr /r /c:"^3\.10\." >nul
                if !errorlevel! == 0 (
                    set FOUND_PYTHON=%%P
                    echo ✅ Found Python 3.10: %%P
                )
            )
        )
    )
)

if not defined FOUND_PYTHON (
    echo ❌ Python 3.10 not found!
    echo.
    echo 📋 Available Python versions:
    python --version 2>nul && echo   - python: OK || echo   - python: Not found
    python3 --version 2>nul && echo   - python3: OK || echo   - python3: Not found  
    py --list 2>nul && echo   - py: Available || echo   - py: Not found
    echo.
    echo 💡 Please install Python 3.10 from:
    echo   https://www.python.org/downloads/release/python-31011/
    echo.
    echo 🛠️ Or use Windows installer:
    echo   https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    echo.
    set /p CONTINUE="Continue with available Python? (y/N): "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
    REM Try to use any available Python
    python --version >nul 2>&1 && set FOUND_PYTHON=python
    if not defined FOUND_PYTHON (
        python3 --version >nul 2>&1 && set FOUND_PYTHON=python3
    )
    if not defined FOUND_PYTHON (
        echo ❌ No Python found. Exiting.
        pause
        exit /b 1
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo.
    echo 📦 Creating virtual environment...
    %FOUND_PYTHON% -m venv venv
    if !errorlevel! neq 0 (
        echo ❌ Failed to create virtual environment
        echo 💡 Try running: %FOUND_PYTHON% -m pip install venv
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 📥 Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo 📥 Installing dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Some dependencies failed, installing core packages...
    pip install flask opencv-python numpy scipy scikit-image pillow requests
    echo.
    echo 💡 Running in fallback mode without MediaPipe
)

REM Verify installation
echo.
echo 📋 Verifying installation...
python -c "import flask; print('✅ Flask:', flask.__version__)" 2>nul || echo ❌ Flask not installed
python -c "import cv2; print('✅ OpenCV:', cv2.__version__)" 2>nul || echo ❌ OpenCV not installed
python -c "import numpy; print('✅ NumPy:', numpy.__version__)" 2>nul || echo ❌ NumPy not installed
python -c "import sys; print('🐍 Python:', sys.version.split()[0])" 2>nul

echo.
echo 🤖 Starting ML service on http://localhost:5000
echo 💡 Press Ctrl+C to stop
echo.

python app.py

pause