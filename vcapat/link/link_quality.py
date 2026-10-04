"""Illustrative Gaussian-beam pointing-loss proxy, not a calibrated link budget."""
import math

def quality_percent(pointing_error_px,confidence,atmosphere):
    if pointing_error_px is None:return min(100,max(0,confidence*75))
    attenuation={'clear':1.,'haze':.75,'fog':.43,'rain':.64,'low_light':.72,'turbulence':.76}[atmosphere]
    return min(100.,max(0.,100*math.exp(-(pointing_error_px/105)**2)*attenuation))
