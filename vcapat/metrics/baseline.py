"""Closed-loop PID vs fixed-camera baseline using identical seeded scenes."""
from ..config.settings import Scenario
from ..core.engine import Engine
from .collector import summarize

def compare_to_static(scenario,frames=120):
    if not 10<=frames<=360:raise ValueError('Baseline frames must be 10–360')
    cfg=Scenario.from_dict(scenario.to_dict())
    runs=[]
    for fixed in (False,True):
        e=Engine(Scenario.from_dict(cfg.to_dict()));e.manual=fixed;e.command=(0,0)
        try:
            for _ in range(frames):e.step()
            runs.append(summarize(e.rows,e.tracker))
        finally:e.close()
    managed,fixed=runs
    a,b=managed['pointing_rmse_px'],fixed['pointing_rmse_px']
    return {'scenario':cfg.name,'seed':cfg.seed,'frames':frames,'detector':cfg.detector,'controller':cfg.controller,'controlled_rmse_px':a,'fixed_camera_rmse_px':b,
            'improvement_pct':round(100*(b-a)/b,2) if a is not None and b else None,
            'note':'Identical seed and initial conditions; baseline motor remains fixed, not a second trained tracker.'}
