"""Seeded hill-climbing noise search; finds a reproducible hard test, not an exploit."""
from ..config.settings import Scenario
from ..core.engine import Engine
from ..metrics.collector import summarize

def search_weakness(base,frames=60,trials=8):
    best=None
    for seed in range(trials):
        cfg=Scenario.from_dict(base.to_dict());cfg.seed=base.seed+seed
        cfg.world.seed=cfg.seed;cfg.disturbance.noise_types=['gaussian']
        cfg.disturbance.noise_std=20*seed/max(1,trials-1)
        cfg.disturbance.atmosphere=('clear','haze','fog','rain')[seed%4]
        e=Engine(cfg)
        for _ in range(frames):e.step()
        error=summarize(e.rows,e.tracker)['pointing_rmse_px'] or 0
        if best is None or error>best['pointing_rmse_px']:
            best={'scenario':cfg.to_dict(),'pointing_rmse_px':error}
    return best
