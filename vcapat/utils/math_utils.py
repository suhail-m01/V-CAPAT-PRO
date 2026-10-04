"""Numerical helpers for scored benchmark runs."""
import math

def root_mean_square(values):
    data=[float(v) for v in values if v is not None]
    return math.sqrt(sum(v*v for v in data)/len(data)) if data else None

def clamp(value,lower,upper):return max(lower,min(upper,value))
