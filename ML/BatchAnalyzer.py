from FaceAnalyzer import FaceAnalyzer
from typing import List, Dict
import cv2
import numpy as np
from typing import Dict, List

class SkinHealthReport:
    @staticmethod
    def generate_report(metrics: Dict[str, float]) -> Dict[str, any]:
        report = {
            'overall_score': SkinHealthReport._calculate_overall_score(metrics),
            'recommendations': SkinHealthReport._generate_recommendations(metrics),
            'features': SkinHealthReport._get_features(metrics),
            'metrics_summary': metrics
        }
        return report
    
    @staticmethod
    def _calculate_overall_score(metrics: Dict[str, float]) -> float:
        weights = {
            'paleness': 0.05,
            'cyanosis': 0.08,
            'jaundice': 0.08,
            'redness': 0.07,
            'acne_spots': 0.12,
            'oiliness': 0.08,
            'pigmentation': 0.09,
            'vascularity': 0.06,
            'puffiness': 0.07,
            'dark_circles': 0.08,
            'wrinkles': 0.10,
            'texture_roughness': 0.06,
            'pore_size': 0.06
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for key, weight in weights.items():
            if key in metrics:
                total_score += (1.0 - metrics[key]) * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def _get_features(metrics: Dict[str, float]) -> List[str]:
        dark_circles = metrics.get('dark_circles', 0.0)
        puffiness = metrics.get('puffiness', 0.0)
        wrinkles = metrics.get('wrinkles', 0.0)
        redness = metrics.get('redness', 0.0)
        oiliness = metrics.get('oiliness', 0.0)
        paleness = metrics.get('paleness', 0.0)
        cyanosis = metrics.get('cyanosis', 0.0)
        jaundice = metrics.get('jaundice', 0.0)
        mild_acne = metrics.get('mild_acne', 0.0)
        moderate_acne = metrics.get('moderate_acne', 0.0)
        severe_acne = metrics.get('severe_acne', 0.0)
        texture_roughness = metrics.get('texture_roughness', 0.0)
        pigmentation = metrics.get('pigmentation', 0.0)
        pore_size = metrics.get('pore_size', 0.0)
        vascularity = metrics.get('vascularity', 0.0)
            # === КОМПЛЕКСНЫЕ ХАРАКТЕРИСТИКИ ===
        fatigue = (dark_circles + puffiness + wrinkles) / 3.0
        stress = (wrinkles + redness + oiliness) / 3.0
        skin_health = 1 - (0.5*(mild_acne + moderate_acne + severe_acne) + 0.3*redness + 0.2*texture_roughness)
        color_balance = 1 - (0.5*paleness + 0.5*cyanosis)
        eye_condition = 1 - (0.5*dark_circles + 0.5*jaundice + 0.3*redness)
        aging_signs = (0.4*wrinkles + 0.3*pore_size + 0.3*pigmentation)
        puffiness_level = puffiness
        oil_balance = oiliness

        # === РЕЗУЛЬТАТЫ ===
        good_keys = []
        bad_keys = []

        # Эмоциональное состояние
        good_keys.append("fatigue_low" if fatigue < 0.4 else "fatigue_high")
        good_keys.append("stress_low" if stress < 0.4 else "stress_high")

        # Кожа
        if skin_health > 0.7:
            good_keys.append("skin_good")
        elif skin_health < 0.4:
            bad_keys.append("skin_poor")
        else:
            bad_keys.append("skin_moderate")

        # Цвет лица
        if color_balance > 0.7:
            good_keys.append("color_good")
        elif color_balance < 0.4:
            bad_keys.append("color_bad")

        # Область глаз
        if eye_condition > 0.7:
            good_keys.append("eyes_good")
        elif eye_condition < 0.4:
            bad_keys.append("eyes_bad")

        # Старение
        if aging_signs < 0.4:
            good_keys.append("aging_low")
        elif aging_signs > 0.7:
            bad_keys.append("aging_high")

        # Отёки
        if puffiness_level > 0.6:
            bad_keys.append("puffiness_high")
        elif puffiness_level < 0.3:
            good_keys.append("puffiness_low")

        # Баланс жирности
        if oil_balance > 0.6:
            bad_keys.append("oiliness_high")
        elif oil_balance < 0.3 and texture_roughness > 0.5:
            bad_keys.append("dryness_high")
        else:
            good_keys.append("hydration_ok")


        return good_keys, bad_keys      
        
    @staticmethod
    def _generate_recommendations(metrics: Dict[str, float]) -> List[str]:
        recommendations = []
        
        if metrics.get('acne_spots', 0) > 0.4 or metrics.get('severe_acne', 0) > 0.3:
            recommendations.append("Консультация дерматолога для лечения акне")
            recommendations.append("Использование некомедогенных продуктов")
        
        if metrics.get('oiliness', 0) > 0.5:
            recommendations.append("Матирующие средства и контроль жирности")
            recommendations.append("Регулярное очищение кожи")
        
        if metrics.get('pigmentation', 0) > 0.5:
            recommendations.append("SPF защита ежедневно")
            recommendations.append("Средства с витамином C и ниацинамидом")
        
        if metrics.get('dark_circles', 0) > 0.5:
            recommendations.append("Крем для области вокруг глаз с кофеином")
            recommendations.append("Контроль режима сна")
        
        if metrics.get('wrinkles', 0) > 0.5:
            recommendations.append("Антивозрастные средства с ретинолом")
            recommendations.append("Увлажнение и защита от солнца")
        
        if metrics.get('puffiness', 0) > 0.5:
            recommendations.append("Лимфодренажный массаж")
            recommendations.append("Контроль потребления соли")
        
        if metrics.get('cyanosis', 0) > 0.3 or metrics.get('jaundice', 0) > 0.3:
            recommendations.append("Обратиться к врачу для обследования")
        
        if metrics.get('texture_roughness', 0) > 0.5:
            recommendations.append("Мягкие эксфолианты для выравнивания текстуры")
        
        if metrics.get('pore_size', 0) > 0.5:
            recommendations.append("Средства с BHA кислотами для очищения пор")
        
        return recommendations if recommendations else ["Кожа в хорошем состоянии"]


class BatchAnalyzer:
    def __init__(self):
        self.analyzer = FaceAnalyzer()
    
    def analyze_multiple(self, image_paths: List[str]) -> List[Dict]:
        results = []
        
        for path in image_paths:
            try:
                img = cv2.imread(path)
                if img is None:
                    results.append({'path': path, 'error': 'Не удалось загрузить изображение'})
                    continue
                
                metrics, _ = self.analyzer.analyze(img, visualize=False)
                report = SkinHealthReport.generate_report(metrics)
                
                results.append({
                    'path': path,
                    'metrics': metrics,
                    'report': report
                })
            except Exception as e:
                results.append({'path': path, 'error': str(e)})
        
        return results
    
    def compare_analyses(self, results: List[Dict]) -> Dict[str, any]:
        if not results or all('error' in r for r in results):
            return {'error': 'Нет валидных результатов для сравнения'}
        
        valid_results = [r for r in results if 'metrics' in r]
        
        if len(valid_results) < 2:
            return {'error': 'Недостаточно результатов для сравнения'}
        
        metric_keys = valid_results[0]['metrics'].keys()
        comparisons = {}
        
        for key in metric_keys:
            values = [r['metrics'][key] for r in valid_results]
            comparisons[key] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'trend': 'улучшение' if values[-1] < values[0] else 'ухудшение' if values[-1] > values[0] else 'стабильно'
            }
        
        return {
            'comparisons': comparisons,
            'overall_trend': self._calculate_overall_trend(valid_results)
        }
    
    @staticmethod
    def _calculate_overall_trend(results: List[Dict]) -> str:
        scores = [r['report']['overall_score'] for r in results]
        
        if len(scores) < 2:
            return 'недостаточно данных'
        
        if scores[-1] > scores[0] + 0.05:
            return 'значительное улучшение'
        elif scores[-1] > scores[0]:
            return 'улучшение'
        elif scores[-1] < scores[0] - 0.05:
            return 'значительное ухудшение'
        elif scores[-1] < scores[0]:
            return 'ухудшение'
        else:
            return 'стабильно'

