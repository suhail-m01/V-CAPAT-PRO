"""Controlled one-factor-at-a-time sweep with a fresh engine per setting."""
from ..config.settings import Scenario
from ..core.engine import Engine
from ..metrics.collector import summarize

def sweep(base,section,parameter,values,frames=90):
    results=[]
    for value in values:
        config=Scenario.from_dict(base.to_dict())
        target=getattr(config,section,None)
        if target is None or not hasattr(target,parameter):raise ValueError('Unknown scenario parameter')
        setattr(target,parameter,value);config.validate()
        engine=Engine(config)
        for _ in range(frames):engine.step()
        s=summarize(engine.rows,engine.tracker)
        results.append({'value':value,'pointing_rmse_px':s['pointing_rmse_px'],
                        'centroid_rmse_px':s['centroid_rmse_px'],'processing_fps':s['average_processing_fps'],
                        'acquisition_s':s['acquisition_s']})
    return results
