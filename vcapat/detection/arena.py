"""Candidate extraction and algorithm selection."""
import cv2
import numpy as np
from .base import Detection
from . import adaptive_threshold,top_hat,template_match,optical_flow
from .centroiding import weighted_centroid
from .xai import candidate_contributions
from .tinyml import model as tinyml_model

class Detector:
    def __init__(self,mode='adaptive'):
        self.mode=mode; self.previous=None; self.point=None

    def detect(self,frame,prediction=None,gate_px=None):
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY) if frame.ndim==3 else frame
        mode=self.mode
        ai_mode=mode in ('tinyml','ai_auto')
        if mode in ('auto','ai_auto'):
            _, scene_std = cv2.meanStdDev(gray)
            mode='top_hat' if float(scene_std[0,0])>25 else 'adaptive'
        elif mode=='tinyml': mode='adaptive'
        if mode=='optical_flow':
            found=optical_flow.track(self.previous,gray,self.point,prediction,gate_px)
            if found is not None:
                self.previous=gray.copy();self.point=(found.x,found.y)
                return found
        smooth=cv2.GaussianBlur(gray,(5,5),.9)
        if mode=='top_hat':mask=top_hat.threshold_mask(smooth)
        elif mode=='template':mask=template_match.threshold_mask(smooth)
        else:mask=adaptive_threshold.threshold_mask(smooth)
        n,labels,stats,centers=cv2.connectedComponentsWithStats(mask,8)
        candidates=[]; best=None; bestscore=-1
        for i in range(1,n):
            x,y,w,h,area=map(int,stats[i])
            if area<3 or area>700 or w>48 or h>48 or min(w,h)<2:continue
            box=gray[y:y+h,x:x+w].astype('float32')
            base=float(np.median(gray[max(0,y-8):min(gray.shape[0],y+h+8),max(0,x-8):min(gray.shape[1],x+w+8)]))
            bright=float(box.max()-base)
            if bright<15:continue
            centroid=weighted_centroid(box,x,y,base)
            if centroid is None:continue
            cx,cy=centroid
            shape=min(w,h)/max(w,h)
            compactness=float(area/(w*h))
            dist=float(np.hypot(cx-prediction[0],cy-prediction[1])) if prediction is not None else None
            contributions=candidate_contributions(area,bright,shape,compactness,dist)
            heuristic=float(contributions['total'])
            ml_prob=tinyml_model().probability(bright,compactness,shape,area,dist,gate_px) if ai_mode else None
            score=(0.52*heuristic+0.48*ml_prob) if ml_prob is not None else heuristic
            if ml_prob is not None: contributions['tinyml_probability']=float(ml_prob)
            contributions['total']=float(score)
            dist=0. if dist is None else dist
            candidate={'x':round(cx,2),'y':round(cy,2),'score':round(max(0,score),3),'area':area,'brightness':round(bright,1),'distance':round(dist,1),'bbox':(x,y,w,h),'ml_probability':round(ml_prob,3) if ml_prob is not None else None,'contributions':{k:round(v,3) for k,v in contributions.items()}}
            candidates.append(candidate)
            if (gate_px is None or prediction is None or dist<=gate_px) and score>bestscore:
                bestscore=score;best=(cx,cy,(x,y,w,h))
        candidates.sort(key=lambda k:k['score'],reverse=True)
        self.previous=gray.copy()
        if best is None or bestscore<.28:
            self.point=None
            return Detection(candidates=candidates[:15],debug=mask)
        self.point=(best[0],best[1])
        return Detection(best[0],best[1],float(np.clip(bestscore,0,1)),best[2],candidates[:15],mask)

