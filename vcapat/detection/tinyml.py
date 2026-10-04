"""Tiny deterministic ML beacon-candidate classifier.

The model is intentionally dependency-free (NumPy only).  It trains a logistic
classifier once from synthetic feature samples generated from the known beacon
candidate feature domain.  This makes the MVP self-contained while still
providing a genuine learned decision layer rather than hard-coded thresholding.

Features (all normalized to roughly 0..1): brightness, compactness, aspect
symmetry, area plausibility and prediction proximity.
"""
from __future__ import annotations
import numpy as np

class TinyMLBeaconClassifier:
    def __init__(self, seed: int = 26169, epochs: int = 220, lr: float = 0.18):
        self.seed=seed
        self.weights=np.zeros(5,dtype=np.float64)
        self.bias=0.0
        self._fit(epochs,lr)

    @staticmethod
    def _sigmoid(z):
        z=np.clip(z,-30,30)
        return 1.0/(1.0+np.exp(-z))

    def _fit(self,epochs,lr):
        rng=np.random.default_rng(self.seed)
        n=1800
        # Positive synthetic candidates resemble compact, bright beacon spots.
        pos=np.column_stack([
            rng.uniform(.58,1,n//2), rng.uniform(.40,1,n//2),
            rng.uniform(.58,1,n//2), rng.uniform(.35,1,n//2),
            rng.uniform(.45,1,n//2)])
        # Negatives model noise blobs, elongated streaks and distant distractors.
        neg=np.column_stack([
            rng.uniform(0,.78,n//2), rng.uniform(.05,.75,n//2),
            rng.uniform(.05,.78,n//2), rng.uniform(.02,.82,n//2),
            rng.uniform(0,.72,n//2)])
        X=np.vstack([pos,neg]); y=np.r_[np.ones(n//2),np.zeros(n//2)]
        order=rng.permutation(n);X=X[order];y=y[order]
        for _ in range(epochs):
            p=self._sigmoid(X@self.weights+self.bias)
            e=p-y
            self.weights-=lr*(X.T@e/n + .002*self.weights)
            self.bias-=lr*float(e.mean())

    def probability(self, brightness: float, compactness: float, shape: float,
                    area: float, distance: float | None, gate_px: float | None) -> float:
        bright=np.clip(brightness/180.0,0,1)
        compact=np.clip(compactness,0,1)
        symmetry=np.clip(shape,0,1)
        # Beacon blobs in this project are usually tens to a few hundred pixels.
        area_score=float(np.exp(-((np.clip(area,3,700)-90.0)/160.0)**2))
        if distance is None or gate_px is None or gate_px<=0:
            proximity=.65
        else:
            proximity=float(np.exp(-0.5*(distance/max(gate_px,1.0))**2))
        X=np.array([bright,compact,symmetry,area_score,proximity],dtype=np.float64)
        return float(self._sigmoid(X@self.weights+self.bias))

_model=None
def model():
    global _model
    if _model is None:_model=TinyMLBeaconClassifier()
    return _model
