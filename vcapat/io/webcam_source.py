"""Opt-in local camera device enumeration and capture."""
import cv2

def enumerate_webcams(max_devices=5):
    found=[]
    for index in range(max_devices):
        cap=cv2.VideoCapture(index)
        if cap.isOpened():found.append(index)
        cap.release()
    return found

def open_webcam(index=0):
    capture=cv2.VideoCapture(index)
    if not capture.isOpened():raise ValueError(f'Cannot open webcam {index}')
    return capture
