"""Portable SQLite time series and dependency-free one-page PDF evidence sheet.

The PDF is a *software benchmark report*, never an ISRO-issued certificate.
"""
from pathlib import Path
import sqlite3
import json

TEXT={'source_mode','lock_state','noise_mode','atmosphere_mode'}
INT={'frame_id','target_visible','detected','designated_id','correct_target'}
EXTRA=('link_quality','lead_x_px','lead_y_px','lead_distance_km')

def write_database(path,rows,columns,summary):
    path=Path(path)
    keys=tuple(columns)+EXTRA
    with sqlite3.connect(path) as db:
        schema=', '.join('"'+name+'" '+('TEXT' if name in TEXT else 'INTEGER' if name in INT else 'REAL') for name in keys)
        db.execute('CREATE TABLE frames ('+schema+')')
        db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value_json TEXT NOT NULL)')
        db.executemany('INSERT INTO metadata VALUES (?,?)',[(k,json.dumps(v,default=str)) for k,v in summary.items()])
        placeholders=','.join('?' for _ in keys)
        sql='INSERT INTO frames VALUES ('+placeholders+')'
        # Keep bounded batches when the caller supplies a streaming row iterable.
        batch=[]
        for row in rows:
            batch.append(tuple(int(row.get(k)) if k in INT and row.get(k) is not None and isinstance(row.get(k),bool) else row.get(k) for k in keys))
            if len(batch)==1000:db.executemany(sql,batch);batch=[]
        if batch:db.executemany(sql,batch)
        db.execute('CREATE INDEX idx_frames_pointing_error ON frames(pointing_error_px)')
        db.execute('CREATE INDEX idx_frames_centroid_error ON frames(centroid_error_px)')
        db.execute('CREATE INDEX idx_frames_state_time ON frames(lock_state,timestamp_s)')
    return path

def query_anomalies(path,threshold_px=15,limit=100,metric='pointing'):
    if metric not in ('pointing','centroid'): raise ValueError('metric must be pointing or centroid')
    column='pointing_error_px' if metric=='pointing' else 'centroid_error_px'
    threshold_px=float(threshold_px);limit=int(limit)
    if not (0<=threshold_px<=100_000 and 1<=limit<=500):raise ValueError('Invalid threshold/limit')
    with sqlite3.connect(path) as db:
        db.row_factory=sqlite3.Row
        rows=db.execute('SELECT frame_id,timestamp_s,source_mode,lock_state,'+column+',detection_confidence FROM frames WHERE '+column+' > ? ORDER BY '+column+' DESC LIMIT ?', (threshold_px,limit)).fetchall()
    return [dict(r) for r in rows]

