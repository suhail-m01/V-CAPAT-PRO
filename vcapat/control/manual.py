"""Manual pan/tilt intent and bounded optional assist blending."""
from dataclasses import dataclass
import numpy as np

@dataclass
class ManualCommand:
    pan_deg_s:float=0.
    tilt_deg_s:float=0.
    assist_fraction:float=0.
    def blend(self,auto_pan,auto_tilt,limit):
        a=float(np.clip(self.assist_fraction,0,1))
        return tuple(float(np.clip(u*(1-a)+v*a,-limit,limit)) for u,v in zip((self.pan_deg_s,self.tilt_deg_s),(auto_pan,auto_tilt)))
