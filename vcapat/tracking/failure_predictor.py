"""Transparent error-trend early warning; not a trained failure classifier."""
import numpy as np

def warning_probability(pointing_errors,window=30):
    data=np.array([e for e in pointing_errors[-window:] if e is not None],float)
    if len(data)<5:return 0.
    slope=float(np.polyfit(np.arange(len(data)),data,1)[0])
    # Rising error and proximity to the ten-pixel budget increase concern.
    return float(np.clip(max(0,slope)/2 + max(0,float(np.mean(data[-5:]))-6)/10,0,1))
