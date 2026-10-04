"""Stress report artefacts are deliberately labelled software evidence."""
from pathlib import Path
from vcapat.stress.stress_suite import save_experiment

def test_stress_evidence_is_pdf_png_and_not_certification(tmp_path):
    result={'name':'20-case reproducible stress matrix','passing_cases':0,
            'cases':[{'name':f'fog / circular #{i}','atmosphere':'fog','trajectory':'circular','seed':i,
                      'pointing_rmse_px':15,'target_loss_pct':20,'processing_fps':30,
                      'passed_checks':1,'failed_checks':2,'centroid_rmse_px':.3} for i in range(20)]}
    folder=Path(save_experiment(result,tmp_path,'stress.json'))
    assert (folder/'stress_evidence.pdf').read_bytes().startswith(b'%PDF-1.4')
    assert (folder/'stress_heatmap.png').read_bytes().startswith(b'\x89PNG')
    assert b'NOT AN ISRO' in (folder/'stress_evidence.pdf').read_bytes()
