import ColorConverter
import numpy as np
import cv2
from skimage import morphology

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

