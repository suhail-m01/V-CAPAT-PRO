"""Intensity-weighted subpixel centroid on a bounded grayscale ROI."""
import numpy as np

def weighted_centroid(box,x,y,baseline):
    weights=np.maximum(box.astype('float32')-baseline,0)**1.4
    total=float(weights.sum())
    if total<1:return None
    yy,xx=np.mgrid[y:y+box.shape[0],x:x+box.shape[1]]
    return float((xx*weights).sum()/total),float((yy*weights).sum()/total)
