import numpy as np
def glcm_contrast(gray, distances=[1], angles=[0], levels=256):
    """
    Вычисление GLCM contrast на сером изображении без skimage.
    """
    h, w = gray.shape
    gray = gray.astype(int)
    contrast_values = []
    
    for d in distances:
        for angle in angles:
            # горизонтальное смещение (angle=0)
            if angle == 0:
                glcm = np.zeros((levels, levels), dtype=np.float32)
                for i in range(h):
                    for j in range(w-d):
                        row = gray[i,j]
                        col = gray[i,j+d]
                        glcm[row, col] += 1
                # нормировка
                glcm = glcm / glcm.sum()
                # contrast = sum((i-j)^2 * P(i,j))
                I, J = np.meshgrid(np.arange(levels), np.arange(levels), indexing='ij')
                contrast = np.sum(glcm * (I-J)**2)
                contrast_values.append(contrast)
    return np.mean(contrast_values)