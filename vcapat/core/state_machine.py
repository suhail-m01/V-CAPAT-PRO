"""SEARCHING / ACQUIRING / LOCKED / COASTING / REACQUIRING transitions."""
import numpy as np
from ..tracking.kalman import Kalman

class Tracker:
    def __init__(self,hits_to_lock=3,coast_after=5,reacquire_after=20,process_noise=12.,measurement_noise=5.):
        self.hits_to_lock=hits_to_lock;self.coast_after=coast_after;self.reacquire_after=reacquire_after
        self.process_noise=process_noise;self.measurement_noise=measurement_noise
        self.kalman=Kalman(process_noise,measurement_noise);self.state='SEARCHING';self.hits=0;self.misses=0;self.first_lock=None
        self.lost_at=None;self.reacquisitions=[];self.losses=0;self.confidence=0.
    def step(self,detection,t,dt):
        prediction=self.kalman.predict(dt)
        if detection.found:
            if self.state=='REACQUIRING':
                # A long lost track can be far from the reacquired image spot.
                # Reset only from a real CV measurement, never simulator truth.
                self.kalman=Kalman(self.process_noise,self.measurement_noise)
            self.kalman.update(detection.x,detection.y);self.hits+=1;self.misses=0
            if self.state=='SEARCHING':self.state='ACQUIRING'
            if self.state in ('COASTING','REACQUIRING'):
                if self.lost_at is not None:self.reacquisitions.append(t-self.lost_at)
                self.lost_at=None;self.state='LOCKED';self.hits=self.hits_to_lock
            if self.state=='ACQUIRING' and self.hits>=self.hits_to_lock:
                self.state='LOCKED'
                if self.first_lock is None:self.first_lock=t
        else:
            self.hits=0;self.misses+=1
            if self.state=='LOCKED' and self.misses>=self.coast_after:
                self.state='COASTING';self.lost_at=t;self.losses+=1
            elif self.state=='COASTING' and self.misses>=self.reacquire_after:self.state='REACQUIRING'
            elif self.state=='ACQUIRING':self.state='SEARCHING'
        self.confidence=float(np.clip((.55+detection.confidence*.45 if detection.found else self.confidence*.89),0,1))
        return prediction

