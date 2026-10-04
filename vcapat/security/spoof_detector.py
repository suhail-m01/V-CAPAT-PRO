"""Candidate-consistency trust score; a heuristic, not authentication."""
import math

def trust_score(candidate,prediction=None,expected_brightness=None):
    score=float(candidate.get('score',0))
    if prediction is not None:score*=math.exp(-math.dist((candidate['x'],candidate['y']),prediction)**2/(2*40**2))
    if expected_brightness is not None:score*=math.exp(-abs(candidate.get('brightness',0)-expected_brightness)/100)
    return max(0.,min(1.,score))
