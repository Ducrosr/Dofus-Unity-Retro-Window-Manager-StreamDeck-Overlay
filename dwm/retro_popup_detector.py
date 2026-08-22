from __future__ import annotations

import numpy as np

"""
Retro popup detector (Groupe / Échange) for Dofus Retro.

Robustness goals:
- tolerate UI scale / aspect ratio shifts
- no OCR / no OpenCV dependency
- fast enough for several stacked windows

Approach:
- Look for the "Oui / Non" buttons area using a perceptual hash (dHash)
- Try a small 3x3 jitter grid around the expected center ROI
- Use a cheap orange-ish pixel ratio as a pre-filter
"""

BASE_BUTTONS_ROI = (0.33, 0.67, 0.38, 0.58)  # (x1,x2,y1,y2) fractions

JITTER_X = (-0.02, 0.0, 0.02)
JITTER_Y = (-0.02, 0.0, 0.02)

TEMPLATE_BUTTONS_HASH = 1175529319918776402

MAX_HAMMING_BUTTONS = 20
THR_ORANGE = 0.015


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _roi_shift(roi: tuple[float, float, float, float], dx: float, dy: float) -> tuple[float, float, float, float]:
    x1, x2, y1, y2 = roi
    return (_clamp01(x1 + dx), _clamp01(x2 + dx), _clamp01(y1 + dy), _clamp01(y2 + dy))


def _crop_frac(frame_bgr: np.ndarray, roi: tuple[float, float, float, float]) -> np.ndarray:
    h, w, _ = frame_bgr.shape
    x1, x2, y1, y2 = roi
    X1 = int(w * x1)
    X2 = int(w * x2)
    Y1 = int(h * y1)
    Y2 = int(h * y2)
    if X2 <= X1 or Y2 <= Y1:
        return frame_bgr[0:0, 0:0, :]
    return frame_bgr[Y1:Y2, X1:X2]


def _to_gray(roi_bgr: np.ndarray) -> np.ndarray:
    b = roi_bgr[:, :, 0].astype(np.float32)
    g = roi_bgr[:, :, 1].astype(np.float32)
    r = roi_bgr[:, :, 2].astype(np.float32)
    return 0.114 * b + 0.587 * g + 0.299 * r


def _resize_nn(gray: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    h, w = gray.shape
    if h <= 1 or w <= 1:
        return np.zeros((out_h, out_w), dtype=np.float32)
    ys = (np.linspace(0, h - 1, out_h)).astype(np.int32)
    xs = (np.linspace(0, w - 1, out_w)).astype(np.int32)
    return gray[ys][:, xs]


def _dhash(gray: np.ndarray, hash_size: int = 8) -> int:
    small = _resize_nn(gray, hash_size, hash_size + 1)
    diff = small[:, 1:] > small[:, :-1]
    val = 0
    for bit in diff.flatten():
        val = (val << 1) | int(bool(bit))
    return int(val)


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def _orange_ratio(roi_bgr: np.ndarray) -> float:
    roi = roi_bgr[::6, ::6, :]
    if roi.size == 0:
        return 0.0
    b = roi[:, :, 0].astype(np.int16)
    g = roi[:, :, 1].astype(np.int16)
    r = roi[:, :, 2].astype(np.int16)
    orange = (r > 160) & (g > 70) & (b < 190) & (r > g) & (g > b)
    return float(orange.mean())


def detect_retro_modal_popup(frame_bgr: np.ndarray) -> bool:
    if frame_bgr is None or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        return False
    h, w, _ = frame_bgr.shape
    if h < 200 or w < 200:
        return False

    best = 999
    for dx in JITTER_X:
        for dy in JITTER_Y:
            roi = _roi_shift(BASE_BUTTONS_ROI, dx, dy)
            buttons = _crop_frac(frame_bgr, roi)
            if buttons.size == 0:
                continue
            if _orange_ratio(buttons) < THR_ORANGE:
                continue
            try:
                bh = _dhash(_to_gray(buttons), 8)
                d = _hamming(bh, TEMPLATE_BUTTONS_HASH)
                if d < best:
                    best = d
            except Exception:
                continue
    return best <= MAX_HAMMING_BUTTONS
