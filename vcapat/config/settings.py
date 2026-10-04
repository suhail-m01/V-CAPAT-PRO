"""Validated, serializable scenario configuration. Units: px, seconds and degrees."""
from dataclasses import dataclass, field, asdict
import json

@dataclass
class WorldConfig:
    width: int = 2000
    height: int = 2000
    background: str = 'deep_space'
    star_density: float = 0.00006
    seed: int = 42
    solid_gray: int = 25

@dataclass
class TargetConfig:
    shape: str = 'gaussian'
    size_px: int = 10
    width_px: int = 10
    height_px: int = 10
    brightness: int = 245
    trajectory: str = 'circular'
    speed_pps: float = 60.0
    initial_position: list = field(default_factory=lambda: [1020, 1000])
    count: int = 1
    auto_handover: bool = False
    blink_hz: float = 0.0
    initial_mode: str = 'manual'  # manual | center | random (seeded)
    boundary: str = 'bounce'  # bounce | wrap
    color_rgb: list = field(default_factory=lambda: [255,255,255])
    priorities: list = field(default_factory=lambda: [0,1,2,3,4])

@dataclass
class CameraConfig:
    resolution: list = field(default_factory=lambda: [640, 480])
    fov_deg: list = field(default_factory=lambda: [4.0, 3.0])
    update_hz: int = 30
    max_pan_speed: float = 5.0
    max_tilt_speed: float = 5.0
    initial_pan_deg: float = 0.0
    initial_tilt_deg: float = 0.0
    acceleration_deg_s2: float = 0.0  # 0 disables acceleration limit
    digital_zoom: float = 1.0
    color: bool = False

@dataclass
class DisturbanceConfig:
    atmosphere: str = 'clear'
    noise_types: list = field(default_factory=list)
    noise_std: float = 5.0
    salt_pepper_pct: float = 0.02
    camera_jitter_px: float = 0.0
    platform_motion: str = 'none'
    platform_amplitude_px: float = 0.0
    platform_max_step_px: float = 20.0
    contrast_scale: float = 1.0
    brightness_offset: float = 0.0
    occlusion_start_s: float = -1.0
    occlusion_duration_s: float = 0.0
    turbulence_r0: float = 0.15
    sensor_enabled: bool = False
    sensor_qe: float = 0.8
    sensor_read_noise_e: float = 2.0
    sensor_dark_current_e_s: float = 1.0
    sensor_exposure_s: float = 0.01
    sensor_bit_depth: int = 8
    hot_pixel_pct: float = 0.0
    thermal_enabled: bool = False
    temperature_c: float = 20.0
    thermal_coefficient_px_c: float = 0.15
    spoof_enabled: bool = False
    spoof_offset_px: float = 60.0

@dataclass
class LinkConfig:
    point_ahead: bool = False
    distance_km: float = 1_000.0
    round_trip: bool = True

@dataclass
class ControlConfig:
    kp: float = 14.0
    ki: float = 0.3
    kd: float = 0.12
    deadband_deg: float = 0.0015
    search_pattern: str = 'spiral'
    assist_fraction: float = 0.0

@dataclass
class TrackingConfig:
    process_noise: float = 12.0
    measurement_noise: float = 5.0
    hits_to_lock: int = 3
    coast_after: int = 5
    reacquire_after: int = 20

