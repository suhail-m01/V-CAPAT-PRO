"""Public plugin interfaces. Plugins are Python code: load trusted files only."""
from typing import Protocol
import numpy as np
from ..detection.base import Detection

class DetectorPlugin(Protocol):
    def detect(self,frame:np.ndarray,prediction=None,gate_px=None)->Detection: ...

class ControllerPlugin(Protocol):
    def step(self,error_x_deg:float,error_y_deg:float,dt:float,limit_deg_s:float)->tuple[float,float]: ...
