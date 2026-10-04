"""Reproducible offline experiments; never modify the active live engine."""
from pathlib import Path
import csv,json,datetime
import numpy as np
from ..config.settings import Scenario
from ..core.engine import Engine
from ..metrics.collector import summarize
from ..metrics.compliance import compliance
from ..simulation.camera import Simulator
from ..detection.arena import Detector

METHODS=('adaptive','top_hat','template','optical_flow')

def compare_detectors(scenario,frames=120):
    """Same seed and initial camera position for each closed-loop run."""
    results=[]
    for name in METHODS:
        cfg=Scenario.from_dict(scenario.to_dict());cfg.detector=name
        engine=Engine(cfg)
        for _ in range(frames):engine.step()
        s=summarize(engine.rows,engine.tracker)
        results.append({'detector':name,'centroid_rmse_px':s['centroid_rmse_px'],
                        'pointing_rmse_px':s['pointing_rmse_px'],'lock_retention_pct':s['lock_retention_pct'],
                        'processing_fps':s['average_processing_fps'],'acquisition_s':s['acquisition_s']})
    results.sort(key=lambda x:(x['centroid_rmse_px'] is None,x['centroid_rmse_px'] if x['centroid_rmse_px'] is not None else 1e9))
    return {'scenario':scenario.name,'frames_per_detector':frames,'seed':scenario.seed,'ranking':results,
            'note':'Accuracy ranks by centroid RMSE. FPS measures pipeline cost, not capture cadence.'}

def stress_suite(scenario,frames=75):
    """20 isolated runs: four motion classes × five atmosphere presets."""
    trajectories=['circular','figure8','straight','random'];atmospheres=['clear','haze','fog','rain','low_light'];cases=[]
    for ai,atmosphere in enumerate(atmospheres):
        for ti,trajectory in enumerate(trajectories):
            cfg=Scenario.from_dict(scenario.to_dict());cfg.name=f'{atmosphere} / {trajectory}'
            cfg.target.trajectory=trajectory;cfg.disturbance.atmosphere=atmosphere
            cfg.disturbance.noise_types=['gaussian'] if ai>=2 else [];cfg.disturbance.noise_std=float(ai*2)
            cfg.target.size_px=8 if ti==3 else 10;cfg.seed=scenario.seed+ai*100+ti;cfg.world.seed=cfg.seed
            cfg.disturbance.occlusion_start_s=-1;cfg.disturbance.occlusion_duration_s=0
            e=Engine(cfg)
            for _ in range(frames):e.step()
            s=summarize(e.rows,e.tracker);checks=compliance(s)
            cases.append({'name':cfg.name,'atmosphere':atmosphere,'trajectory':trajectory,'seed':cfg.seed,
                          'pointing_rmse_px':s['pointing_rmse_px'],'centroid_rmse_px':s['centroid_rmse_px'],
                          'target_loss_pct':s['target_loss_pct'],'processing_fps':s['average_processing_fps'],
                          'passed_checks':sum(v['status']=='PASS' for v in checks.values()),
                          'failed_checks':sum(v['status']=='FAIL' for v in checks.values()),'checks':checks})
    return {'name':'20-case reproducible stress matrix','frames_per_case':frames,'cases':cases,
            'passing_cases':sum(c['failed_checks']==0 for c in cases),
            'note':'Short tests do not certify long-session performance. N/A checks do not count as passed.'}

def signal_injection(offset_px=5):
    """Known synthetic sensor displacement; validates recovered centroid delta."""
    center=(220.25,160.4);base=np.full((320,440),8,np.uint8);shifted=base.copy()
    Simulator._draw_beacon(base,*center,12,245,'gaussian')
    Simulator._draw_beacon(shifted,center[0]+offset_px,center[1],12,245,'gaussian')
    a=Detector().detect(base);b=Detector().detect(shifted)
    measured=b.x-a.x if a.found and b.found else None
    return {'injected_x_px':offset_px,'measured_x_px':round(measured,4) if measured is not None else None,
            'absolute_error_px':round(abs(measured-offset_px),4) if measured is not None else None,
            'status':'PASS' if measured is not None and abs(measured-offset_px)<.5 else 'FAIL',
            'method':'Two separately rendered spots, same detector; compare subpixel centroid displacement.'}

def save_experiment(data,root='reports',filename='experiment.json'):
    folder=Path(root)/('experiment_'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f'))
    folder.mkdir(parents=True,exist_ok=True)
    (folder/filename).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
    if 'cases' in data:
        from ..metrics.stress_evidence import write_stress_pdf,write_stress_heatmap
        write_stress_pdf(folder/'stress_evidence.pdf',data)
        write_stress_heatmap(folder/'stress_heatmap.png',data)
        with (folder/'stress_matrix.csv').open('w',newline='') as f:
            keys=['name','atmosphere','trajectory','seed','pointing_rmse_px','centroid_rmse_px','target_loss_pct','processing_fps','passed_checks','failed_checks']
            writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(data['cases'])
    return str(folder)
