"""Bright small-scale features relative to morphological background."""
import cv2
import numpy as np

_TOPHAT_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
_OPEN_KERNEL = np.ones((2, 2), np.uint8)


def threshold_mask(smooth):
    feature = cv2.morphologyEx(smooth, cv2.MORPH_TOPHAT, _TOPHAT_KERNEL)
    mean, std = cv2.meanStdDev(feature)
    threshold = max(14.0, float(mean[0, 0] + 3.0 * std[0, 0]))
    _, binary = cv2.threshold(feature, threshold, 1, cv2.THRESH_BINARY)
    return cv2.morphologyEx(binary, cv2.MORPH_OPEN, _OPEN_KERNEL)
