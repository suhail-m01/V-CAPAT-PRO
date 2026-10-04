"""Gaussian-kernel correlation for roughly point-shaped beacons."""
import cv2
import numpy as np

def threshold_mask(smooth):
    yy,xx=np.mgrid[-5:6,-5:6]
    kernel=np.exp(-(xx*xx+yy*yy)/(2*2.1**2)).astype('float32');kernel-=kernel.mean()
    response=cv2.filter2D(smooth.astype('float32'),-1,kernel)
    response=cv2.normalize(response,None,0,255,cv2.NORM_MINMAX).astype('uint8')
    threshold=max(90,float(response.mean()+3*response.std()))
    return cv2.morphologyEx((response>threshold).astype('uint8'),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
