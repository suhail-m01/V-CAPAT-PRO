"""Context-managed OpenCV benchmark video with validated FPS and seeking."""
import cv2

class VideoSource:
    def __init__(self,path):
        self.cap=cv2.VideoCapture(str(path))
        if not self.cap.isOpened():raise ValueError(f'Cannot open benchmark video: {path}')
    @property
    def fps(self):return self.cap.get(cv2.CAP_PROP_FPS) or 30.
    @property
    def frame_count(self):return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
    def seek(self,index):
        index=max(0,min(int(index),max(0,self.frame_count-1)))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,index);return index
    def read(self):return self.cap.read()
    def close(self):self.cap.release()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
