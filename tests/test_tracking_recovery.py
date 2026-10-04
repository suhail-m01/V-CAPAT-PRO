"""Regression tests for stale-gate recovery and realistic tracking outcomes."""
from vcapat.config.settings import Scenario
from vcapat.core.engine import Engine
from vcapat.metrics.collector import summarize
from vcapat.metrics.compliance import compliance


def test_three_second_blackout_reacquires_from_visible_pixels_only():
    config=Scenario.load('scenarios/total_blackout.json')
    assert config.disturbance.occlusion_duration_s==3
    engine=Engine(config)
    try:
        for _ in range(360):engine.step()
        states=[row['lock_state'] for row in engine.rows]
        assert 'REACQUIRING' in states and engine.tracker.reacquisitions
        assert engine.tracker.state=='LOCKED'
        assert engine.rows[-1]['correct_target'] is True
        # Three seconds of invisibility cannot honestly satisfy a one-second
        # loss-to-recovery limit. The failure must remain visible in evidence.
        assert compliance(summarize(engine.rows,engine.tracker))['max_reacquisition_s']['status']=='FAIL'
    finally:engine.close()


def test_default_closed_loop_works_under_clear_and_fog():
    for slug in ('easy_clear_circular','medium_foggy_figure8'):
        engine=Engine(Scenario.load('scenarios/'+slug+'.json'))
        try:
            for _ in range(300):engine.step()
            summary=summarize(engine.rows,engine.tracker)
            assert engine.tracker.state=='LOCKED'
            assert summary['pointing_rmse_px']<=10,slug
            assert summary['lock_retention_pct']>=95,slug
            assert summary['average_processing_fps']>=20,slug
        finally:engine.close()
