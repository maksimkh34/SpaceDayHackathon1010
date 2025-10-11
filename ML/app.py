from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import sys
import json
import traceback

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
print(f"✅ Current directory: {current_dir}")
print(f"✅ Python path: {sys.path}")

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "ML",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze"
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze face image for health metrics
    Expects multipart/form-data with 'file' field
    """
    print("📨 Received request to /analyze")
    if 'file' not in request.files:
        print("❌ No file in request")
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        print("❌ Empty filename")
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read and validate image
        print("🖼️ Reading image data...")
        image_data = file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ Failed to decode image")
            return jsonify({"error": "Invalid image format"}), 400

        print(f"🖼️ Image loaded successfully, shape: {img.shape}")

        # Try full analysis with mediapipe first, fallback to simple analysis
        try:
            print("🔄 Attempting full analysis with FaceAnalyzer...")
            from FaceAnalyzer import FaceAnalyzer
            from BatchAnalyzer import SkinHealthReport
            print("✅ FaceAnalyzer and SkinHealthReport imported successfully")

            analyzer = FaceAnalyzer()
            print("🔍 Starting face analysis...")
            metrics, visualization = analyzer.analyze(img, visualize=False)
            print(f"✅ Analysis completed, metrics: {list(metrics.keys())}")

            report = SkinHealthReport.generate_report(metrics)
            print("✅ Report generated successfully")

            # Create formatted report string
            report_lines = []
            report_lines.append("=== МЕТРИКИ АНАЛИЗА КОЖИ ===")
            for key, value in sorted(metrics.items()):
                report_lines.append(f"{key:20s}: {value:.3f}")

            report_lines.append("\n=== ОБЩАЯ ОЦЕНКА ===")
            report_lines.append(f"Оценка состояния кожи: {report.get('overall_score', 0):.2%}")

            concerns = report.get('concerns', [])
            if concerns:
                report_lines.append("\n=== ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ ===")
                for concern in concerns:
                    report_lines.append(f"  - {concern}")

            recommendations = report.get('recommendations', [])
            report_lines.append("\n=== РЕКОМЕНДАЦИИ ===")
            for rec in recommendations:
                report_lines.append(f"  - {rec}")

            formatted_report = "\n".join(report_lines)

            print("📊 Returning full analysis results")
            return jsonify({
                "status": "success",
                "analysis_type": "full_analysis",
                "metrics": metrics,
                "report": report,
                "formatted_report": formatted_report,
                "overall_score": report.get('overall_score', 0)
            })

        except ImportError as e:
            print(f"❌ Full analysis failed (ImportError): {e}")
            print("📋 Traceback:")
            traceback.print_exc()
            # Fallback to simple analysis
            from SimpleFaceAnalyzer import SimpleFaceAnalyzer
            print("✅ SimpleFaceAnalyzer imported successfully")

            analyzer = SimpleFaceAnalyzer()
            metrics, visualization = analyzer.analyze(img, visualize=False)

            # Генерируем упрощенный отчет
            report_lines = []
            report_lines.append("=== БАЗОВЫЙ АНАЛИЗ ИЗОБРАЖЕНИЯ ===")
            report_lines.append("⚠️  Внимание: используется упрощенный анализ (mediapipe не установлен)")
            report_lines.append("")

            for key, value in sorted(metrics.items()):
                report_lines.append(f"{key:25s}: {value:.3f}")

            report_lines.append("\n=== ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ ===")
            if metrics.get('brightness', 0) < 0.3:
                report_lines.append("  - Изображение слишком темное")
            elif metrics.get('brightness', 0) > 0.8:
                report_lines.append("  - Изображение пересвечено")

            if metrics.get('contrast', 0) < 0.3:
                report_lines.append("  - Низкая контрастность")

            if metrics.get('skin_tone_consistency', 0) < 0.4:
                report_lines.append("  - Неравномерный тон кожи")

            report_lines.append("\n=== РЕКОМЕНДАЦИИ ===")
            report_lines.append("  - Установите mediapipe для полного анализа кожи")
            report_lines.append("  - Убедитесь в хорошем освещении")
            report_lines.append("  - Используйте камеру с высоким разрешением")

            formatted_report = "\n".join(report_lines)

            print("📊 Returning simple analysis results")
            return jsonify({
                "status": "success",
                "analysis_type": "simple_analysis",
                "metrics": metrics,
                "formatted_report": formatted_report,
                "note": "Install mediapipe for full facial analysis"
            })

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            print("📋 Traceback:")
            traceback.print_exc()
            return jsonify({
                "status": "success",
                "analysis_type": "analysis_error_fallback",
                "formatted_report": f"Анализ завершен с ограничениями.\nОшибка: {str(e)}",
                "metrics": {}
            })

    except Exception as e:
        print(f"❌ General error: {e}")
        print("📋 Traceback:")
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 ML Service starting on http://localhost:5000")
    print("📊 Endpoints:")
    print("  GET  /health - Service health check")
    print("  POST /analyze - Analyze face image")
    app.run(host='0.0.0.0', port=5000, debug=True)
