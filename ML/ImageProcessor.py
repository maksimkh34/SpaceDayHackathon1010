import numpy as np
from typing import Tuple, Optional, Dict, List
import cv2 

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

