import cv2
import numpy as np

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

