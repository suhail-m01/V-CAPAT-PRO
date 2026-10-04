"""Virtual pan-tilt FPA ROI and time-stepped scene composition."""
import math
import numpy as np
import cv2
from ..disturbance.sensor_physics import expose
from .world import World
from .trajectories import Trajectory
from .occlusion import cloud_visible
from .target import draw_beacon
from ..disturbance.platform_motion import platform_offset
from ..disturbance.jitter import sample_jitter
from ..disturbance.atmosphere import apply_environment
from ..disturbance.turbulence import PhaseScreen

class Simulator:
    _draw_beacon=staticmethod(draw_beacon)  # public compatibility for synthetic tests
    def __init__(self,config):
        self.c=config; self.world=World(config.world); self.rng=np.random.default_rng(config.seed)
        self.targets=[Trajectory(config.target,config.world,config.seed,i) for i in range(config.target.count)]
        self.pan=float(config.camera.initial_pan_deg); self.tilt=float(config.camera.initial_tilt_deg)
        w,h=config.camera.resolution; zoom=config.camera.digital_zoom
        self.cx=float(np.clip(config.world.width/2+self.pan*w/config.camera.fov_deg[0]/zoom,0,config.world.width))
        self.cy=float(np.clip(config.world.height/2+self.tilt*h/config.camera.fov_deg[1]/zoom,0,config.world.height))
        self.pan_velocity=self.tilt_velocity=0.
        self.thermal_reference_c=20.
        self.t=0.; self.positions=[]; self.last_truths=[]; self.jitter=(0,0); self.platform_offset_prev=(0.0,0.0)
        self.phase_screen = PhaseScreen(config.seed + 7)

    def point(self,pan_speed,tilt_speed,dt):
        c=self.c.camera
        pan_speed=float(np.clip(pan_speed,-c.max_pan_speed,c.max_pan_speed))
        tilt_speed=float(np.clip(tilt_speed,-c.max_tilt_speed,c.max_tilt_speed))
        step=c.acceleration_deg_s2*dt
        self.pan_velocity=float(np.clip(pan_speed,self.pan_velocity-step,self.pan_velocity+step)) if step else pan_speed
        self.tilt_velocity=float(np.clip(tilt_speed,self.tilt_velocity-step,self.tilt_velocity+step)) if step else tilt_speed
        self.pan+=self.pan_velocity*dt; self.tilt+=self.tilt_velocity*dt
        w,h=c.resolution
        self.cx=np.clip(self.c.world.width/2+self.pan*w/c.fov_deg[0]/c.digital_zoom,0,self.c.world.width)
        self.cy=np.clip(self.c.world.height/2+self.tilt*h/c.fov_deg[1]/c.digital_zoom,0,self.c.world.height)

    def frame(self,dt):
        self.t+=dt; c=self.c; w,h=c.camera.resolution
        d=c.disturbance; self.positions=[tr.step(self.t,dt) for tr in self.targets]
        px,py=platform_offset(d.platform_motion,d.platform_amplitude_px,self.t,self.rng)
        # Enforce the PS platform-motion limit as a true per-frame displacement.
        max_step=float(d.platform_max_step_px)
        dx=float(np.clip(px-self.platform_offset_prev[0],-max_step,max_step));dy=float(np.clip(py-self.platform_offset_prev[1],-max_step,max_step))
        px=self.platform_offset_prev[0]+dx;py=self.platform_offset_prev[1]+dy;self.platform_offset_prev=(px,py)
        self.jitter=sample_jitter(self.rng,d.camera_jitter_px)
        ox=self.cx+px+self.jitter[0]; oy=self.cy+py+self.jitter[1]
        if c.camera.digital_zoom!=1:
            zw,zh=w/c.camera.digital_zoom,h/c.camera.digital_zoom
            image=cv2.resize(self.world.view(ox,oy,max(1,int(zw)),max(1,int(zh))),(w,h))
        else:image=self.world.view(ox,oy,w,h)
        scale=c.camera.digital_zoom
        truths=[]
        occult=not cloud_visible(self.t,d.occlusion_start_s,d.occlusion_duration_s)
        for i,(tx,ty) in enumerate(self.positions):
            x=(tx-ox)*scale+w/2; y=(ty-oy)*scale+h/2
            visible=(0<=x<w and 0<=y<h and not (occult and i==0))
            if c.target.blink_hz>0 and math.sin(2*math.pi*c.target.blink_hz*self.t)<-.65: visible=False
            truths.append((x,y,visible))
            if visible: draw_beacon(image,x,y,(c.target.width_px,c.target.height_px),c.target.brightness,c.target.shape)
        if d.spoof_enabled:
            # Intentional unlabeled distractor, never accepted as ground truth.
            draw_beacon(image,w/2+d.spoof_offset_px,h/2,(c.target.width_px,c.target.height_px),c.target.brightness,c.target.shape)
        image=apply_environment(image,d,self.rng,self.phase_screen)
        if d.thermal_enabled:
            offset=(d.temperature_c-self.thermal_reference_c)*d.thermal_coefficient_px_c
            image=cv2.warpAffine(image,np.float32([[1,0,offset],[0,1,offset*.5]]),(w,h),borderMode=cv2.BORDER_REFLECT)
            truths=[(x+offset,y+offset*.5,visible and 0<=x+offset<w and 0<=y+offset*.5<h) for x,y,visible in truths]
        if d.sensor_enabled:
            sample=expose(image,self.rng,d.sensor_qe,d.sensor_read_noise_e,d.sensor_dark_current_e_s,d.sensor_exposure_s,d.sensor_bit_depth)
            image=(sample.astype('float32')*(255/((1<<d.sensor_bit_depth)-1))).clip(0,255).astype('uint8') if d.sensor_bit_depth>8 else sample
            if d.hot_pixel_pct:
                mask=self.rng.random((h,w))<d.hot_pixel_pct;image[mask]=255
        if c.camera.color:
            tinted=cv2.cvtColor(image,cv2.COLOR_GRAY2BGR)
            rgb=c.target.color_rgb;weights=np.array(rgb[::-1],dtype='float32')/255
            for x,y,visible in truths:
                if not visible:continue
                r=c.target.size_px*2;ix=int(x);iy=int(y)
                xa=max(0,ix-r);xb=min(w,ix+r+1);ya=max(0,iy-r);yb=min(h,iy+r+1)
                if xa<xb and ya<yb:
                    yy,xx=np.mgrid[ya:yb,xa:xb];mask=((xx-x)**2+(yy-y)**2)<r*r
                    roi=tinted[ya:yb,xa:xb];roi[mask]=(roi[mask]*weights).astype('uint8')
            image=tinted
        self.last_truths=truths
        return image,truths

