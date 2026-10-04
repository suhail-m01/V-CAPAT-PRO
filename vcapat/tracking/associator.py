"""Prediction-gated candidate association without truth access."""
import math

def choose_candidate(candidates,prediction=None,max_distance=None):
    eligible=[c for c in candidates if prediction is None or max_distance is None or math.dist((c['x'],c['y']),prediction)<=max_distance]
    return max(eligible,key=lambda c:c['score'],default=None)
