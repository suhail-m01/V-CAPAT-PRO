"""Adaptive global-background threshold with morphological impulse rejection."""
import cv2
import numpy as np

_KERNEL = np.ones((2, 2), np.uint8)


def _median_u8(image):
    """Fast deterministic median for an 8-bit image using a 256-bin histogram."""
    hist = cv2.calcHist([image], [0], None, [256], [0, 256]).ravel()
    return float(np.searchsorted(np.cumsum(hist), image.size * 0.5))


def threshold_mask(smooth):
    median = _median_u8(smooth)
    _, std = cv2.meanStdDev(smooth)
    threshold = max(29.0, median + 3.2 * float(std[0, 0]))
    _, binary = cv2.threshold(smooth, threshold, 1, cv2.THRESH_BINARY)
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, _KERNEL)
