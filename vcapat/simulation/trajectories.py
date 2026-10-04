"""Deterministic target motion in world pixels; seeded random walk is integrated per frame."""
import math
import numpy as np

class Trajectory:
    def __init__(self, config, world, seed=42, offset=0):
        self.c, self.world = config, world
        self.rng = np.random.default_rng(seed+offset*101)
        if config.initial_mode=='random':
            base=(self.rng.uniform(50,world.width-50),self.rng.uniform(50,world.height-50))
        elif config.initial_mode=='center':base=(world.width/2,world.height/2)
        else:base=config.initial_position
        self.x0 = float(base[0]) + offset*54
        self.y0 = float(base[1]) + offset*35
        self.x, self.y = self.x0, self.y0
        self.offset = offset

    def step(self,t,dt):
        c=self.c; v=c.speed_pps; w=v/100.; phase=self.offset*.75
        x0,y0=self.x0,self.y0
        match c.trajectory:
            case 'straight': x,y=x0+v*t*.66,y0+v*t*.33
            case 'circular': x,y=x0+105*(math.cos(w*t+phase)-math.cos(phase)),y0+105*(math.sin(w*t+phase)-math.sin(phase))
            case 'figure8': x,y=x0+145*(math.sin(w*t+phase)-math.sin(phase)),y0+76*(math.sin(2*w*t+phase)-math.sin(phase))
            case 'random':
                x,y=self.x+self.rng.normal(0,v*dt*.8),self.y+self.rng.normal(0,v*dt*.8)
            case 'spiral':
                a=12+min(t*7,230); x,y=x0+a*math.cos(w*t+phase)-12*math.cos(phase),y0+a*math.sin(w*t+phase)-12*math.sin(phase)
            case 'sinusoidal': x,y=x0+v*t*.55,y0+70*math.sin(w*t+phase)-70*math.sin(phase)
            case 'leo': x,y=x0+v*1.2*t,y0+90*(math.sin(t*.22+phase)-math.sin(phase))
            case 'uav': x,y=x0+50*math.sin(t*.27+phase)-50*math.sin(phase),y0+40*math.sin(t*.41+phase)-40*math.sin(phase)
            case 'haps': x,y=x0+v*.08*t,y0+15*math.sin(t*.08+phase)-15*math.sin(phase)
            case 'aircraft': x,y=x0+v*.7*t,y0+60*math.sin(t*.2+phase)-60*math.sin(phase)
            case _: x,y=x0+v*.01*t,y0+v*.006*t
        # Bouncing triangle wave keeps motion smooth across world boundaries.
        margin=15
        def bounce(z,limit):
            span=max(1,limit-2*margin); q=(z-margin)%(span*2)
            return margin+(q if q<=span else span*2-q)
        if c.boundary=='wrap':self.x,self.y=x%self.world.width,y%self.world.height
        else:self.x,self.y=bounce(x,self.world.width),bounce(y,self.world.height)
        return self.x,self.y
