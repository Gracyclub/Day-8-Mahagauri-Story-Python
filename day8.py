import cv2
import numpy as np
import ctypes
import math
import os

# Integrity verification
author = "gracy_builds"
_checksum = sum(bytearray(author, "utf-8"))
assert _checksum == 1272, "Checksum mismatch: unauthorized modification."

try:
    user32 = ctypes.windll.user32
    screen_w, screen_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
except Exception:
    screen_w, screen_h = 1920, 1080

def load_image(base_name):
    for ext in [".png", ".jpg", ".jpeg"]:
        file_path = f"{base_name}{ext}"
        if os.path.exists(file_path):
            img = cv2.imread(file_path)
            if img is not None:
                return img
    return None

# Load source frames
raw_dark = load_image("mahagauri_scene_1")
raw_half = load_image("mahagauri_scene_2")
raw_full = load_image("mahagauri_scene_3")

if raw_dark is None or raw_full is None:
    raise FileNotFoundError("Missing files: Ensure mahagauri_scene_1 and mahagauri_scene_3 exist in the directory.")

if raw_half is None:
    raw_half = raw_full

WIDTH, HEIGHT = 1060, 600
frame_dark = cv2.resize(raw_dark, (WIDTH, HEIGHT))
frame_half = cv2.resize(raw_half, (WIDTH, HEIGHT))
frame_full = cv2.resize(raw_full, (WIDTH, HEIGHT))

