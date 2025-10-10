# Требования:
# pip install opencv-python mediapipe numpy scipy scikit-image
# Python 3.8+
import cv2
import mediapipe as mp
import numpy as np
from scipy import ndimage
from skimage import exposure, filters, morphology, feature
from skimage.color import rgb2gray
from skimage.feature.texture import local_binary_pattern
import matplotlib.pyplot as plt
from GreyCO import glcm_contrast

mp_face = mp.solutions.face_mesh

def to_rgb(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

def to_lab(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)

def to_hsv(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

def normalize01(x):
    x = np.array(x, dtype=np.float32)
    x = np.clip(x, 0.0, 1.0)
    return float(x)

def simple_skin_mask_bgr(roi_bgr):
    ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    mask = (Cr > 135) & (Cr < 180) & (Cb > 85) & (Cb < 135)
    mask = morphology.remove_small_objects(mask, min_size=100)
    return mask.astype(np.uint8)


def mean_channel(img, mask=None):
    if mask is None:
        return np.mean(img.reshape(-1, img.shape[2]), axis=0)
    else:
        mask_bool = mask.astype(bool)
        if mask_bool.sum() == 0:
            return np.zeros(img.shape[2], dtype=float)
        vals = img[mask_bool]
        return vals.mean(axis=0)

def polygon_mask(img_shape, pts):
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    pts_arr = np.array(pts, dtype=np.int32)
    cv2.fillConvexPoly(mask, pts_arr, 255)
    return mask

LEFT_CHEEK_IDX = [50, 205, 187, 61, 146, 243]   # approximate convex hull for left cheek
RIGHT_CHEEK_IDX = [280, 425, 411, 291, 375, 454] # right cheek
NOSE_IDX = [6, 197, 195, 5, 4, 1]               # nose bridge and tip
FOREHEAD_IDX = [10, 338, 297, 332, 284, 251]    # broad forehead area
LEFT_EYE_IDX = [33, 7, 163, 144, 145, 153, 154] # area around left eye
RIGHT_EYE_IDX = [362, 382, 381, 380, 374, 373, 390] # around right eye
CHIN_IDX = [152, 148, 176, 149, 150]             # chin/jaw area
NECK_IDX = [152, 234, 454]                      # approximate neck base use points

def get_landmark_points(landmarks, img_w, img_h, idx_list):
    pts = []
    for idx in idx_list:
        lm = landmarks[idx]
        x = int(lm.x * img_w)
        y = int(lm.y * img_h)
        pts.append((x, y))
    return pts

# ---------- Metric calculations ----------
def compute_paleness_lab(roi_bgr, skin_mask=None):
    # Pallor (бледность) ~ высокая L в LAB но низкая насыщенность (a, b near neutral)
    lab = to_lab(roi_bgr)
    meanL, meana, meanb = mean_channel(lab, skin_mask)
    # Normalize: L in 0..255 -> 0..1. We'll map higher L => more pale, but also low chroma raises pallor.
    Ln = meanL / 255.0
    chroma = np.sqrt((meana**2 + meanb**2)) / 255.0
    # Pallor score heuristic: high L and low chroma
    pallor = Ln * (1.0 - chroma)
    return normalize01(pallor)

def compute_cyanosis(roi_bgr, skin_mask=None):
    # Cyanosis: bluish -> in RGB more blue channel relative to red/green
    rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
    if skin_mask is not None:
        vals = rgb[skin_mask.astype(bool)]
    else:
        vals = rgb.reshape(-1, 3)
    if vals.size == 0:
        return 0.0
    r_mean = vals[:,0].mean()
    g_mean = vals[:,1].mean()
    b_mean = vals[:,2].mean()
    # bluish if B >> R and B-G moderate
    score = max(0.0, (b_mean - (r_mean + g_mean)/2.0) / 255.0)
    return normalize01(score*2.0)  # amplify a bit

def compute_jaundice(roi_bgr, skin_mask=None):
    # Jaundice: yellowish -> high Y relative to B (in YCrCb or HSV: high B channel? better use HSV: hue around 20-40)
    hsv = to_hsv(roi_bgr)
    h = hsv[:,:,0].astype(np.float32) # 0..179
    s = hsv[:,:,1].astype(np.float32)
    v = hsv[:,:,2].astype(np.float32)
    if skin_mask is not None:
        h_vals = h[skin_mask.astype(bool)]
        s_vals = s[skin_mask.astype(bool)]
        v_vals = v[skin_mask.astype(bool)]
    else:
        h_vals = h.reshape(-1)
        s_vals = s.reshape(-1)
        v_vals = v.reshape(-1)
    if h_vals.size == 0:
        return 0.0
    # Yellow hue approx 10..35 in OpenCV HSV (0..179)
    yellow_mask = ((h_vals >= 10) & (h_vals <= 35)) & (s_vals > 30)
    score = yellow_mask.mean()
    return normalize01(score * 1.5)

def compute_redness(roi_bgr, skin_mask=None):
    # Redness: elevated red channel relative to green/blue and local saturation
    rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB).astype(np.float32)
    r = rgb[:,:,0]
    g = rgb[:,:,1]
    b = rgb[:,:,2]
    if skin_mask is not None:
        r_vals = r[skin_mask.astype(bool)]
        g_vals = g[skin_mask.astype(bool)]
        b_vals = b[skin_mask.astype(bool)]
    else:
        r_vals = r.reshape(-1)
        g_vals = g.reshape(-1)
        b_vals = b.reshape(-1)
    if r_vals.size == 0:
        return 0.0
    score = np.maximum(0, (r_vals - (g_vals + b_vals)/2.0)) / 255.0
    return float(np.clip(score.mean()*2.0, 0.0, 1.0))

def detect_spots_and_acne(roi_bgr, skin_mask=None):
    
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    
    # CLAHE
    # Применяем CLAHE только на ROI
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray_eq = clahe.apply(gray)
    
    # Применяем skin_mask к серой маске
    if skin_mask is not None:
        gray_eq_skin = gray_eq.copy()
        # Заполнение областей вне кожи - медиана ROI
        median_val = np.median(gray_eq[skin_mask.astype(bool)]) if skin_mask.sum()>0 else 127
        gray_eq_skin[~skin_mask.astype(bool)] = median_val
    else:
        gray_eq_skin = gray_eq

    h, w = roi_bgr.shape[:2]

    # ---------- Адаптивный локальный порог variance (для обнаружения бугров/неровностей) ----------
    local_var = ndimage.generic_filter(gray_eq_skin, np.var, size=9)
    # Используем медиану и IQR для более робастной оценки порога
    Q1 = np.percentile(local_var, 25)
    Q3 = np.percentile(local_var, 75)
    IQR = Q3 - Q1
    var_thresh = Q3 + 1.5 * IQR  # Порог выбросов
    candidate_var = local_var > var_thresh

    # ---------- Красный канал (для обнаружения воспалений) ----------
    b,g,r = cv2.split(roi_bgr)
    
    # Индекс покраснения: R - (G+B)/2
    red_index = r.astype(float) - (g.astype(float) + b.astype(float)) / 2
    
    # Адаптивный порог для покраснения (например, 90-й процентиль)
    red_thresh = np.percentile(red_index.flatten(), 90)
    red_prom = red_index > red_thresh
    
    # ---------- Текстурные признаки (LBP + Локальная Энтропия) ----------
    # LBP
    lbp = local_binary_pattern(gray_eq_skin, P=8, R=1, method='uniform')
    lbp_thresh = np.percentile(lbp.flatten(), 90) # Верхние 10% значений LBP
    lbp_mask = lbp > lbp_thresh
    
    # Локальная Энтропия (измеряет случайность/сложность) - акне обычно имеют низкую однородность
    # Уменьшим размер для ускорения и большей локальности
    small_gray = cv2.resize(gray_eq_skin, (w//4, h//4))
    entropy = filters.rank.entropy(small_gray, morphology.disk(5))
    entropy_resized = cv2.resize(entropy, (w, h), interpolation=cv2.INTER_LINEAR)
    
    # Порог: высокая энтропия
    entropy_mask = entropy_resized > np.percentile(entropy_resized.flatten(), 85)

    # ---------- Комбинируем кандидаты ----------
    # Комбинируем вариацию, покраснение, и текстуру
    # Spots - это области с высоким локальным контрастом (var), высокой краснотой (red_prom) и сложной текстурой (lbp_mask или entropy_mask)
    spots = candidate_var & red_prom & (lbp_mask | entropy_mask)

    if skin_mask is not None:
        spots = spots & (skin_mask.astype(bool))

    # ---------- Морфология и фильтрация по размеру ----------
    min_size = max(5, int(0.0005*h*w)) # Немного уменьшим минимальный размер
    spots = morphology.remove_small_objects(spots, min_size=min_size)
    spots = morphology.binary_closing(spots, morphology.disk(3)) # Заполнение небольших промежутков
    spots = morphology.remove_small_objects(spots, min_size=min_size) # Повторная фильтрация

    # ---------- Фильтрация по форме ----------
    # Находим контуры
    contours, _ = cv2.findContours(spots.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    spots_filtered = np.zeros_like(spots, dtype=np.uint8) # Изменено с dtype=bool
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4*np.pi*area/(perimeter**2)
        # Добавляем фильтр на эксцентриситет для более строгой формы
        (x,y), (MA,ma), angle = cv2.fitEllipse(cnt)
        eccentricity = np.sqrt(1 - (MA/ma)**2) if ma>0 else 1.0
        
        # Только относительно круглые/овальные пятна с умеренной эксцентричностью
        if 0.4 <= circularity <= 1.0 and eccentricity < 0.9: 
             # Дополнительная проверка размера (допустим, максимум 0.05 от общей площади)
             if area < 0.05*h*w:
                cv2.drawContours(spots_filtered, [cnt], -1, 1, -1)

    spots = spots_filtered

    # ---------- Финальная оценка ----------
    score = spots.sum() / float(h*w)
    # Немного уменьшим коэффициент нормализации для более чувствительного ответа
    return normalize01(score / 0.015) # Шкала: 0.05 площади = 1.0 (можно настроить)
def compute_oiliness(roi_bgr, skin_mask=None):
    # Oiliness -> more specular highlights (bright saturated small regions)
    hsv = to_hsv(roi_bgr)
    v = hsv[:,:,2].astype(np.float32)
    s = hsv[:,:,1].astype(np.float32)
    bright = v > 220
    sat = s > 50
    highlight = bright & ~sat  # specular highlights often high V, low-medium saturation
    if skin_mask is not None:
        highlight = highlight & (skin_mask.astype(bool))
    frac = highlight.sum() / (roi_bgr.shape[0]*roi_bgr.shape[1])
    # Oiliness score: small bright specular areas relative area
    return normalize01(frac * 10.0)  # scale

def compute_pigmentation(roi_bgr, skin_mask=None):
    # Pigment spots: darker patches with low L and higher local contrast
    lab = to_lab(roi_bgr)
    L = lab[:,:,0].astype(np.float32)
    # local mean L
    L_blur = cv2.GaussianBlur(L, (25,25), 0)
    diff = (L_blur - L)  # positive where L is darker than local mean
    mask = diff > 6  # threshold in L scale
    if skin_mask is not None:
        mask = mask & (skin_mask.astype(bool))
    frac = mask.sum() / (roi_bgr.shape[0]*roi_bgr.shape[1])
    return normalize01(frac / 0.03)  # typical pigmentation area ratio ~0..0.03

def compute_vascularity(roi_bgr, skin_mask=None):
    # Vascular network: detect thin red/blue lines -> enhance red channel, use high-pass filter
    b,g,r = cv2.split(roi_bgr.astype(np.float32))
    red_minus_green = (r - g)
    # high-pass filter (laplacian) to emphasize thin lines
    hp = cv2.Laplacian(red_minus_green, cv2.CV_32F, ksize=3)
    hp_pos = hp > np.percentile(hp, 90)
    if skin_mask is not None:
        hp_pos = hp_pos & (skin_mask.astype(bool))
    frac = hp_pos.sum() / (roi_bgr.shape[0]*roi_bgr.shape[1])
    return normalize01(frac * 5.0)

def compute_puffiness(landmarks, img_w, img_h):
    # Отёчность: намывка тканей вокруг глаз/щеки — простая эвристика на основе расстояний
    # сравниваем вертикальный размер глазного отверстия и расстояние от глаз до нижней границы скул.
    # Возьмём левые/правые ключевые точки
    # indices from mediapipe: left eye top: 386? (approx) — but вместо точных мы используем наборы:
    # We'll pick pairs: eye top(159) eye bottom(145) ; cheek bottom (205) ; eye center (33)
    try:
        # these indices are approximate commonly used
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        left_cheek_bottom = landmarks[205]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        right_cheek_bottom = landmarks[425]
    except Exception:
        return 0.0
    def dist(a,b):
        return np.hypot((a.x-b.x)*img_w, (a.y-b.y)*img_h)
    left_eye_h = dist(left_eye_top, left_eye_bottom)
    left_eye_to_cheek = dist(left_eye_bottom, left_cheek_bottom)
    right_eye_h = dist(right_eye_top, right_eye_bottom)
    right_eye_to_cheek = dist(right_eye_bottom, right_cheek_bottom)
    # puffiness if eye height small but distance to cheek small (swelling)
    left_score = 1.0 - (left_eye_h / (left_eye_to_cheek + 1e-6))
    right_score = 1.0 - (right_eye_h / (right_eye_to_cheek + 1e-6))
    score = np.clip((left_score + right_score)/2.0, 0.0, 1.0)
    return float(score)

def compute_dark_circles(image_bgr, landmarks, img_w, img_h):
    # Compare mean darkness / hue under eye vs cheek/lower face.
    left_eye_pts = get_landmark_points(landmarks, img_w, img_h, LEFT_EYE_IDX)
    right_eye_pts = get_landmark_points(landmarks, img_w, img_h, RIGHT_EYE_IDX)
    # Expand area below eye by offset
    def expand_pts(pts, dy=15):
        return [(x, y+dy) for (x,y) in pts]
    le_below = polygon_mask(image_bgr.shape, expand_pts(left_eye_pts, dy=18))
    re_below = polygon_mask(image_bgr.shape, expand_pts(right_eye_pts, dy=18))
    # cheek masks
    left_cheek = polygon_mask(image_bgr.shape, get_landmark_points(landmarks, img_w, img_h, LEFT_CHEEK_IDX))
    right_cheek = polygon_mask(image_bgr.shape, get_landmark_points(landmarks, img_w, img_h, RIGHT_CHEEK_IDX))
    # ensure mask shapes bool
    mask_eye = (le_below.astype(bool)) | (re_below.astype(bool))
    mask_cheek = (left_cheek.astype(bool)) | (right_cheek.astype(bool))
    lab = to_lab(image_bgr)
    L = lab[:,:,0].astype(np.float32)
    mean_eye_L = L[mask_eye].mean() if mask_eye.sum()>0 else 255.0
    mean_cheek_L = L[mask_cheek].mean() if mask_cheek.sum()>0 else 255.0
    # dark circles if eye area noticeably darker than cheek area
    diff = (mean_cheek_L - mean_eye_L) / 255.0
    return normalize01(diff * 2.0)

# ---------- Skin segmentation (simple heuristic) ----------
def simple_skin_mask_bgr(roi_bgr):
    # Simple skin color segmentation in YCrCb
    ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(ycrcb)
    mask = (Cr > 135) & (Cr < 180) & (Cb > 85) & (Cb < 135)
    mask = morphology.remove_small_objects(mask, min_size=100)
    return mask.astype(np.uint8)

# ---------- Main analysis pipeline ----------
def analyze_face_image(img_bgr, visualize=False):
    h, w = img_bgr.shape[:2]
    with mp_face.FaceMesh(static_image_mode=True,
                         max_num_faces=1,
                         refine_landmarks=False,
                         min_detection_confidence=0.5) as face_mesh:
        img_rgb = to_rgb(img_bgr)
        results = face_mesh.process(img_rgb)
        if not results.multi_face_landmarks:
            raise RuntimeError("Лицо не обнаружено")
        landmarks = results.multi_face_landmarks[0].landmark

    # Build masks for ROIs
    left_cheek_pts = get_landmark_points(landmarks, w, h, LEFT_CHEEK_IDX)
    right_cheek_pts = get_landmark_points(landmarks, w, h, RIGHT_CHEEK_IDX)
    nose_pts = get_landmark_points(landmarks, w, h, NOSE_IDX)
    forehead_pts = get_landmark_points(landmarks, w, h, FOREHEAD_IDX)
    chin_pts = get_landmark_points(landmarks, w, h, CHIN_IDX)

    left_cheek_mask = polygon_mask(img_bgr.shape, left_cheek_pts).astype(bool)
    right_cheek_mask = polygon_mask(img_bgr.shape, right_cheek_pts).astype(bool)
    nose_mask = polygon_mask(img_bgr.shape, nose_pts).astype(bool)
    forehead_mask = polygon_mask(img_bgr.shape, forehead_pts).astype(bool)
    chin_mask = polygon_mask(img_bgr.shape, chin_pts).astype(bool)
    # overall face mask = union of these masks (approx)
    face_mask = left_cheek_mask | right_cheek_mask | nose_mask | forehead_mask | chin_mask

    # ROIs cropped images for local ops: use bounding rects
    def crop_with_mask(mask_bool):
        ys, xs = np.where(mask_bool)
        if ys.size == 0:
            return None, None
        x0, x1 = xs.min(), xs.max()
        y0, y1 = ys.min(), ys.max()
        crop = img_bgr[y0:y1+1, x0:x1+1].copy()
        mask_crop = mask_bool[y0:y1+1, x0:x1+1].astype(np.uint8)
        return crop, mask_crop

    # left cheek crop
    lc_crop, lc_mask = crop_with_mask(left_cheek_mask)
    rc_crop, rc_mask = crop_with_mask(right_cheek_mask)
    nose_crop, nose_mask_crop = crop_with_mask(nose_mask)
    forehead_crop, forehead_mask_crop = crop_with_mask(forehead_mask)
    chin_crop, chin_mask_crop = crop_with_mask(chin_mask)
    # fallback if one side missing
    face_crop, face_mask_crop = crop_with_mask(face_mask)

    # skin mask for whole face (in crop coords): for most color ops
    # We'll compute simple skin mask per-ROI if available; otherwise use face approximate mask.
    # Compute metrics across combined cheek area if available
    # Compute pallor using cheeks first else face.
    skin_mask_cheeks = None
    cheeks_crop = None
    if lc_crop is not None and rc_crop is not None:
        # combine left+right cheek into one canvas
        # Simplest: analyze separately and average
        pallor_l = compute_paleness_lab(lc_crop, lc_mask)
        pallor_r = compute_paleness_lab(rc_crop, rc_mask)
        pallor = (pallor_l + pallor_r)/2.0
    elif face_crop is not None:
        # use face crop
        pallor = compute_paleness_lab(face_crop, face_mask_crop)
    else:
        pallor = 0.0

    # cyanosis and jaundice on nose+cheeks/face
    if face_crop is not None:
        cyanosis = compute_cyanosis(face_crop, face_mask_crop)
        jaundice = compute_jaundice(face_crop, face_mask_crop)
        redness = compute_redness(face_crop, face_mask_crop)
        pigmentation = compute_pigmentation(face_crop, face_mask_crop)
        vascularity = compute_vascularity(face_crop, face_mask_crop)
        oiliness = compute_oiliness(face_crop, face_mask_crop)
        acne = detect_spots_and_acne(face_crop, face_mask_crop)
    else:
        cyanosis = jaundice = redness = pigmentation = vascularity = oiliness = acne = 0.0

    puffiness = compute_puffiness(landmarks, w, h)
    dark_circles = compute_dark_circles(img_bgr, landmarks, w, h)

    metrics = {
        "paleness": normalize01(pallor),
        "cyanosis": normalize01(cyanosis),
        "jaundice": normalize01(jaundice),
        "redness": normalize01(redness),
        "acne_spots": normalize01(acne),
        "oiliness": normalize01(oiliness),
        "pigmentation": normalize01(pigmentation),
        "vascularity": normalize01(vascularity),
        "puffiness": normalize01(puffiness),
        "dark_circles": normalize01(dark_circles)
    }

    vis = None
    if visualize:
        vis = img_bgr.copy()
        def draw_poly(pts, color=(0,255,0)):
            arr = np.array(pts, np.int32).reshape((-1,1,2))
            cv2.polylines(vis, [arr], True, color, 2)
        draw_poly(left_cheek_pts); draw_poly(right_cheek_pts); draw_poly(nose_pts)
        draw_poly(forehead_pts); draw_poly(chin_pts)
        # overlay metrics
        y0 = 30
        for k,v in metrics.items():
            txt = f"{k}: {v:.2f}"
            cv2.putText(vis, txt, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
            y0 += 22

    return metrics, vis

if __name__ == "__main__":
    import sys
    img_path = sys.argv[1] if len(sys.argv) > 1 else "face.jpg"
    im = cv2.imread(img_path)
    if im is None:
        print("Не удалось открыть изображение:", img_path)
        sys.exit(1)
    metrics, vis = analyze_face_image(im, visualize=True)
    print("Metrics:")
    for k,v in metrics.items():
        print(f"  {k}: {v:.3f}")
    if vis is not None:
        cv2.imwrite("analysis_vis.jpg", vis)
        print("Saved visualization to analysis_vis.jpg")
