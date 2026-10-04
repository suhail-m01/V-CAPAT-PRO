"""Pixelized Gaussian, Airy-like, square and circular optical beacon profiles."""
import numpy as np

def draw_beacon(im,x,y,size,brightness,shape):
    # `size` may be a scalar for backward compatibility or [width,height].
    if isinstance(size,(tuple,list)):
        rw=max(3,int(size[0])//2); rh=max(3,int(size[1])//2)
    else:
        rw=rh=max(3,int(size)//2)
    ix=int(round(x)); iy=int(round(y))
    xa=max(0,ix-rw*3); xb=min(im.shape[1],ix+rw*3+1)
    ya=max(0,iy-rh*3); yb=min(im.shape[0],iy+rh*3+1)
    if xa>=xb or ya>=yb:return
    yy,xx=np.mgrid[ya:yb,xa:xb]
    ex=(xx-x)/max(rw,1); ey=(yy-y)/max(rh,1); rrn=ex**2+ey**2
    if shape=='square': intensity=np.where((abs(xx-x)<=rw)&(abs(yy-y)<=rh),brightness,0)
    elif shape=='circle': intensity=np.where(rrn<=1,brightness,0)
    elif shape=='airy':
        z=np.sqrt(rrn)/.7; intensity=brightness*(np.sinc(z)**2)
    else: intensity=brightness*np.exp(-rrn/(2*(.55**2)))
    roi=im[ya:yb,xa:xb]; np.maximum(roi,np.uint8(np.clip(intensity,0,255)),out=roi)

