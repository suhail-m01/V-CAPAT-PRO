"""Portable scenario JSON loading and seeded perturbation for comparisons."""
from pathlib import Path
import numpy as np
from ..config.settings import Scenario

def list_scenarios(folder):
    return [(p.stem,Scenario.load(p).name) for p in sorted(Path(folder).glob('*.json'))]

def perturb_scenario(scenario,seed):
    rng=np.random.default_rng(seed);result=Scenario.from_dict(scenario.to_dict())
    result.seed=int(seed);result.world.seed=int(seed)
    result.target.speed_pps=float(rng.uniform(25,120))
    result.disturbance.noise_std=float(rng.uniform(0,15))
    result.disturbance.noise_types=['gaussian']
    result.disturbance.atmosphere=str(rng.choice(['clear','haze','fog','rain','low_light']))
    result.name=f'Generated #{seed}'
    return result.validate()
