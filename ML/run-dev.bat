@echo off
cd /d %~dp0
echo 🚀 Starting ML Service in development mode...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment  
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo 📥 Installing dependencies...
pip install --upgrade pip

REM Try to install requirements
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ⚠️  Some dependencies failed, installing core packages...
    pip install flask opencv-python numpy scipy scikit-image pillow requests
)

echo 🌐 Starting ML service on http://localhost:5000
python app.py
pause
