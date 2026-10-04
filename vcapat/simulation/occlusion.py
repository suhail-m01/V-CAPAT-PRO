"""Deterministic temporal cloud-pass visibility gate."""
def cloud_visible(time_s:float,start_s:float,duration_s:float)->bool:
    return not (start_s>=0 and start_s<=time_s<start_s+duration_s)
