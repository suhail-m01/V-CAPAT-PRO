"""Seeded point-source star clutter rendered once, before camera sampling."""
import numpy as np

def render_star_field(image:np.ndarray,density:float,rng:np.random.Generator)->np.ndarray:
    if not 0<=density<=.01:raise ValueError('star density must be between 0 and .01')
    height,width=image.shape[:2]
    count=int(height*width*density)
    if count:
        xs=rng.integers(0,width,count);ys=rng.integers(0,height,count)
        image[ys,xs]=rng.integers(25,115,count,dtype=np.uint8)
    return image
