"""Transparent warning rule; not a trained failure-prediction model."""
def forecast_risk(rows):
    if len(rows)<6:return {'risk':'N/A','reason':'At least six frames required','model':'heuristic'}
    recent=rows[-12:];misses=sum(not x['detected'] for x in recent)
    errors=[x['pointing_error_px'] for x in recent if x.get('pointing_error_px') is not None]
    increasing=len(errors)>=6 and sum(errors[-3:])/3>sum(errors[:3])/3+15
    if misses>=4 or increasing:risk='HIGH'
    elif misses>0 or (errors and max(errors)>30):risk='ELEVATED'
    else:risk='LOW'
    return {'risk':risk,'misses':misses,'increasing_error':increasing,'model':'deterministic recent-frame heuristic',
            'reason':'Detection misses or rising pointing error' if risk!='LOW' else 'No recent degradation trigger',
            'note':'Not a trained predictor; no guaranteed 2-second forecast.'}
