"""Independent spec checks; unknown evidence is N/A, never PASS."""

def compliance(summary):
    error_key='pointing_rmse_px' if summary.get('source_mode')=='simulator' else 'centroid_rmse_px'
    checks={'acquisition_s':('Acquisition ≤ 2 s',2,'max'),
            error_key:(('Pointing RMSE' if error_key=='pointing_rmse_px' else 'Centroid RMSE')+' ≤ 10 px',10,'max'),
            'target_loss_pct':('Target loss < 5 %',5,'strict'),
            'max_reacquisition_s':('Re-acquisition ≤ 1 s',1,'max'),
            'average_processing_fps':('Processing ≥ 20 FPS',20,'min')}
    result={}
    for key,(label,limit,op) in checks.items():
        value=summary.get(key)
        status='N/A' if value is None else ('PASS' if (value<limit if op=='strict' else value>=limit if op=='min' else value<=limit) else 'FAIL')
        result[key]={'label':label,'value':value,'limit':limit,'status':status}
    return result

