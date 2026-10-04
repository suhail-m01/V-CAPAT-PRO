"""Deterministic, key-free performance narrative with actionable suggestions."""
def rule_based_summary(summary):
    if not summary:return 'No frames were processed.'
    observations=[f"Processed {summary['total_frames']} frames over {summary['duration_s']} simulated seconds."]
    error=summary.get('pointing_rmse_px') if summary.get('source_mode')=='simulator' else summary.get('centroid_rmse_px')
    if error is None:observations.append('Accuracy cannot be evaluated without visible labelled ground truth.')
    elif error>10:observations.append(f'Error RMSE of {error} px exceeds the ten-pixel target. Check beacon association and adjust PID or detector gating.')
    else:observations.append(f'Error RMSE of {error} px is within the ten-pixel budget for this run.')
    if summary.get('target_loss_pct') is not None and summary['target_loss_pct']>=5:
        observations.append('Lock retention is below the required threshold; test alternative search and handover settings.')
    if summary.get('max_reacquisition_s') is None:
        observations.append('No completed loss/recovery event was measured; reacquisition remains unverified.')
    return ' '.join(observations)
