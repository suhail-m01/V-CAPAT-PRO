"""Ground-truth CSV schema for zero-indexed external video frames."""
import csv

def load_ground_truth(path):
    with open(path,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        required={'frame','timestamp_s','gt_x','gt_y','visible'}
        if not required.issubset(reader.fieldnames or []):raise ValueError('Ground truth must have: '+','.join(sorted(required)))
        return {int(r['frame']):(float(r['gt_x']),float(r['gt_y']),str(r['visible']).lower() in ('1','true','yes')) for r in reader}
