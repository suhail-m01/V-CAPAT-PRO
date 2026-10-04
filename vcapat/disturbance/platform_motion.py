"""Platform displacement patterns, measured in scene pixels."""
import math

def platform_offset(pattern,amplitude,time_s,rng):
    a,t=amplitude,time_s
    if pattern=='linear':return a*math.sin(t*.4),0.
    if pattern=='circular':return a*math.cos(t),a*math.sin(t)
    if pattern=='sinusoidal':return a*math.sin(t*2),a*math.sin(t*1.2)
    if pattern=='random':return tuple(float(v) for v in rng.uniform(-a,a,2))
    if pattern=='figure8':return a*math.sin(t),a*math.sin(2*t)*.5
    return 0.,0.