@dataclass
class Scenario:
    name: str = 'Easy · Clear Orbit'
    world: WorldConfig = field(default_factory=WorldConfig)
    target: TargetConfig = field(default_factory=TargetConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    disturbance: DisturbanceConfig = field(default_factory=DisturbanceConfig)
    link: LinkConfig = field(default_factory=LinkConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    detector: str = 'adaptive'
    controller: str = 'pid'
    duration_s: float = 60.0
    seed: int = 42

    def validate(self):
        """Reject unsafe allocations and incompatible input before initializing NumPy/Qt."""
        def require(condition,message):
            if not condition:raise ValueError(message)
        require(2000<=self.world.width<=4000 and 2000<=self.world.height<=4000,'PS-compliant world dimensions must be 2000–4000 × 2000–4000 px')
        require(self.world.background in ('deep_space','sky','solid') and 0<=self.world.solid_gray<=255,'Invalid world background')
        require(0<=self.world.star_density<=.01 and 0<=self.world.seed<=2**32-1,'Invalid star density or seed')
        require(5<=self.target.size_px<=20 and 5<=self.target.width_px<=20 and 5<=self.target.height_px<=20 and 1<=self.target.count<=5,'Target size/dimensions/count out of range')
        require(self.target.trajectory in ('straight','circular','figure8','random','spiral','sinusoidal','leo','uav','haps','aircraft','star'),'Invalid trajectory')
        require(self.target.shape in ('gaussian','square','circle','airy') and 0<=self.target.brightness<=255,'Invalid beacon profile')
        require(0<self.target.speed_pps<=300 and 0<=self.target.blink_hz<=20,'Target speed/blink out of range')
        require(len(self.target.initial_position)==2,'Initial target position must have x and y')
        require(self.target.initial_mode in ('manual','center','random') and self.target.boundary in ('bounce','wrap'),'Invalid start or boundary mode')
        require(len(self.target.color_rgb)==3 and all(isinstance(x,int) and 0<=x<=255 for x in self.target.color_rgb),'Color must be three 8-bit RGB channels')
        require(sorted(self.target.priorities)==list(range(5)),'Target priorities must be a permutation of 0..4')
        require(len(self.camera.resolution)==2 and 320<=self.camera.resolution[0]<=1920 and 240<=self.camera.resolution[1]<=1080,'Camera resolution out of range')
        require(len(self.camera.fov_deg)==2 and all(.5<=f<=30 for f in self.camera.fov_deg),'Camera FOV must be 0.5–30 degrees')
        require(30<=self.camera.update_hz<=60 and 5<=self.camera.max_pan_speed<=10 and 5<=self.camera.max_tilt_speed<=10,'PS-compliant camera rate/speed requires update >=30 Hz and pan/tilt 5–10 deg/s')
        require(abs(self.camera.initial_pan_deg)<=20 and abs(self.camera.initial_tilt_deg)<=20 and 0<=self.camera.acceleration_deg_s2<=100 and 1<=self.camera.digital_zoom<=4,'Invalid camera pose, acceleration or zoom')
        require(self.disturbance.atmosphere in ('clear','haze','fog','rain','low_light','turbulence'),'Invalid atmosphere')
        require(all(n in ('gaussian','poisson','salt_pepper') for n in self.disturbance.noise_types),'Invalid noise type')
        require(0<=self.disturbance.camera_jitter_px<=20 and 0<=self.disturbance.platform_amplitude_px<=20 and 0<=self.disturbance.platform_max_step_px<=20,'Disturbance exceeds ±20 px/frame')
        require(0<=self.disturbance.salt_pepper_pct<=.1 and 0<=self.disturbance.noise_std<=20,'Noise out of range')
        require(0.1<=self.disturbance.contrast_scale<=1.5 and -100<=self.disturbance.brightness_offset<=100,'Atmospheric contrast/brightness adjustment out of range')
        require(.03<=self.disturbance.turbulence_r0<=1.0,'Fried parameter must be 0.03–1 m')
        d=self.disturbance
        require(0<d.sensor_qe<=1 and 0<=d.sensor_read_noise_e<=30 and 0<=d.sensor_dark_current_e_s<=500 and .0001<=d.sensor_exposure_s<=2 and d.sensor_bit_depth in (8,12,14,16) and 0<=d.hot_pixel_pct<=.01,'Invalid sensor model')
        require(-50<=d.temperature_c<=100 and 0<=d.thermal_coefficient_px_c<=2 and 5<=d.spoof_offset_px<=300,'Invalid thermal/spoof settings')
        require(self.control.search_pattern in ('spiral','raster','random') and all(0<=x<=100 for x in (self.control.kp,self.control.ki,self.control.kd)) and 0<=self.control.deadband_deg<=1 and 0<=self.control.assist_fraction<=1,'Invalid controller tuning')
        require(0<=self.tracking.process_noise<=100 and 0<self.tracking.measurement_noise<=100 and 1<=self.tracking.hits_to_lock<=20 and 1<=self.tracking.coast_after<self.tracking.reacquire_after<=200,'Invalid tracker tuning')
        require(10<=self.link.distance_km<=40_000 and isinstance(self.link.point_ahead,bool),'Invalid point-ahead link settings')
        require(self.detector in ('adaptive','top_hat','template','optical_flow','auto','tinyml','ai_auto') or self.detector.startswith('plugin:'),'Invalid detector')
        require(self.controller=='pid' or self.controller.startswith('plugin:'),'Invalid controller')
        require(0<=self.seed<=2**32-1 and 0<self.duration_s<=3600,'Invalid seed or duration')
        return self

    def to_dict(self): return asdict(self)

    @classmethod
    def from_dict(cls, data):
        kwargs = {k:v for k,v in data.items() if k in ('name','detector','controller','duration_s','seed')}
        for key, model in [('world',WorldConfig),('target',TargetConfig),('camera',CameraConfig),('disturbance',DisturbanceConfig),('link',LinkConfig),('control',ControlConfig),('tracking',TrackingConfig)]:
            kwargs[key] = model(**{k:v for k,v in data.get(key,{}).items() if k in model.__dataclass_fields__})
        return cls(**kwargs).validate()

    @classmethod
    def load(cls, path):
        with open(path, encoding='utf-8') as f: return cls.from_dict(json.load(f))

    def save(self, path):
        with open(path,'w',encoding='utf-8') as f: json.dump(self.to_dict(),f,indent=2)
