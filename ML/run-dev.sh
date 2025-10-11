#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting ML Service in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install --upgrade pip

# Try to install from requirements, skip mediapipe if it fails
if pip install -r requirements.txt; then
    echo "✅ All dependencies installed successfully"
else
    echo "⚠️  Some dependencies failed, installing core packages..."
    pip install flask opencv-python numpy scipy scikit-image pillow requests
fi

echo "🌐 Starting ML service on http://localhost:5000"
python app.py
