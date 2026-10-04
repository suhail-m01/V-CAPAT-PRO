"""Deterministic world raster and camera ROI sampling."""
import cv2
import numpy as np
from .star_field import render_star_field

class World:
    def __init__(self,c):
        self.c=c; rng=np.random.default_rng(c.seed)
        if c.background=='sky':
            line=np.linspace(36,70,c.height,dtype=np.uint8)[:,None]
            self.image=np.repeat(line,c.width,axis=1)
        else: self.image=np.full((c.height,c.width),8 if c.background=='deep_space' else c.solid_gray,np.uint8)
        render_star_field(self.image,c.star_density,rng)

    def view(self,cx,cy,w,h):
        # Affine remap with a dark constant border. Camera centre is independent of world origin.
        matrix=np.float32([[1,0,cx-w/2],[0,1,cy-h/2]])
        return cv2.warpAffine(self.image,matrix,(w,h),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=5)

