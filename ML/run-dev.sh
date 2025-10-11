#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting ML Service in development mode..."

# Принудительно удаляем старое окружение если оно не Python 3.10
if [ -d "venv" ]; then
    VENV_PYTHON_VERSION=$(venv/bin/python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "unknown")
    if [ "$VENV_PYTHON_VERSION" != "3.10" ]; then
        echo "🗑️ Removing incompatible virtual environment (Python $VENV_PYTHON_VERSION)"
        rm -rf venv
    fi
fi

# Проверяем наличие Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 not found!"
    echo "💡 Please install Python 3.10:"
    echo "   sudo apt update && sudo apt install python3.10 python3.10-venv"
    exit 1
fi

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with Python 3.10..."
    python3.10 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📥 Installing dependencies..."
pip install --upgrade pip

# Пытаемся установить все зависимости
if pip install -r requirements.txt; then
    echo "✅ All dependencies installed successfully"
else
    echo "⚠️ Some dependencies failed, installing core packages..."
    pip install flask opencv-python numpy scipy scikit-image pillow requests
    echo "💡 Running in fallback mode without MediaPipe"
fi

echo "🤖 Starting ML service on http://localhost:5000"
python app.py
