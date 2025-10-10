import cv2
import mediapipe as mp
import numpy as np
from scipy import ndimage
from skimage import exposure, filters, morphology, feature, measure
from skimage.color import rgb2gray
from skimage.feature.texture import local_binary_pattern
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List
from functools import lru_cache
import warnings

warnings.filterwarnings('ignore')

mp_face = mp.solutions.face_mesh


@dataclass
class FaceRegions:
    LEFT_CHEEK: List[int] = None
    RIGHT_CHEEK: List[int] = None
    NOSE: List[int] = None
    FOREHEAD: List[int] = None
    LEFT_EYE: List[int] = None
    RIGHT_EYE: List[int] = None
    CHIN: List[int] = None
    NECK: List[int] = None
    
    def __post_init__(self):
        self.LEFT_CHEEK = LEFT_CHEEK = [36, 205, 187, 147, 187, 207, 216, 206, 203, 50, 101, 50]
        self.RIGHT_CHEEK = [280, 425, 411, 291, 375, 454]
        self.NOSE = [6, 197, 195, 5, 4, 1]
        self.FOREHEAD = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377]
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154]
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390]
        self.CHIN = [152, 148, 176, 149, 150]
        self.NECK = [152, 234, 454]


class ColorConverter:
    @staticmethod
    def to_rgb(img_bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def to_lab(img_bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    
    @staticmethod
    def to_hsv(img_bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    @staticmethod
    def to_ycrcb(img_bgr: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)


class ImageProcessor:
    @staticmethod
    def normalize01(x: float) -> float:
        return float(np.clip(x, 0.0, 1.0))
    
    @staticmethod
    def mean_channel(img: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        if mask is None:
            return np.mean(img.reshape(-1, img.shape[2]), axis=0)
        mask_bool = mask.astype(bool)
        if not mask_bool.any():
            return np.zeros(img.shape[2], dtype=float)
        return img[mask_bool].mean(axis=0)
    
    @staticmethod
    def polygon_mask(img_shape: Tuple[int, int], pts: List[Tuple[int, int]]) -> np.ndarray:
        mask = np.zeros(img_shape[:2], dtype=np.uint8)
        pts_arr = np.array(pts, dtype=np.int32)
        cv2.fillConvexPoly(mask, pts_arr, 255)
        return mask
    
    @staticmethod
    def get_landmark_points(landmarks, img_w: int, img_h: int, idx_list: List[int]) -> List[Tuple[int, int]]:
        return [(int(landmarks[idx].x * img_w), int(landmarks[idx].y * img_h)) for idx in idx_list]
    
    @staticmethod
    def crop_with_mask(img: np.ndarray, mask_bool: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        ys, xs = np.where(mask_bool)
        if ys.size == 0:
            return None, None
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        crop = img[y0:y1+1, x0:x1+1].copy()
        mask_crop = mask_bool[y0:y1+1, x0:x1+1].astype(np.uint8)
        return crop, mask_crop


class SkinSegmentation:
    @staticmethod
    def simple_skin_mask(roi_bgr: np.ndarray) -> np.ndarray:
        ycrcb = ColorConverter.to_ycrcb(roi_bgr)
        Y, Cr, Cb = cv2.split(ycrcb)
        mask = (Cr > 135) & (Cr < 180) & (Cb > 85) & (Cb < 135)
        mask = morphology.remove_small_objects(mask, min_size=100)
        return mask.astype(np.uint8)
    
    @staticmethod
    def advanced_skin_mask(roi_bgr: np.ndarray) -> np.ndarray:
        hsv = ColorConverter.to_hsv(roi_bgr)
        ycrcb = ColorConverter.to_ycrcb(roi_bgr)
        
        h, s, v = cv2.split(hsv)
        Y, Cr, Cb = cv2.split(ycrcb)
        
        mask1 = (Cr > 135) & (Cr < 180) & (Cb > 85) & (Cb < 135)
        mask2 = (h >= 0) & (h <= 50) & (s > 30) & (v > 40)
        
        combined = mask1 | mask2
        combined = morphology.remove_small_objects(combined, min_size=150)
        combined = morphology.binary_closing(combined, morphology.disk(3))
        
        return combined.astype(np.uint8)


class SkinMetrics:
    @staticmethod
    def compute_paleness_lab(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        lab = ColorConverter.to_lab(roi_bgr)
        meanL, meana, meanb = ImageProcessor.mean_channel(lab, skin_mask)
        Ln = meanL / 255.0
        chroma = np.sqrt(meana**2 + meanb**2) / 255.0
        pallor = Ln * (1.0 - chroma)
        return ImageProcessor.normalize01(pallor)
    
    @staticmethod
    def compute_cyanosis(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        rgb = ColorConverter.to_rgb(roi_bgr)
        vals = rgb[skin_mask.astype(bool)] if skin_mask is not None else rgb.reshape(-1, 3)
        if vals.size == 0:
            return 0.0
        r_mean, g_mean, b_mean = vals[:, 0].mean(), vals[:, 1].mean(), vals[:, 2].mean()
        score = max(0.0, (b_mean - (r_mean + g_mean) / 2.0) / 255.0)
        return ImageProcessor.normalize01(score * 2.0)
    
    @staticmethod
    def compute_jaundice(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        hsv = ColorConverter.to_hsv(roi_bgr)
        h, s, v = hsv[:,:,0].astype(np.float32), hsv[:,:,1].astype(np.float32), hsv[:,:,2].astype(np.float32)
        
        if skin_mask is not None:
            mask_bool = skin_mask.astype(bool)
            h_vals, s_vals = h[mask_bool], s[mask_bool]
        else:
            h_vals, s_vals = h.reshape(-1), s.reshape(-1)
        
        if h_vals.size == 0:
            return 0.0
        
        yellow_mask = ((h_vals >= 10) & (h_vals <= 35)) & (s_vals > 30)
        score = yellow_mask.mean()
        return ImageProcessor.normalize01(score * 1.5)
    
    @staticmethod
    def compute_redness(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        rgb = ColorConverter.to_rgb(roi_bgr).astype(np.float32)
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        
        if skin_mask is not None:
            mask_bool = skin_mask.astype(bool)
            r_vals, g_vals, b_vals = r[mask_bool], g[mask_bool], b[mask_bool]
        else:
            r_vals, g_vals, b_vals = r.reshape(-1), g.reshape(-1), b.reshape(-1)
        
        if r_vals.size == 0:
            return 0.0
        
        score = np.maximum(0, (r_vals - (g_vals + b_vals) / 2.0)) / 255.0
        return ImageProcessor.normalize01(score.mean() * 2.0)
    
    @staticmethod
    def compute_oiliness(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        hsv = ColorConverter.to_hsv(roi_bgr)
        v, s = hsv[:,:,2].astype(np.float32), hsv[:,:,1].astype(np.float32)
        
        bright = v > 220
        sat = s > 50
        highlight = bright & ~sat
        
        if skin_mask is not None:
            highlight = highlight & skin_mask.astype(bool)
        
        frac = highlight.sum() / (roi_bgr.shape[0] * roi_bgr.shape[1])
        return ImageProcessor.normalize01(frac * 10.0)
    
    @staticmethod
    def compute_pigmentation(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        lab = ColorConverter.to_lab(roi_bgr)
        L = lab[:,:,0].astype(np.float32)
        L_blur = cv2.GaussianBlur(L, (25, 25), 0)
        diff = L_blur - L
        mask = diff > 6
        
        if skin_mask is not None:
            mask = mask & skin_mask.astype(bool)
        
        frac = mask.sum() / (roi_bgr.shape[0] * roi_bgr.shape[1])
        return ImageProcessor.normalize01(frac / 0.03)
    
    @staticmethod
    def compute_vascularity(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        b, g, r = cv2.split(roi_bgr.astype(np.float32))
        red_minus_green = r - g
        hp = cv2.Laplacian(red_minus_green, cv2.CV_32F, ksize=3)
        hp_pos = hp > np.percentile(hp, 90)
        
        if skin_mask is not None:
            hp_pos = hp_pos & skin_mask.astype(bool)
        
        frac = hp_pos.sum() / (roi_bgr.shape[0] * roi_bgr.shape[1])
        return ImageProcessor.normalize01(frac * 5.0)


class AcneDetector:
    @staticmethod
    def detect_spots_and_acne(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        h, w = roi_bgr.shape[:2]
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_eq = clahe.apply(gray)
        
        if skin_mask is not None:
            mask_bool = skin_mask.astype(bool)
            median_val = np.median(gray_eq[mask_bool]) if mask_bool.sum() > 0 else 127
            gray_eq_skin = gray_eq.copy()
            gray_eq_skin[~mask_bool] = median_val
        else:
            gray_eq_skin = gray_eq
        
        local_var = ndimage.generic_filter(gray_eq_skin, np.var, size=9)
        Q1, Q3 = np.percentile(local_var, 25), np.percentile(local_var, 75)
        IQR = Q3 - Q1
        var_thresh = Q3 + 1.5 * IQR
        candidate_var = local_var > var_thresh
        
        b, g, r = cv2.split(roi_bgr)
        red_index = r.astype(float) - (g.astype(float) + b.astype(float)) / 2
        red_thresh = np.percentile(red_index.flatten(), 90)
        red_prom = red_index > red_thresh
        
        lbp = local_binary_pattern(gray_eq_skin, P=8, R=1, method='uniform')
        lbp_thresh = np.percentile(lbp.flatten(), 90)
        lbp_mask = lbp > lbp_thresh
        
        small_gray = cv2.resize(gray_eq_skin, (w // 4, h // 4))
        entropy = filters.rank.entropy(small_gray, morphology.disk(5))
        entropy_resized = cv2.resize(entropy, (w, h), interpolation=cv2.INTER_LINEAR)
        entropy_mask = entropy_resized > np.percentile(entropy_resized.flatten(), 85)
        
        spots = candidate_var & red_prom & (lbp_mask | entropy_mask)
        
        if skin_mask is not None:
            spots = spots & skin_mask.astype(bool)
        
        min_size = max(5, int(0.0005 * h * w))
        spots = morphology.remove_small_objects(spots, min_size=min_size)
        spots = morphology.binary_closing(spots, morphology.disk(3))
        spots = morphology.remove_small_objects(spots, min_size=min_size)
        
        contours, _ = cv2.findContours(spots.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        spots_filtered = np.zeros_like(spots, dtype=np.uint8)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            
            if perimeter == 0 or area < min_size:
                continue
            
            circularity = 4 * np.pi * area / (perimeter ** 2)
            
            if len(cnt) >= 5:
                (x, y), (MA, ma), angle = cv2.fitEllipse(cnt)
                eccentricity = np.sqrt(1 - (min(MA, ma) / max(MA, ma)) ** 2) if max(MA, ma) > 0 else 1.0
            else:
                eccentricity = 1.0
            
            if 0.4 <= circularity <= 1.0 and eccentricity < 0.9 and area < 0.05 * h * w:
                cv2.drawContours(spots_filtered, [cnt], -1, 1, -1)
        
        score = spots_filtered.sum() / float(h * w)
        return ImageProcessor.normalize01(score / 0.015)
    
    @staticmethod
    def analyze_acne_severity(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        h, w = roi_bgr.shape[:2]
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_eq = clahe.apply(gray)
        
        b, g, r = cv2.split(roi_bgr)
        red_index = r.astype(float) - (g.astype(float) + b.astype(float)) / 2
        
        local_var = ndimage.generic_filter(gray_eq, np.var, size=9)
        
        mild_mask = (red_index > np.percentile(red_index, 75)) & (local_var > np.percentile(local_var, 70))
        moderate_mask = (red_index > np.percentile(red_index, 85)) & (local_var > np.percentile(local_var, 80))
        severe_mask = (red_index > np.percentile(red_index, 92)) & (local_var > np.percentile(local_var, 90))
        
        if skin_mask is not None:
            mask_bool = skin_mask.astype(bool)
            mild_mask = mild_mask & mask_bool
            moderate_mask = moderate_mask & mask_bool
            severe_mask = severe_mask & mask_bool
        
        total_pixels = h * w
        mild_score = mild_mask.sum() / total_pixels
        moderate_score = moderate_mask.sum() / total_pixels
        severe_score = severe_mask.sum() / total_pixels
        
        return {
            'mild_acne': ImageProcessor.normalize01(mild_score / 0.02),
            'moderate_acne': ImageProcessor.normalize01(moderate_score / 0.01),
            'severe_acne': ImageProcessor.normalize01(severe_score / 0.005)
        }


class FacialFeatureAnalyzer:
    @staticmethod
    def compute_puffiness(landmarks, img_w: int, img_h: int) -> float:
        try:
            left_eye_top = landmarks[159]
            left_eye_bottom = landmarks[145]
            left_cheek_bottom = landmarks[205]
            right_eye_top = landmarks[386]
            right_eye_bottom = landmarks[374]
            right_cheek_bottom = landmarks[425]
        except Exception:
            return 0.0
        
        def dist(a, b):
            return np.hypot((a.x - b.x) * img_w, (a.y - b.y) * img_h)
        
        left_eye_h = dist(left_eye_top, left_eye_bottom)
        left_eye_to_cheek = dist(left_eye_bottom, left_cheek_bottom)
        right_eye_h = dist(right_eye_top, right_eye_bottom)
        right_eye_to_cheek = dist(right_eye_bottom, right_cheek_bottom)
        
        left_score = 1.0 - (left_eye_h / (left_eye_to_cheek + 1e-6))
        right_score = 1.0 - (right_eye_h / (right_eye_to_cheek + 1e-6))
        score = np.clip((left_score + right_score) / 2.0, 0.0, 1.0)
        
        return float(score)
    
    @staticmethod
    def compute_dark_circles(image_bgr: np.ndarray, landmarks, img_w: int, img_h: int, regions: FaceRegions) -> float:
        left_eye_pts = ImageProcessor.get_landmark_points(landmarks, img_w, img_h, regions.LEFT_EYE)
        right_eye_pts = ImageProcessor.get_landmark_points(landmarks, img_w, img_h, regions.RIGHT_EYE)
        
        def expand_pts(pts, dy=15):
            return [(x, y + dy) for (x, y) in pts]
        
        le_below = ImageProcessor.polygon_mask(image_bgr.shape, expand_pts(left_eye_pts, dy=18))
        re_below = ImageProcessor.polygon_mask(image_bgr.shape, expand_pts(right_eye_pts, dy=18))
        
        left_cheek = ImageProcessor.polygon_mask(image_bgr.shape, 
                                                ImageProcessor.get_landmark_points(landmarks, img_w, img_h, regions.LEFT_CHEEK))
        right_cheek = ImageProcessor.polygon_mask(image_bgr.shape,
                                                 ImageProcessor.get_landmark_points(landmarks, img_w, img_h, regions.RIGHT_CHEEK))
        
        mask_eye = le_below.astype(bool) | re_below.astype(bool)
        mask_cheek = left_cheek.astype(bool) | right_cheek.astype(bool)
        
        lab = ColorConverter.to_lab(image_bgr)
        L = lab[:,:,0].astype(np.float32)
        
        mean_eye_L = L[mask_eye].mean() if mask_eye.sum() > 0 else 255.0
        mean_cheek_L = L[mask_cheek].mean() if mask_cheek.sum() > 0 else 255.0
        
        diff = (mean_cheek_L - mean_eye_L) / 255.0
        return ImageProcessor.normalize01(diff * 2.0)
    
    @staticmethod
    def compute_wrinkles(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        edges = feature.canny(gray, sigma=1.5, low_threshold=10, high_threshold=30)
        
        if skin_mask is not None:
            mask_bool = skin_mask.astype(bool)
            gradient_magnitude = gradient_magnitude * mask_bool
            edges = edges & mask_bool
        
        grad_score = gradient_magnitude.mean() / 255.0
        edge_score = edges.sum() / (roi_bgr.shape[0] * roi_bgr.shape[1])
        
        wrinkle_score = (grad_score * 0.6 + edge_score * 0.4)
        return ImageProcessor.normalize01(wrinkle_score * 3.0)
    
    @staticmethod
    def compute_texture_roughness(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        
        lbp = local_binary_pattern(gray, P=24, R=3, method='uniform')
        
        if skin_mask is not None:
            lbp_vals = lbp[skin_mask.astype(bool)]
        else:
            lbp_vals = lbp.reshape(-1)
        
        if lbp_vals.size == 0:
            return 0.0
        
        hist, _ = np.histogram(lbp_vals, bins=26, range=(0, 26), density=True)
        roughness = -np.sum(hist * np.log2(hist + 1e-10))
        
        return ImageProcessor.normalize01(roughness / 5.0)
    
    @staticmethod
    def compute_pore_size(roi_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> float:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        morph_grad = cv2.morphologyEx(blurred, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        
        _, thresh = cv2.threshold(morph_grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        if skin_mask is not None:
            thresh = thresh & (skin_mask * 255)
        
        pore_density = thresh.sum() / (roi_bgr.shape[0] * roi_bgr.shape[1] * 255)
        return ImageProcessor.normalize01(pore_density * 8.0)


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


class SkinHealthReport:
    @staticmethod
    def generate_report(metrics: Dict[str, float]) -> Dict[str, any]:
        report = {
            'overall_score': SkinHealthReport._calculate_overall_score(metrics),
            'concerns': SkinHealthReport._identify_concerns(metrics),
            'recommendations': SkinHealthReport._generate_recommendations(metrics),
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
    def _identify_concerns(metrics: Dict[str, float]) -> List[str]:
        concerns = []
        thresholds = {
            'acne_spots': 0.4,
            'severe_acne': 0.3,
            'moderate_acne': 0.4,
            'oiliness': 0.5,
            'pigmentation': 0.5,
            'dark_circles': 0.5,
            'wrinkles': 0.5,
            'puffiness': 0.5,
            'redness': 0.5,
            'cyanosis': 0.3,
            'jaundice': 0.3
        }
        
        for key, threshold in thresholds.items():
            if key in metrics and metrics[key] > threshold:
                concerns.append(key.replace('_', ' ').title())
        
        return concerns
    
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