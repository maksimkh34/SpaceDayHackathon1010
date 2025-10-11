#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Starting Frontend in development mode..."

# Проверяем и устанавливаем зависимости если нужно
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Проверяем что Vite доступен
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Please install Node.js"
    exit 1
fi

echo "✅ Dependencies ready. Starting dev server..."
npm run dev -- --host 0.0.0.0
