"""Stable public data model imports for plugins and standalone clients."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
from ..config.settings import Scenario,WorldConfig,TargetConfig,CameraConfig,DisturbanceConfig,LinkConfig
from ..detection.base import Detection

@dataclass
class TrackState:
    x: float
    y: float
    vx: float
    vy: float
    covariance: np.ndarray
    lock_state: str
    lock_confidence: float

__all__=['Scenario','WorldConfig','TargetConfig','CameraConfig','DisturbanceConfig','LinkConfig','Detection','TrackState']
