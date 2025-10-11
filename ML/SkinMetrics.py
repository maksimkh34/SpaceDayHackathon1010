from ImageProcessor import ImageProcessor
from ColorConverter import ColorConverter
from typing import Optional
import numpy as np
import cv2

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

