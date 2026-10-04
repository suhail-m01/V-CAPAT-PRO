from pathlib import Path
import numpy as np
from vcapat.config.settings import Scenario
from vcapat.config.ps_compliance import evaluate
from vcapat.core.engine import Engine
from vcapat.detection.tinyml import TinyMLBeaconClassifier
from vcapat.disturbance.beam_optics import draw_beacon

ROOT=Path(__file__).resolve().parents[1]

def test_reference_scenario_meets_ps_constraints():
    cfg=Scenario.load(ROOT/'scenarios'/'ps_compliant_reference.json')
    checks=evaluate(cfg)
    assert checks and all(c.passed for c in checks),[(c.name,c.detail) for c in checks if not c.passed]

def test_reference_scenario_acquires_and_tracks():
    e=Engine(Scenario.load(ROOT/'scenarios'/'ps_compliant_reference.json'))
    for _ in range(120):e.step()
    assert any(r['lock_state']=='LOCKED' for r in e.rows)
    e.close()

def test_rectangular_target_renderer_and_blink_path():
    im=np.zeros((120,160),np.uint8)
    draw_beacon(im,80,60,(8,16),245,'square')
    ys,xs=np.where(im>0)
    assert np.ptp(xs)+1>=7 and np.ptp(ys)+1>=15
    cfg=Scenario();cfg.target.blink_hz=2.0
    e=Engine(cfg)
    for _ in range(10):e.step()
    e.close()

def test_tinyml_classifier_prefers_beacon_like_candidate():
    m=TinyMLBeaconClassifier()
    good=m.probability(180,.8,.9,90,3,30)
    bad=m.probability(20,.15,.2,500,80,30)
    assert good>bad and good>.5
