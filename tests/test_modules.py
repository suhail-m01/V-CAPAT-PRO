"""Architectural boundaries and optional-feature contracts."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import numpy as np
import pytest
from vcapat.config.settings import Scenario
from vcapat.core.engine import Engine
from vcapat.core.event_bus import EventBus
from vcapat.plugins.loader import discover,load_plugin
from vcapat.utils.qr_code import dashboard_qr_png
from vcapat.api.websocket_stream import encode_text_frame
from vcapat.disturbance.sensor_physics import expose
from vcapat.disturbance.thermal_drift import ThermalDrift
from vcapat.link.ber_model import bpsk_ber,pointing_snr
from vcapat.metrics.reporter import export_session
from vcapat.stress.sensitivity import sweep
from vcapat.io.session_recorder import SessionRecorder

ROOT=Path(__file__).resolve().parents[1]

def test_exact_requested_module_layout():
    expected={'config':'settings defaults.json','core':'models state_machine event_bus constants',
      'simulation':'world target trajectories camera star_field occlusion',
      'disturbance':'noise atmosphere turbulence jitter platform_motion sensor_physics thermal_drift beam_optics',
      'detection':'base adaptive_threshold top_hat template_match yolo_onnx optical_flow arena centroiding xai',
      'tracking':'kalman associator multi_target failure_predictor handover',
      'control':'pid rl_agent search lead_angle manual','link':'link_quality ber_model',
      'metrics':'collector compliance reporter time_series_db llm_summary',
      'io':'video_source webcam_source ground_truth scenario_manager session_recorder tle_loader',
      'gui':'main_window viewport_widget minimap_widget metrics_panel settings_dialog xray_overlay ar_hud plots_panel replay_widget judge_demo achievements tutorial compliance_widget link_quality_widget multi_algo_widget stress_test_widget sensitivity_widget theme',
      'plugins':'loader interfaces','api':'rest_server websocket_stream',
      'security':'spoof_detector','stress':'stress_suite adversarial sensitivity',
      'utils':'geometry math_utils logger qr_code audio'}
    for package,names in expected.items():
        assert (ROOT/'vcapat'/package/'__init__.py').is_file()
        for name in names.split():
            assert (ROOT/'vcapat'/package/(name if name.endswith('.json') else name+'.py')).is_file(),(package,name)
    assert (ROOT/'vcapat/api/companion_web/templates/index.html').is_file()
    assert (ROOT/'assets/models/README.md').is_file()
    assert not (ROOT/'assets/models/yolov8n_beacon.onnx').exists() # no counterfeit model

def test_trusted_example_plugins_run_in_shared_pipeline():
    assert set(discover())=={'example_detector_plugin','example_controller_plugin'}
    s=Scenario();s.detector='plugin:example_detector_plugin';s.controller='plugin:example_controller_plugin'
    e=Engine(s)
    for _ in range(60):e.step()
    assert e.tracker.state=='LOCKED' and e.last['centroid_error_px']<4
    with pytest.raises(ValueError):load_plugin('../outside')

def test_event_bus_isolation_and_unsubscribe():
    bus=EventBus();seen=[]
    off=bus.subscribe('LOCKED',lambda event:seen.append(event['frame']))
    bus.subscribe('LOCKED',lambda event:1/0)
    bus.publish({'event':'LOCKED','frame':3})
    off();bus.publish({'event':'LOCKED','frame':4})
    assert seen==[3]

def test_qr_websocket_and_camera_physics():
    assert dashboard_qr_png('http://localhost:8000/').startswith(b'\x89PNG\r\n\x1a\n')
    data='x'*170;frame=encode_text_frame(data)
    assert frame[0]==0x81 and frame[1]==126 and int.from_bytes(frame[2:4],'big')==170
    rng=np.random.default_rng(3)
    image=np.full((6,6),100,dtype=np.uint8)
    out=expose(image,rng,bit_depth=12)
    assert out.dtype==np.uint16 and out.shape==image.shape
    drift=ThermalDrift();drift.calibrate(4,3)
    assert drift.measure(4,20)==3
    assert bpsk_ber(20)<bpsk_ber(1)
    assert pointing_snr(100,.1,.1)<pointing_snr(100,0,.1)

def test_sensitivity_and_recording_export(tmp_path):
    result=sweep(Scenario(),'disturbance','noise_std',[0,3],frames=20)
    assert len(result)==2 and all(r['processing_fps']>0 for r in result)
    e=Engine(Scenario());e.start_recording(tmp_path/'capture.mp4')
    for _ in range(8):e.step()
    folder=Path(export_session(e,tmp_path))
    assert (folder/'session_video.mp4').stat().st_size>1000
    assert json.loads((folder/'summary.json').read_text())['total_frames']==8
