"""Transparent hand-designed score contributions (not SHAP)."""
import numpy as np

def candidate_contributions(area,brightness,shape,compactness,distance=None):
    terms={'area':.23*min(1.,area/20),'brightness':.39*min(1.,brightness/170),
           'aspect':.21*shape,'compactness':.17*compactness}
    terms['prediction_penalty']=min(.58,distance/300) if distance is not None else 0.
    terms['total']=float(np.clip(sum(terms[k] for k in ('area','brightness','aspect','compactness'))-terms['prediction_penalty'],0,1))
    return terms
