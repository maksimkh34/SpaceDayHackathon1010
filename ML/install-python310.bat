@echo off
echo 🐍 Python 3.10 Installation Helper for Windows
echo =============================================
echo.

echo 📋 This script will help you install Python 3.10
echo.

set /p choice="Choose installation method (1-3):
1. Download from python.org (recommended)
2. Use winget (Windows Package Manager)
3. Use chocolatey
Your choice: "

if "%choice%"=="1" (
    echo.
    echo 🌐 Opening Python 3.10 download page...
    start https://www.python.org/downloads/release/python-31011/
    echo 📥 Please download and run the installer manually
    echo 💡 During installation, check 'Add Python to PATH'
)

if "%choice%"=="2" (
    echo.
    echo 📦 Installing via winget...
    winget install Python.Python.3.10
    if %errorlevel% equ 0 (
        echo ✅ Python 3.10 installed successfully!
    ) else (
        echo ❌ winget installation failed
        echo 💡 Make sure winget is available on your system
    )
)

if "%choice%"=="3" (
    echo.
    echo 📦 Installing via chocolatey...
    choco install python310 -y
    if %errorlevel% equ 0 (
        echo ✅ Python 3.10 installed successfully!
    ) else (
        echo ❌ chocolatey installation failed
        echo 💡 Make sure chocolatey is installed first
    )
)

echo.
echo 🔧 After installation, restart your command prompt and run:
echo    ML\run-dev.bat
echo.
pause
