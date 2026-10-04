"""Illustrative multi-station world-plane coverage and truth-audit handover.

Not real ground-station RF/FSOC network simulation or orbital ephemeris.
"""
import math

def evaluate_network(target_xy, stations, fov_px=(640,480), previous=None):
    if len(stations)>12 or len(stations)<1:raise ValueError('Provide 1–12 station coordinates')
    x,y=map(float,target_xy);fw,fh=map(float,fov_px)
    if fw<=0 or fh<=0:raise ValueError('FOV dimensions must be positive')
    coverage=[]
    for i,station in enumerate(stations):
        if len(station)!=2:raise ValueError('Station must have two world coordinates')
        sx,sy=map(float,station);visible=abs(x-sx)<=fw/2 and abs(y-sy)<=fh/2
        coverage.append({'station':i,'world_xy':[sx,sy],'visible':visible,'distance_px':round(math.hypot(x-sx,y-sy),2)})
    inside=[c for c in coverage if c['visible']]
    chosen=next((c for c in inside if c['station']==previous),None) if previous is not None else None
    if chosen is None:chosen=min(inside,key=lambda c:c['distance_px'],default=None)
    return {'selected_station':chosen['station'] if chosen else None,'handover':previous is not None and chosen is not None and chosen['station']!=previous,
            'covered_by':len(inside),'overlap':len(inside)>=2,'stations':coverage,
            'note':'World-plane visibility proxy using ground truth for network planning only; never fed to detector/PID.'}
