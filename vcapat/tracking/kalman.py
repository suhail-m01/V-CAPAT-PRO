"""Constant-velocity Kalman filter with pixel-domain covariance."""
import numpy as np

class Kalman:
    def __init__(self,process_noise=12.,measurement_noise=5.):
        self.state=None;self.P=np.eye(4)*40;self.process_noise=process_noise;self.measurement_noise=measurement_noise
    def predict(self,dt):
        if self.state is None:return None
        F=np.array([[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]],float)
        q=self.process_noise; G=np.array([[dt*dt/2,0],[0,dt*dt/2],[dt,0],[0,dt]])
        self.state=F@self.state;self.P=F@self.P@F.T+q*(G@G.T)+np.eye(4)*.03
        return self.state[:2].copy()
    def update(self,x,y):
        z=np.array([x,y],float)
        if self.state is None:self.state=np.array([x,y,0,0],float);return self.state.copy()
        H=np.array([[1,0,0,0],[0,1,0,0]],float);S=H@self.P@H.T+np.eye(2)*self.measurement_noise
        K=self.P@H.T@np.linalg.inv(S);self.state=self.state+K@(z-H@self.state)
        self.P=(np.eye(4)-K@H)@self.P
        return self.state.copy()

