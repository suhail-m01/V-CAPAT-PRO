"""Human image-space designation and post-decision evaluation matching."""
import math

def image_candidate_at(candidates,x,y,tolerance_px=25):
    if not candidates:return None
    best=min(candidates,key=lambda c:math.dist((c['x'],c['y']),(x,y)))
    return best if math.dist((best['x'],best['y']),(x,y))<=tolerance_px else None

def truth_identity_for_evaluation(x,y,truths,tolerance_px=18):
    matches=[(math.dist((x,y),(tx,ty)),index) for index,(tx,ty,visible) in enumerate(truths) if visible]
    if not matches:return None
    distance,index=min(matches)
    return index if distance<=tolerance_px else None
