"""Aggregation of labelled visible frames and telemetry."""
import numpy as np
import math
from ..utils.math_utils import root_mean_square

def summarize(rows,tracker):
    if not rows:return {}
    values=lambda key:[float(r[key]) for r in rows if r.get(key) is not None]
    errors=values('centroid_error_px');points=values('pointing_error_px');times=values('processing_time_ms')
    visible=sum(r['target_visible'] is True for r in rows); locked=sum(r['target_visible'] is True and r.get('correct_target') is True and r['lock_state']=='LOCKED' for r in rows)
    truth_available=any(r['target_visible'] is not None for r in rows)
    return {'source_mode':rows[-1]['source_mode'],'duration_s':rows[-1]['timestamp_s'],'total_frames':len(rows),'processed_frames':len(rows),
            'average_processing_fps':round(1000/np.mean(times),2) if times else None,
            'minimum_processing_fps':round(1000/max(times),2) if times else None,
            'average_processing_ms':round(float(np.mean(times)),2) if times else None,
            'maximum_processing_ms':round(max(times),2) if times else None,
            'acquisition_s':next((round(r['timestamp_s'],3) for r in rows if r['lock_state']=='LOCKED' and r.get('correct_target') is True),None),
            'average_reacquisition_s':round(float(np.mean(tracker.reacquisitions)),3) if tracker.reacquisitions else None,
            'max_reacquisition_s':round(max(tracker.reacquisitions),3) if tracker.reacquisitions else None,
            'number_of_losses':tracker.losses,
            'lock_retention_pct':round(100*locked/visible,2) if visible else None,
            'target_loss_pct':round(100*(1-locked/visible),2) if visible else None,
            'centroid_rmse_px':round(root_mean_square(errors),3) if errors else None,
            'centroid_mean_px':round(float(np.mean(errors)),3) if errors else None,
            'centroid_max_px':round(max(errors),3) if errors else None,
            'pointing_rmse_px':round(root_mean_square(points),3) if points else None,
            'pointing_mean_px':round(float(np.mean(points)),3) if points else None,
            'pointing_max_px':round(max(points),3) if points else None,
            'ground_truth_available':truth_available,
            'metrics_note':'Processing FPS is 1000 / mean pipeline milliseconds, not capture/render cadence. Lock retention uses visible frames including initial acquisition.'}