window_name = "Maa Mahagauri Abhishek - Devotional Motion Sequence"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, WIDTH, HEIGHT)
cv2.moveWindow(window_name, (screen_w - WIDTH) // 2, max(10, (screen_h - HEIGHT) // 2 - 30))

def render_watermark(target_canvas):
    label = f"code by {author}"
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    scale = 0.75
    thickness = 2
    (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)
    
    # Position at bottom-center
    pos_x = (WIDTH - tw) // 2
    pos_y = HEIGHT - 20
    
    # Soft translucent background plate
    overlay = target_canvas.copy()
    cv2.rectangle(overlay, (pos_x - 14, pos_y - th - 8), (pos_x + tw + 14, pos_y + baseline + 6), (10, 10, 12), -1)
    cv2.addWeighted(overlay, 0.40, target_canvas, 0.60, 0, target_canvas)
    
    # Rich golden cursive script
    cv2.putText(target_canvas, label, (pos_x, pos_y), font, scale, (0, 215, 255), thickness, cv2.LINE_AA)

# -------------------------------------------------------------
# STRICT SHIVA CUTOUT (Excluding Mata Parvati's Body)
# -------------------------------------------------------------
delta = cv2.absdiff(frame_half, frame_dark)
delta_gray = cv2.cvtColor(delta, cv2.COLOR_BGR2GRAY)

# Restrict exclusively to Shiva's boundary (Cutoff before Mata's hand/knee)
roi_mask = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
shiva_strict_poly = np.array([
    [0, int(HEIGHT * 0.15)],
    [int(WIDTH * 0.20), int(HEIGHT * 0.08)],
    [int(WIDTH * 0.36), int(HEIGHT * 0.03)],
    [int(WIDTH * 0.54), int(HEIGHT * 0.12)],
    [int(WIDTH * 0.58), int(HEIGHT * 0.28)],  # Lota edge
    [int(WIDTH * 0.49), int(HEIGHT * 0.44)],  # Strict cutoff above Mata's hand
    [int(WIDTH * 0.44), int(HEIGHT * 0.70)],  # Cutoff before Mata's knee
    [int(WIDTH * 0.43), HEIGHT],
    [0, HEIGHT]
], np.int32)
cv2.fillPoly(roi_mask, [shiva_strict_poly], 255)
delta_gray = cv2.bitwise_and(delta_gray, roi_mask)

_, raw_alpha = cv2.threshold(delta_gray, 20, 255, cv2.THRESH_BINARY)
morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
raw_alpha = cv2.morphologyEx(raw_alpha, cv2.MORPH_CLOSE, morph_kernel)
raw_alpha = cv2.dilate(raw_alpha, morph_kernel, iterations=1)

# Feathering for seamless blending
feathered_alpha = cv2.GaussianBlur(raw_alpha.astype(np.float32) / 255.0, (15, 15), 0)
alpha_3c = np.repeat(feathered_alpha[:, :, np.newaxis], 3, axis=2)

shiva_cutout = frame_half.copy()

# -------------------------------------------------------------
# PHASE 1: NATURAL SLIDE-IN OF LORD SHIVA ALONE
# -------------------------------------------------------------
slide_frames = 60
shift_width = int(WIDTH * 0.56)

for i in range(slide_frames):
    progress = i / float(slide_frames - 1)
    ease = 1.0 - math.pow(1.0 - progress, 3)
    offset_x = int((1.0 - ease) * (-shift_width))
    
    canvas = frame_dark.copy()
    
    matrix = np.float32([[1, 0, offset_x], [0, 1, 0]])
    shifted_shiva = cv2.warpAffine(shiva_cutout, matrix, (WIDTH, HEIGHT))
    shifted_alpha = cv2.warpAffine(alpha_3c, matrix, (WIDTH, HEIGHT))
    
    canvas = (canvas * (1.0 - shifted_alpha) + shifted_shiva * shifted_alpha).astype(np.uint8)
    
    render_watermark(canvas)
    cv2.imshow(window_name, canvas)
    if cv2.waitKey(16) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        exit()

# -------------------------------------------------------------
# PHASE 2: NATURAL WATERFALL & CONTINUOUS ORGANIC DISSOLVE
# -------------------------------------------------------------
lota_x, lota_y = int(WIDTH * 0.54), int(HEIGHT * 0.20)
maa_head_x, maa_head_y = int(WIDTH * 0.655), int(HEIGHT * 0.35)

y_grid, x_grid = np.indices((HEIGHT, WIDTH))

class SoftDroplet:
    def __init__(self):
        self.spawn()
    def spawn(self):
        self.x = lota_x + np.random.uniform(16, 32)
        self.y = lota_y + np.random.uniform(4, 12)
        self.vy = np.random.uniform(6.0, 11.0)
        self.vx = np.random.uniform(0.7, 1.7)
        self.length = np.random.randint(5, 10)

droplets = [SoftDroplet() for _ in range(95)]
for d in droplets:
    d.y = lota_y + np.random.uniform(0, 180)

wash_frames = 180

for f in range(wash_frames):
    progress = f / float(wash_frames - 1)
    
    # Continuous radial expansion from head down to entire body
    expansion_dist = np.sqrt(((x_grid - maa_head_x) * 1.0)**2 + ((y_grid - maa_head_y) * 1.2)**2)
    current_reach = progress * 460.0
    cleansed_field = np.clip((current_reach - expansion_dist) / 65.0, 0.0, 1.0)
    cleansed_3c = np.repeat(cleansed_field[:, :, np.newaxis], 3, axis=2)
    
    # Seamless transition directly from dark tapasya to radiant Mahagauri
    blended_body = (frame_dark * (1.0 - cleansed_3c) + frame_full * cleansed_3c).astype(np.uint8)
    
    # Keep Shiva static and solid
    canvas = (blended_body * (1.0 - alpha_3c) + frame_half * alpha_3c).astype(np.uint8)
    
    # Natural translucent water droplets
    for drop in droplets:
        drop.y += drop.vy
        drop.x += drop.vx
        drop.vy += 0.30
        
        impact_bound = int(maa_head_y + (progress * 240) + 20)
        if drop.y >= impact_bound or drop.y >= HEIGHT - 50:
            if 0 <= int(drop.x) < WIDTH and 0 <= int(drop.y) < HEIGHT:
                cv2.circle(canvas, (int(drop.x), int(drop.y)), 2, (255, 255, 255), -1)
                cv2.circle(canvas, (int(drop.x + np.random.randint(-4, 4)), int(drop.y)), 1, (220, 240, 255), -1)
            drop.spawn()
            
        ix, iy = int(drop.x), int(drop.y)
        if 0 <= ix < WIDTH and 0 <= iy + drop.length < HEIGHT:
            cv2.line(canvas, (ix, iy), (ix, iy + drop.length), (255, 250, 235), 1, cv2.LINE_AA)
            
    render_watermark(canvas)
    cv2.imshow(window_name, canvas)
    if cv2.waitKey(16) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        exit()

# -------------------------------------------------------------
# PHASE 3: DIVINE GOLDEN HALO & RADIANT CLIMAX
# -------------------------------------------------------------
halo_layer = np.zeros_like(frame_full, dtype=np.uint8)
cv2.circle(halo_layer, (maa_head_x + 10, maa_head_y - 25), 220, (50, 215, 255), -1)
halo_layer = cv2.GaussianBlur(halo_layer, (141, 141), 0)
climax_frame = cv2.addWeighted(frame_full, 0.88, halo_layer, 0.38, 0)

flash_matrix = np.full_like(frame_full, 255)
for intensity in np.linspace(0.80, 0, 12):
    lit_canvas = cv2.addWeighted(climax_frame, 1.0 - intensity, flash_matrix, intensity, 0)
    render_watermark(lit_canvas)
    cv2.imshow(window_name, lit_canvas)
    cv2.waitKey(16)

render_watermark(climax_frame)
cv2.imshow(window_name, climax_frame)
cv2.waitKey(0)
cv2.destroyAllWindows()