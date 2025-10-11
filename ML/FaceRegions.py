from dataclasses import dataclass
from typing import List

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
        self.LEFT_CHEEK  = [36, 205, 187, 147, 187, 207, 216, 206, 203, 50, 101, 50]
        self.RIGHT_CHEEK = [280, 425, 411, 291, 375, 454]
        self.NOSE = [6, 197, 195, 5, 4, 1]
        self.FOREHEAD = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377]
        self.LEFT_EYE = [33, 7, 163, 144, 145, 153, 154]
        self.RIGHT_EYE = [362, 382, 381, 380, 374, 373, 390]
        self.CHIN = [152, 148, 176, 149, 150]
        self.NECK = [152, 234, 454]