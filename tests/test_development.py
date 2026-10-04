"""Regression tests for the FSOC engineering and evidence modules."""
import json
from pathlib import Path
import numpy as np
import pytest
from vcapat.config.settings import Scenario
from vcapat.disturbance.turbulence import PhaseScreen
from vcapat.control.lead_angle import LIGHT_SPEED_M_S,lead_angle_rad

from vcapat.simulation.camera import Simulator
from vcapat.core.engine import Engine
from vcapat.metrics.reporter import export_session
from vcapat.metrics.collector import summarize
from vcapat.metrics.time_series_db import query_anomalies

def test_point_ahead_units_and_validation():
    assert lead_angle_rad(.01,40000)==pytest.approx(.01*80_000_000/LIGHT_SPEED_M_S)
    assert lead_angle_rad(.01,40000,False)==pytest.approx(lead_angle_rad(.01,40000)/2)
    with pytest.raises(ValueError):lead_angle_rad(.01,40001)
    cfg=Scenario();cfg.link.point_ahead=True;cfg.link.distance_km=40000
    e=Engine(cfg)
    for _ in range(90):e.step()
    assert 1<abs(e.snapshot()['lead_px'][0])<35 and e.rows[-1]['lead_distance_km']==40000

def test_phase_screen_is_reproducible_and_time_correlated():
    a,b=PhaseScreen(17),PhaseScreen(17)
    first=a.step(.15);assert np.array_equal(first[0],b.step(.15)[0])
    second=a.step(.15);assert np.array_equal(second[1],b.step(.15)[1])
    assert np.corrcoef(first[0].ravel(),second[0].ravel())[0,1]>.7
    cfg=Scenario();cfg.disturbance.atmosphere='turbulence'
    sim1,sim2=Simulator(cfg),Simulator(cfg)
    assert np.array_equal(sim1.frame(1/30)[0],sim2.frame(1/30)[0])

def test_manual_designation_and_identity_sensitive_metrics():
    cfg=Scenario();cfg.target.count=3
    engine=Engine(cfg);engine.step();other=engine.last_candidates[1]
    event=engine.designate_candidate(other['x'],other['y'])
    assert event['to_id']==1
    for _ in range(30):engine.step()
    assert engine.designated_target==1
    assert summarize(engine.rows,engine.tracker)['centroid_rmse_px']<1
    # Wrong-beacon locks do not count towards retention.
    rows=[dict(r) for r in engine.rows]
    for row in rows:row['correct_target']=False
    assert summarize(rows,engine.tracker)['target_loss_pct']==100

def test_automatic_handover_is_image_triggered():
    cfg=Scenario();cfg.target.count=3;cfg.target.auto_handover=True
    cfg.disturbance.occlusion_start_s=1;cfg.disturbance.occlusion_duration_s=3
    engine=Engine(cfg)
    for _ in range(100):engine.step()
    assert engine.handover_events
    assert engine.handover_events[0]['event']=='AUTO_HANDOVER'
    assert engine.designated_target!=0
    assert summarize(engine.rows,engine.tracker)['centroid_rmse_px']<1

def test_export_sqlite_pdf_and_indexed_queries(tmp_path):
    e=Engine(Scenario())
    for _ in range(60):e.step()
    folder=Path(export_session(e,tmp_path))
    assert (folder/'certificate.pdf').read_bytes().startswith(b'%PDF-1.4')
    assert (folder/'frames.sqlite').exists()
    hits=query_anomalies(folder/'frames.sqlite',5,10)
    assert hits and all(r['pointing_error_px']>5 for r in hits)
    assert len(hits)<=10
    with pytest.raises(ValueError):query_anomalies(folder/'frames.sqlite',0,metric='DROP TABLE')
    content=(folder/'certificate.pdf').read_bytes()
    assert b'NOT an ISRO' in content
