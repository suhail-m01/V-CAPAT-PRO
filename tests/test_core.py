import json,math
from pathlib import Path
import cv2
import numpy as np
from vcapat.config.settings import Scenario
from vcapat.simulation.camera import Simulator
from vcapat.simulation.trajectories import Trajectory
from vcapat.detection.arena import Detector
from vcapat.tracking.kalman import Kalman
from vcapat.control.pid import PID
from vcapat.core.engine import Engine
from vcapat.metrics.collector import summarize
from vcapat.metrics.compliance import compliance
from vcapat.io.ground_truth import load_ground_truth
from vcapat.metrics.reporter import export_session

def test_all_trajectories_are_bounded_and_deterministic():
    for name in ['straight','circular','figure8','random','spiral','sinusoidal','leo','uav','haps','aircraft','star']:
        cfg=Scenario();cfg.target.trajectory=name
        a=Trajectory(cfg.target,cfg.world,5);b=Trajectory(cfg.target,cfg.world,5)
        for i in range(100):
            x,y=a.step(i/30,1/30);assert np.allclose([x,y],b.step(i/30,1/30))
            assert 0<=x<=cfg.world.width and 0<=y<=cfg.world.height

def test_detectors_find_beacon_without_truth_leak():
    img=np.full((480,640),9,np.uint8)
    Simulator._draw_beacon(img,273.4,204.7,12,245,'gaussian')
    for mode in ['adaptive','top_hat','template','optical_flow','auto']:
        d=Detector(mode).detect(img)
        assert d.found,(mode,d.candidates)
        assert math.hypot(d.x-273.4,d.y-204.7)<2.5,(mode,d.x,d.y)

def test_kalman_smoothing_and_pid_saturation():
    k=Kalman();k.update(0,0);rng=np.random.default_rng(7);raw=[];filtered=[]
    for i in range(1,100):
        k.predict(.1);x=i*.6+rng.normal(0,3);k.update(x,0);raw.append(x-i*.6);filtered.append(k.state[0]-i*.6)
    assert np.std(filtered)<np.std(raw)
    pid=PID(limit=5)
    for _ in range(200):assert abs(pid.step(100,.03))<=5
    assert math.isfinite(pid.integral)

def test_truth_sensitive_compliance():
    summary={'source_mode':'simulator','acquisition_s':.1,'pointing_rmse_px':15,'target_loss_pct':8,'max_reacquisition_s':None,'average_processing_fps':25}
    result=compliance(summary)
    assert result['pointing_rmse_px']['status']=='FAIL'
    assert result['target_loss_pct']['status']=='FAIL'
    assert result['max_reacquisition_s']['status']=='N/A'

def test_engine_report_and_seed_replay(tmp_path):
    cfg=Scenario();a=Engine(cfg);b=Engine(Scenario.from_dict(cfg.to_dict()))
    for i in range(100):
        r=a.step();other=b.step();assert r['gt_x']==other['gt_x']
    s=summarize(a.rows,a.tracker)
    assert s['acquisition_s']<=2 and s['centroid_rmse_px']<1
    folder=Path(export_session(a,tmp_path));assert (folder/'frames.csv').exists()
    assert json.loads((folder/'summary.json').read_text())['seed']==cfg.seed

def test_video_ground_truth_preserves_unknown(tmp_path):
    path=tmp_path/'truth.csv';path.write_text('frame,timestamp_s,gt_x,gt_y,visible\n0,0,4,5,1\n1,.033,4,5,0\n')
    assert load_ground_truth(path)=={0:(4.,5.,True),1:(4.,5.,False)}
    cfg=Scenario();e=Engine(cfg)
    video=tmp_path/'test.avi';out=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'MJPG'),30,(320,240))
    for i in range(4):
        frame=np.zeros((240,320,3),np.uint8);cv2.circle(frame,(160+i,120),5,(255,255,255),-1);out.write(frame)
    out.release();e.open_video(str(video));e.step()
    assert e.last['gt_x'] is None and compliance(summarize(e.rows,e.tracker))['centroid_rmse_px']['status']=='N/A'
    e.close()

def test_multi_beacon_initial_association_is_not_truth_driven():
    cfg=Scenario();cfg.target.count=5;cfg.disturbance.atmosphere='haze'
    e=Engine(cfg)
    for _ in range(20):e.step()
    assert e.rows[0]['centroid_error_px']<2
    assert summarize(e.rows,e.tracker)['centroid_rmse_px']<2


def test_known_signal_injection():
    from vcapat.stress.stress_suite import signal_injection
    result=signal_injection(5)
    assert result['status']=='PASS' and result['absolute_error_px']<.5
