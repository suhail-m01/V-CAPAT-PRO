"""Dual-axis speed-limited PID primitive with anti-windup."""
import numpy as np

class PID:
    def __init__(self,kp=10.0,ki=.3,kd=.12,limit=5.,deadband=.0015):
        self.kp=kp;self.ki=ki;self.kd=kd;self.limit=limit;self.integral=0.;self.prev=None;self.deadband=deadband
    def step(self,error,dt):
        if abs(error)<self.deadband:error=0.
        derivative=0. if self.prev is None else (error-self.prev)/max(dt,.001)
        self.prev=error
        tentative=np.clip(self.integral+error*dt,-self.limit/max(self.ki,.01),self.limit/max(self.ki,.01))
        raw=self.kp*error+self.ki*tentative+self.kd*derivative
        if abs(raw)<self.limit or np.sign(raw)!=np.sign(error):self.integral=tentative
        return float(np.clip(self.kp*error+self.ki*self.integral+self.kd*derivative,-self.limit,self.limit))
