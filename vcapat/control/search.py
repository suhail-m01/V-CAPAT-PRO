"""Rate-limited world-search steering commands. Angles are degrees."""
import math
import numpy as np

def search_velocity(t,limit,pattern='spiral',seed=0):
    if pattern=='spiral':return limit*.25*math.sin(t*2.5),limit*.25*math.cos(t*2.5)
    if pattern=='raster':return (limit*.4 if int(t/2)%2==0 else -limit*.4),(.08*limit if (t%2)<.2 else 0.)
    if pattern=='random':
        rng=np.random.default_rng(seed+int(t*4));return tuple(float(v) for v in rng.uniform(-limit*.25,limit*.25,2))
    raise ValueError(f'Unknown search pattern: {pattern}')
