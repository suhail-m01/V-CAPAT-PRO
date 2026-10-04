"""Example trusted detector: bright compact blobs, no simulator truth."""
import cv2
import numpy as np
from vcapat.detection.base import Detection

PLUGIN_KIND='detector'

class ExampleDetector:
    def detect(self,frame,prediction=None,gate_px=None):
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) if frame.ndim==3 else frame
        smooth=cv2.GaussianBlur(gray,(5,5),1)
        threshold=max(32,float(np.median(smooth)+4*smooth.std()))
        n,labels,stats,centroids=cv2.connectedComponentsWithStats((smooth>threshold).astype('uint8'),8)
        best=None
        for i in range(1,n):
            x,y,w,h,area=map(int,stats[i])
            if not 5<=area<=300 or w>35 or h>35:continue
            cx,cy=map(float,centroids[i])
            distance=0 if prediction is None else float(np.hypot(cx-prediction[0],cy-prediction[1]))
            if gate_px is not None and prediction is not None and distance>gate_px:continue
            score=min(1.,(float(gray[y:y+h,x:x+w].max())-float(np.median(gray)))/220)-distance/350
            if best is None or score>best.confidence:best=Detection(cx,cy,max(0.,score),(x,y,w,h))
        return best or Detection()

PLUGIN_CLASS=ExampleDetector
