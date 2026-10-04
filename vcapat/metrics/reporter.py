"""Timestamped CSV / JSON / PDF / SQLite / PNG session export."""
import csv,json,datetime,shutil
from pathlib import Path
from .time_series_db import write_database
from .collector import summarize
from .llm_summary import rule_based_summary
from .compliance import compliance

COLUMNS=['frame_id', 'timestamp_s', 'source_mode', 'gt_x', 'gt_y', 'detected_x', 'detected_y', 'filtered_x', 'filtered_y', 'detection_confidence', 'target_visible', 'detected', 'lock_state', 'centroid_error_px', 'pointing_error_px', 'pan_deg', 'tilt_deg', 'pan_velocity_deg_s', 'tilt_velocity_deg_s', 'processing_time_ms', 'instantaneous_fps', 'noise_mode', 'atmosphere_mode', 'designated_id', 'correct_target']

def export_session(engine,root='reports'):
    folder=Path(root)/('session_'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f'))
    folder.mkdir(parents=True,exist_ok=True)
    if engine.recorder:engine.stop_recording()
    if engine.recording_path and engine.recording_path.exists():shutil.copyfile(engine.recording_path,folder/'session_video.mp4')
    with (folder/'frames.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS+['link_quality','lead_x_px','lead_y_px','lead_distance_km'],extrasaction='ignore');writer.writeheader();writer.writerows(engine.rows)
    summary=summarize(engine.rows,engine.tracker)
    summary['scenario']=engine.config.name;summary['source_mode']=engine.source;summary['seed']=engine.config.seed
    summary['handovers']=len(engine.handover_events)
    result=compliance(summary);summary['compliance']=result
    for filename,data in [('summary.json',summary),('compliance.json',result),('config_snapshot.json',engine.config.to_dict()),('events.json',engine.events)]:
        (folder/filename).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
    (folder/'summary.txt').write_text(rule_based_summary(summary)+'\n\n'+'\n'.join(f'{k}: {v}' for k,v in summary.items() if k!='compliance')+'\n',encoding='utf-8')
    write_database(folder/'frames.sqlite',engine.rows,COLUMNS,summary)
    write_certificate(folder/'certificate.pdf',summary,result)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        charts=folder/'charts';charts.mkdir()
        series=[('error_over_time','pointing_error_px','Pointing error (px)'),('fps_over_time','instantaneous_fps','Pipeline FPS'),('pan_tilt_over_time','pan_deg','Pan (deg)'),('link_quality','link_quality','Link quality (%)')]
        for name,key,label in series:
            x=[r['timestamp_s'] for r in engine.rows if r.get(key) is not None];y=[r[key] for r in engine.rows if r.get(key) is not None]
            fig,ax=plt.subplots(figsize=(9,3));fig.patch.set_facecolor('#0a1422');ax.set_facecolor('#111e30')
            ax.plot(x,y,color='#6ce5bf',lw=1.4,label=label)
            if name=='pan_tilt_over_time':
                tilt=[r['tilt_deg'] for r in engine.rows if r.get(key) is not None]
                ax.plot(x,tilt,color='#64aefc',lw=1.4,label='Tilt (deg)');ax.legend()
            ax.set(title=label,xlabel='Time (s)',ylabel=label)
            ax.tick_params(colors='#b8c8db');ax.xaxis.label.set_color('#b8c8db');ax.yaxis.label.set_color('#b8c8db');ax.title.set_color('white')
            fig.tight_layout();fig.savefig(charts/(name+'.png'),dpi=125,facecolor=fig.get_facecolor());plt.close(fig)
        err=[r['centroid_error_px'] for r in engine.rows if r['centroid_error_px'] is not None]
        fig,ax=plt.subplots(figsize=(9,3));ax.hist(err or [0],bins=25,color='#6ce5bf');ax.set(xlabel='Centroid error (px)',ylabel='Frames',title='Centroid error distribution')
        fig.tight_layout();fig.savefig(charts/'error_histogram.png',dpi=125);plt.close(fig)
    except ImportError:pass
    if engine.last_annotated is not None:
        import cv2
        cv2.imwrite(str(folder/'last_frame.png'),engine.last_annotated)
    return str(folder)


def write_certificate(path,summary,checks):
    """Minimal valid vector PDF; no external PDF package or Unicode font required."""
    def safe(s):
        return str(s).encode('ascii','replace').decode('ascii').replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    def text(x,y,value,size=11,color=(.82,.9,.94),bold=False):
        r,g,b=color
        ops.append(f'BT /{"F2" if bold else "F1"} {size} Tf {r:.3f} {g:.3f} {b:.3f} rg {x} {y} Td ({safe(value)}) Tj ET')
    def box(x,y,w,h,color):
        r,g,b=color;ops.append(f'{r:.3f} {g:.3f} {b:.3f} rg {x} {y} {w} {h} re f')
    ops=[];box(0,0,612,792,(.035,.077,.115));box(0,755,612,37,(.067,.18,.20))
    text(40,767,'V-CAPAT PRO     /     OPTICAL ACQUISITION LAB',12,(.44,.91,.77),True)
    text(40,705,'SESSION EVIDENCE REPORT',24,(.95,.98,1),True)
    text(40,678,'COARSE ALIGNMENT  /  AUTOMATED METRIC ASSESSMENT',10,(.55,.7,.78))
    statuses=[r['status'] for r in checks.values()]
    ready=bool(statuses) and all(s=='PASS' for s in statuses)
    badge='ALL CHECKS PASS' if ready else 'EVIDENCE INCOMPLETE' if 'N/A' in statuses else 'CHECKS FAILED'
    box(40,610,532,48,(.07,.19,.18) if ready else (.20,.15,.13))
    text(55,628,badge,17,(.44,.91,.77) if ready else (1,.73,.51),True)
    text(40,578,'SCENARIO   '+str(summary.get('scenario','Unnamed'))[:65],11,(.91,.95,.97),True)
    text(40,558,'SOURCE     '+str(summary.get('source_mode','unknown')).upper()+'    /    SEED '+str(summary.get('seed','-')),10)
    text(40,539,'DURATION   '+str(summary.get('duration_s','-'))+' s   /    '+str(summary.get('total_frames','-'))+' frames',10)
    y=490
    for key,result in checks.items():
        box(40,y-17,532,46,(.07,.14,.19));state=result['status']
        text(52,y+8,result['label'],10,(.82,.9,.94),True)
        value=result['value'];text(52,y-7,'Measured: '+('not established' if value is None else str(value)),10,(.55,.7,.78))
        text(482,y,state,12,(.41,.88,.69) if state=='PASS' else (1,.65,.53) if state=='FAIL' else (.63,.7,.78),True)
        y-=55
    text(40,132,'EVALUATION NOTES',10,(.44,.91,.77),True)
    text(40,113,'N/A never counts as a pass. Results apply to this run and configuration only.',9)
    text(40,95,'This is software-generated evidence, NOT an ISRO or flight-qualification certificate.',9,(1,.73,.51))
    box(40,61,532,1,(.20,.36,.39))
    text(40,44,'V-CAPAT PRO  /  DETERMINISTIC FSOC COARSE ALIGNMENT PROTOTYPE',8,(.49,.64,.69))
    stream=('\n'.join(ops)+'\n').encode('latin1')
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
             b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>',
             b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'endstream']
    result=bytearray(b'%PDF-1.4\n%VCAPAT\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(result));result.extend(str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n')
    pos=len(result);result.extend(('xref\n0 '+str(len(offsets))+'\n0000000000 65535 f \n').encode())
    for n in offsets[1:]:result.extend(f'{n:010d} 00000 n \n'.encode())
    result.extend(f'trailer\n<< /Root 1 0 R /Size {len(offsets)} >>\nstartxref\n{pos}\n%%EOF\n'.encode())
    Path(path).write_bytes(result)
    return str(path)
