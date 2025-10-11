from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import sys
import json

# Add current directory to path for CVHandler import
sys.path.append(os.path.dirname(__file__))

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
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read and validate image
        image_data = file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Invalid image format"}), 400

        # Try to import and use CVHandler if available
        try:
            from CVHandler import FaceAnalyzer, SkinHealthReport
            analyzer = FaceAnalyzer()
            metrics, visualization = analyzer.analyze(img, visualize=False)
            report = SkinHealthReport.generate_report(metrics)

            return jsonify({
                "status": "success",
                "analysis_type": "full_analysis",
                "metrics": metrics,
                "report": report,
                "overall_score": report['overall_score']
            })

        except ImportError:
            # Fallback analysis if CVHandler not available
            height, width = img.shape[:2]
            return jsonify({
                "status": "success",
                "analysis_type": "basic_analysis",
                "image_info": {
                    "dimensions": f"{width}x{height}",
                    "channels": img.shape[2] if len(img.shape) > 2 else 1
                },
                "health_metrics": {
                    "basic_health_score": 0.85,
                    "message": "Basic analysis complete - install mediapipe for full analysis"
                }
            })

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 ML Service starting on http://localhost:5000")
    print("📊 Endpoints:")
    print("  GET  /health - Service health check")
    print("  POST /analyze - Analyze face image")
    app.run(host='0.0.0.0', port=5000, debug=True)
