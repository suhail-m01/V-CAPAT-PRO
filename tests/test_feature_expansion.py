"""Regression coverage for blueprint-derived, evidence-labelled additions."""
from datetime import datetime, timezone
import json
from pathlib import Path
import cv2
import pytest
from vcapat.config.settings import Scenario
from vcapat.core.engine import Engine
from vcapat.simulation.camera import Simulator
from vcapat.metrics.forecast import forecast_risk
from vcapat.metrics.baseline import compare_to_static
from vcapat.link.network import evaluate_network
from vcapat.io.scenario_manager import perturb_scenario
from vcapat.io.demo_video import produce_demo
from vcapat.io.tle_loader import ground_station_look_angles
from vcapat.core.feature_registry import feature_payload

ROOT=Path(__file__).resolve().parents[1]


def test_55_features_are_explicit_and_honest():
    entries=feature_payload()
    assert [e['id'] for e in entries]==list(range(1,56))
    assert {e['status'] for e in entries}=={'RUNNABLE','PARTIAL','INTEGRATION'}
    assert entries[30]['status']=='INTEGRATION'  # no fabricated RL weights
    assert entries[14]['status']=='INTEGRATION'  # no Windows EXE from Linux


def test_config_and_sensor_camera_are_integrated():
    cfg=Scenario()
    cfg.target.initial_mode='random';cfg.target.boundary='wrap';cfg.target.color_rgb=[255,100,140]
    cfg.target.count=2;cfg.camera.color=True;cfg.camera.digital_zoom=1.5
    cfg.camera.acceleration_deg_s2=5;cfg.disturbance.sensor_enabled=True
    cfg.disturbance.sensor_bit_depth=12;cfg.disturbance.hot_pixel_pct=.00001
    cfg.disturbance.thermal_enabled=True;cfg.disturbance.temperature_c=30
    cfg.disturbance.spoof_enabled=True;cfg.control.kp=8;cfg.control.search_pattern='raster'
    cfg.tracking.hits_to_lock=4;cfg.validate()
    restored=Scenario.from_dict(cfg.to_dict());assert restored==cfg
    sim=Simulator(restored);frame,truth=sim.frame(1/30)
    assert frame.shape==(480,640,3) and frame.dtype.name=='uint8'
    assert len(truth)==2 and sim.targets[0].x0!=cfg.target.initial_position[0]
    sim.point(5,5,1/30)
    assert 0<sim.pan_velocity<=5/30+1e-5
    sim.thermal_reference_c=cfg.disturbance.temperature_c
    engine=Engine(restored)
    for _ in range(8):engine.step()
    snap=engine.snapshot()
    assert snap['search_pattern']=='raster' and 0<=snap['trust']<=1
    assert snap['ber_proxy']>=0 and snap['bytes_proxy']>=0
    assert engine.pan_pid.kp==8 and engine.tracker.hits_to_lock==4
    engine.close()
    cfg.camera.digital_zoom=5
    with pytest.raises(ValueError):cfg.validate()


def test_saved_seed_baseline_station_and_forecast(tmp_path):
    base=Scenario();custom=perturb_scenario(base,123)
    path=tmp_path/'test.json';custom.save(path)
    assert Scenario.load(path).seed==123
    a=compare_to_static(base,30)
    assert a['frames']==30 and a['fixed_camera_rmse_px'] is not None
    n=evaluate_network((1100,1000),[(900,1000),(1100,1000),(1600,1600)])
    assert n['covered_by']==2 and n['overlap'] and n['selected_station']==1
    assert forecast_risk([])['risk']=='N/A'
    warnings=[{'detected':False,'pointing_error_px':65} for _ in range(8)]
    assert forecast_risk(warnings)['risk']=='HIGH'


def test_ground_station_sgp4_and_demo_video(tmp_path):
    tle='''ISS (ZARYA)
1 25544U 98067A   24125.76531013  .00028570  00000-0  51980-3 0  9995
2 25544  51.6416  41.4238 0005513 239.2095 229.7956 15.50794345451770'''
    try:
        import sgp4  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match='sgp4'):
            ground_station_look_angles(tle,datetime(2024,5,4,tzinfo=timezone.utc),13.1,77.6)
    else:
        angles=ground_station_look_angles(tle,datetime(2024,5,4,tzinfo=timezone.utc),13.1,77.6)
        assert 0<=angles['azimuth_deg']<360 and -90<=angles['elevation_deg']<=90
        assert 100<angles['slant_range_km']<15000
    result=produce_demo(tmp_path/'short.mp4',[ROOT/'scenarios/easy_clear_circular.json'],5,fps=10)
    assert result['frames']==50 and (tmp_path/'short.mp4').stat().st_size>1000
    capture=cv2.VideoCapture(str(tmp_path/'short.mp4'))
    assert capture.isOpened() and capture.get(cv2.CAP_PROP_FRAME_COUNT)>=45
    capture.release()
