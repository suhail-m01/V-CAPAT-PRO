"""Problem-statement compliance helpers for SIH26169 / FSOC coarse alignment."""
from __future__ import annotations
from dataclasses import dataclass
from .settings import Scenario

@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str

def evaluate(config: Scenario):
    c=config
    return [
        Check('World size',c.world.width>=2000 and c.world.height>=2000,f'{c.world.width}x{c.world.height} px; minimum 2000x2000'),
        Check('Camera resolution',len(c.camera.resolution)==2,f'{c.camera.resolution[0]}x{c.camera.resolution[1]} px; 640x480 suggested/user-defined'),
        Check('Camera FOV',len(c.camera.fov_deg)==2,f'{c.camera.fov_deg[0]}x{c.camera.fov_deg[1]} deg; default 4x3'),
        Check('Camera update rate',c.camera.update_hz>=30,f'{c.camera.update_hz} Hz; minimum 30 Hz'),
        Check('Pan speed',5<=c.camera.max_pan_speed<=10,f'{c.camera.max_pan_speed} deg/s; required range 5-10'),
        Check('Tilt speed',5<=c.camera.max_tilt_speed<=10,f'{c.camera.max_tilt_speed} deg/s; required range 5-10'),
        Check('Target dimensions',5<=c.target.width_px<=20 and 5<=c.target.height_px<=20,f'{c.target.width_px}x{c.target.height_px} px; required 5-20 each'),
        Check('Target count',c.target.count>=1,f'{c.target.count}; at least one mandatory'),
        Check('Required target motion',c.target.trajectory in ('straight','circular','figure8','random','spiral','sinusoidal'),f'{c.target.trajectory}; core selectable set implemented'),
        Check('Noise standard deviation',0<=c.disturbance.noise_std<=20,f'{c.disturbance.noise_std} px; maximum 20'),
        Check('Salt/pepper amount',0<=c.disturbance.salt_pepper_pct<=.1,f'{100*c.disturbance.salt_pepper_pct:.1f}%; maximum 10%'),
        Check('Camera jitter',0<=c.disturbance.camera_jitter_px<=20,f'±{c.disturbance.camera_jitter_px} px/frame; maximum ±20'),
        Check('Platform step',0<=c.disturbance.platform_max_step_px<=20,f'±{c.disturbance.platform_max_step_px} px/frame; maximum ±20'),
        Check('Atmosphere mode',c.disturbance.atmosphere in ('clear','haze','fog','rain','low_light','turbulence'),c.disturbance.atmosphere),
        Check('AI-assisted detector',c.detector in ('tinyml','ai_auto') or c.detector.startswith('plugin:'),f'{c.detector}; tiny learned candidate classifier is built in'),
    ]

def assert_compliant(config: Scenario):
    failed=[x for x in evaluate(config) if not x.passed]
    if failed: raise ValueError('PS compliance failed: '+'; '.join(f'{x.name}: {x.detail}' for x in failed))
    return True
