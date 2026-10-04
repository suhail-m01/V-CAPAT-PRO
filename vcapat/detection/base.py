"""Detection result and detector protocol."""
from dataclasses import dataclass,field
from typing import Protocol
import numpy as np

@dataclass
class Detection:
    x: float=0.
    y: float=0.
    confidence: float=0.
    bbox: tuple=(0,0,0,0)
    candidates: list=field(default_factory=list)
    debug: object=None
    @property
    def found(self): return self.confidence>0


class DetectorProtocol(Protocol):
    def detect(self,frame:np.ndarray,prediction=None,gate_px=None)->Detection: ...
