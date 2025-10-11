import cv2
from AcneDetector import AcneDetector
from FaceRegions import FaceRegions
from ColorConverter import ColorConverter
from SkinMetrics import SkinMetrics
from SkinSegmentation import SkinSegmentation
from ImageProcessor import ImageProcessor
from FacialFeatureAnalyzer import FacialFeatureAnalyzer
from typing import Tuple, Optional, Dict
import numpy as np
import mediapipe as mp

mp_face = mp.solutions.face_mesh

class FaceAnalyzer:
    def __init__(self):
        self.regions = FaceRegions()
        self.color_converter = ColorConverter()
        self.processor = ImageProcessor()
        self.skin_seg = SkinSegmentation()
        self.metrics = SkinMetrics()
        self.acne_detector = AcneDetector()
        self.feature_analyzer = FacialFeatureAnalyzer()
    
    def analyze(self, img_bgr: np.ndarray, visualize: bool = False) -> Tuple[Dict[str, float], Optional[np.ndarray]]:
        h, w = img_bgr.shape[:2]
        
        with mp_face.FaceMesh(static_image_mode=True,
                            max_num_faces=1,
                            refine_landmarks=False,
                            min_detection_confidence=0.5) as face_mesh:
            img_rgb = self.color_converter.to_rgb(img_bgr)
            results = face_mesh.process(img_rgb)
            
            if not results.multi_face_landmarks:
                raise RuntimeError("Лицо не обнаружено")
            
            landmarks = results.multi_face_landmarks[0].landmark
        
        masks = self._create_region_masks(img_bgr, landmarks, w, h)
        crops = self._create_crops(img_bgr, masks)
        
        metrics_dict = self._compute_all_metrics(img_bgr, landmarks, w, h, crops, masks)
        
        vis = self._create_visualization(img_bgr, landmarks, w, h, metrics_dict) if visualize else None
        
        return metrics_dict, vis
    
    def _create_region_masks(self, img_bgr: np.ndarray, landmarks, w: int, h: int) -> Dict[str, np.ndarray]:
        masks = {}
        
        for region_name in ['LEFT_CHEEK', 'RIGHT_CHEEK', 'NOSE', 'FOREHEAD', 'CHIN', 'LEFT_EYE', 'RIGHT_EYE']:
            indices = getattr(self.regions, region_name)
            pts = self.processor.get_landmark_points(landmarks, w, h, indices)
            masks[region_name.lower()] = self.processor.polygon_mask(img_bgr.shape, pts).astype(bool)
        
        masks['face'] = masks['left_cheek'] | masks['right_cheek'] | masks['nose'] | masks['forehead'] | masks['chin']
        
        return masks
    
    def _create_crops(self, img_bgr: np.ndarray, masks: Dict[str, np.ndarray]) -> Dict[str, Tuple]:
        crops = {}
        for name, mask in masks.items():
            crops[name] = self.processor.crop_with_mask(img_bgr, mask)
        return crops
    
    def _compute_all_metrics(self, img_bgr: np.ndarray, landmarks, w: int, h: int, 
                           crops: Dict, masks: Dict) -> Dict[str, float]:
        face_crop, face_mask = crops['face']
        
        if face_crop is None:
            raise RuntimeError("Не удалось извлечь область лица")
        
        metrics_dict = {
            'paleness': self._compute_paleness_combined(crops),
            'cyanosis': self.metrics.compute_cyanosis(face_crop, face_mask),
            'jaundice': self.metrics.compute_jaundice(face_crop, face_mask),
            'redness': self.metrics.compute_redness(face_crop, face_mask),
            'acne_spots': self.acne_detector.detect_spots_and_acne(face_crop, face_mask),
            'oiliness': self.metrics.compute_oiliness(face_crop, face_mask),
            'pigmentation': self.metrics.compute_pigmentation(face_crop, face_mask),
            'vascularity': self.metrics.compute_vascularity(face_crop, face_mask),
            'puffiness': self.feature_analyzer.compute_puffiness(landmarks, w, h),
            'dark_circles': self.feature_analyzer.compute_dark_circles(img_bgr, landmarks, w, h, self.regions),
            'wrinkles': self.feature_analyzer.compute_wrinkles(face_crop, face_mask),
            'texture_roughness': self.feature_analyzer.compute_texture_roughness(face_crop, face_mask),
            'pore_size': self.feature_analyzer.compute_pore_size(face_crop, face_mask)
        }
        
        acne_severity = self.acne_detector.analyze_acne_severity(face_crop, face_mask)
        metrics_dict.update(acne_severity)
        
        return metrics_dict
    
    def _compute_paleness_combined(self, crops: Dict) -> float:
        lc_crop, lc_mask = crops['left_cheek']
        rc_crop, rc_mask = crops['right_cheek']
        face_crop, face_mask = crops['face']
        
        if lc_crop is not None and rc_crop is not None:
            pallor_l = self.metrics.compute_paleness_lab(lc_crop, lc_mask)
            pallor_r = self.metrics.compute_paleness_lab(rc_crop, rc_mask)
            return (pallor_l + pallor_r) / 2.0
        elif face_crop is not None:
            return self.metrics.compute_paleness_lab(face_crop, face_mask)
        return 0.0
    
    def _create_visualization(self, img_bgr: np.ndarray, landmarks, w: int, h: int, 
                            metrics_dict: Dict[str, float]) -> np.ndarray:
        vis = img_bgr.copy()
        
        region_colors = {
            'LEFT_CHEEK': (0, 255, 0),
            'RIGHT_CHEEK': (0, 255, 0),
            'NOSE': (255, 0, 0),
            'FOREHEAD': (0, 255, 255),
            'CHIN': (255, 255, 0),
            'LEFT_EYE': (255, 0, 255),
            'RIGHT_EYE': (255, 0, 255)
        }
        
        for region_name, color in region_colors.items():
            indices = getattr(self.regions, region_name)
            pts = self.processor.get_landmark_points(landmarks, w, h, indices)
            pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
            cv2.polylines(vis, [pts_arr], True, color, 2)
        
        y_offset = 30
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2
        
        sorted_metrics = sorted(metrics_dict.items())
        
        for key, value in sorted_metrics:
            text = f"{key}: {value:.3f}"
            color = self._get_metric_color(value)
            cv2.putText(vis, text, (10, y_offset), font, font_scale, color, thickness)
            y_offset += 22
        
        return vis
    
    @staticmethod
    def _get_metric_color(value: float) -> Tuple[int, int, int]:
        if value < 0.3:
            return (0, 255, 0)
        elif value < 0.6:
            return (0, 255, 255)
        else:
            return (0, 0, 255)

