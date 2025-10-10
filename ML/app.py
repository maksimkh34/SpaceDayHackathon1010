from flask import Flask, request, jsonify
import cv2
import numpy as np
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "ML"})

@app.route('/analyze', methods=['POST'])
def analyze():
    # Базовая заглушка для анализа
    return jsonify({
        "status": "success",
        "result": "Базовая аналитика: изображение получено успешно",
        "details": "ML сервис в процессе настройки"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)