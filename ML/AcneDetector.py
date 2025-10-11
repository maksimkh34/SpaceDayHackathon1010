import numpy as np
import cv2
from typing import Optional, Dict
from scipy import ndimage
from skimage.feature.texture import local_binary_pattern
from skimage import morphology
from skimage import filters
from ImageProcessor import ImageProcessor

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
        red_thresh = np.percentile(red_index.flatten(), 80)
        red_prom = red_index > red_thresh
        
        lbp = local_binary_pattern(gray_eq_skin, P=8, R=1, method='uniform')
        lbp_thresh = np.percentile(lbp.flatten(), 80)
        lbp_mask = lbp > lbp_thresh
        
        small_gray = cv2.resize(gray_eq_skin, (w // 4, h // 4))
        entropy = filters.rank.entropy(small_gray, morphology.disk(5))
        entropy_resized = cv2.resize(entropy, (w, h), interpolation=cv2.INTER_LINEAR)
        entropy_mask = entropy_resized > np.percentile(entropy_resized.flatten(), 85)
        
        spots = candidate_var & red_prom & (lbp_mask | entropy_mask)
        
        if skin_mask is not None:
            spots = spots & skin_mask.astype(bool)
        
        min_size = max(5, int(0.0001 * h * w))
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
            'mild_acne': ImageProcessor.normalize01(mild_score / 0.05),
            'moderate_acne': ImageProcessor.normalize01(moderate_score / 0.04),
            'severe_acne': ImageProcessor.normalize01(severe_score / 0.03)
        }

