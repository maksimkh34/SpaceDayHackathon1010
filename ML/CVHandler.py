import cv2
import mediapipe as mp
import warnings
from FaceAnalyzer import FaceAnalyzer
from BatchAnalyzer import SkinHealthReport

warnings.filterwarnings('ignore')

mp_face = mp.solutions.face_mesh
def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Использование: python CVHandler_Optimized.py <путь_к_изображению> [--visualize] [--report]")
        sys.exit(1)
    
    img_path = sys.argv[1]
    visualize = '--visualize' in sys.argv
    generate_report = '--report' in sys.argv
    
    img = cv2.imread(img_path)
    if img is None:
        print(f"Ошибка: не удалось загрузить изображение {img_path}")
        sys.exit(1)
    
    analyzer = FaceAnalyzer()
    
    try:
        metrics, vis = analyzer.analyze(img, visualize=visualize)
        
        print("\n=== МЕТРИКИ АНАЛИЗА КОЖИ ===")
        for key, value in sorted(metrics.items()):
            print(f"{key:20s}: {value:.3f}")
        
        if generate_report:
            report = SkinHealthReport.generate_report(metrics)
            print(f"\n=== ОБЩАЯ ОЦЕНКА ===")
            print(f"Оценка состояния кожи: {report['overall_score']:.2%}")
            
            if report['concerns']:
                print(f"\n=== ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ ===")
                for concern in report['concerns']:
                    print(f"  - {concern}")
            
            print(f"\n=== РЕКОМЕНДАЦИИ ===")
            for rec in report['recommendations']:
                print(f"  - {rec}")
            
            with open('skin_analysis_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print("\nПолный отчет сохранен в skin_analysis_report.json")
        
        if vis is not None:
            output_path = 'analysis_visualization.jpg'
            cv2.imwrite(output_path, vis)
            print(f"\nВизуализация сохранена в {output_path}")
    
    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()