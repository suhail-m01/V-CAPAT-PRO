"""Atmospheric scene degradations; Fourier warp is a visual approximation."""
import cv2
import numpy as np
from .noise import apply_noise

def apply_environment(image,config,rng,phase_screen):
    im=image;condition=config.atmosphere
    if condition=='haze':
        im=cv2.GaussianBlur(im,(5,5),1.1);im=cv2.convertScaleAbs(im,alpha=.70,beta=12)
    elif condition=='fog':
        im=cv2.GaussianBlur(im,(9,9),2.3);im=cv2.convertScaleAbs(im,alpha=.43,beta=15)
    elif condition=='low_light':im=cv2.convertScaleAbs(im,alpha=.38,beta=0)
    elif condition=='rain':
        im=im.copy();h,w=im.shape
        for _ in range(95):
            x=int(rng.integers(0,w));y=int(rng.integers(0,h))
            cv2.line(im,(x,y),(min(w-1,x+4),min(h-1,y+13)),int(rng.integers(28,75)),1)
    elif condition=='turbulence':
        h,w=im.shape;dx,dy=phase_screen.step(config.turbulence_r0)
        fx=cv2.resize(dx,(w,h));fy=cv2.resize(dy,(w,h))
        yy,xx=np.mgrid[:h,:w].astype('float32')
        im=cv2.remap(im,xx+fx,yy+fy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    # User-controlled reduction/offset required by the PS. Defaults are neutral,
    # so historical scenarios remain reproducible unless the user changes them.
    if config.contrast_scale!=1.0 or config.brightness_offset!=0.0:
        im=cv2.convertScaleAbs(im,alpha=float(config.contrast_scale),beta=float(config.brightness_offset))
    return apply_noise(im,config,rng)
