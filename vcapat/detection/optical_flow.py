"""Tracked-feature Lucas–Kanade flow with brightness and association checks."""
import cv2
import numpy as np
from .base import Detection

def track(previous,current,point,prediction=None,gate_px=None):
    if previous is None or point is None:return None
    pts=np.array([[point]],dtype=np.float32)
    updated,status,_=cv2.calcOpticalFlowPyrLK(previous,current,pts,None,winSize=(23,23))
    if status is None or not status[0,0]:return None
    x,y=map(float,updated[0,0]);h,w=current.shape
    if not 0<=x<w or not 0<=y<h:return None
    if prediction is not None and gate_px is not None and np.hypot(x-prediction[0],y-prediction[1])>gate_px:return None
    local=current[max(0,int(y)-4):min(h,int(y)+5),max(0,int(x)-4):min(w,int(x)+5)]
    if local.size and local.max()>max(34,float(np.median(current))+23):
        return Detection(x,y,.70,(int(x)-5,int(y)-5,10,10))
    return None
