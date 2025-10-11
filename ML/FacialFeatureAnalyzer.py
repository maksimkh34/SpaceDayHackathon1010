import numpy as np
from ImageProcessor import ImageProcessor
from ColorConverter import ColorConverter
import cv2
from typing import Optional, Dict
from skimage import feature
import FaceRegions
from skimage.feature.texture import local_binary_pattern

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
        
        def expand_pts(pts, dy=40):
            return [(x, y + dy) for (x, y) in pts]
        
        le_below = ImageProcessor.polygon_mask(image_bgr.shape, expand_pts(left_eye_pts, dy=10))
        re_below = ImageProcessor.polygon_mask(image_bgr.shape, expand_pts(right_eye_pts, dy=10))
        
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

