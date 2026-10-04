"""Scripted evidence montage from fresh seeded scenarios, never a guaranteed pass."""
from pathlib import Path
import cv2
import numpy as np
from ..config.settings import Scenario
from ..core.engine import Engine

def produce_demo(root,scenario_files,duration_s=180,fps=20):
    if not 5<=duration_s<=240 or not 5<=fps<=30:raise ValueError('Demo length/FPS out of range')
    files=[Path(p) for p in scenario_files]
    if not files:raise ValueError('Supply scenario files')
    output=Path(root);output.parent.mkdir(parents=True,exist_ok=True)
    size=(640,480);writer=cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*'mp4v'),fps,size)
    if not writer.isOpened():raise RuntimeError('OpenCV cannot encode MP4 on this machine')
    total=duration_s*fps;per=max(1,(total-len(files)*fps)//len(files));written=0
    try:
        for file in files:
            config=Scenario.load(file)
            card=np.full((size[1],size[0],3),(20,35,43),np.uint8)
            cv2.putText(card,'V-CAPAT PRO / FSOC COARSE ACQUISITION',(23,45),cv2.FONT_HERSHEY_SIMPLEX,.6,(180,237,192),1,cv2.LINE_AA)
            cv2.putText(card,config.name[:40],(34,235),cv2.FONT_HERSHEY_SIMPLEX,.9,(235,244,238),2,cv2.LINE_AA)
            cv2.putText(card,'Seed '+str(config.seed)+'  |  Simulation, not flight evidence',(35,276),cv2.FONT_HERSHEY_SIMPLEX,.48,(170,192,198),1,cv2.LINE_AA)
            for _ in range(min(fps,total-written)):writer.write(card);written+=1
            engine=Engine(config)
            try:
                for _ in range(min(per,total-written)):
                    engine.step();image=cv2.resize(engine.last_annotated,size)
                    writer.write(image);written+=1
            finally:engine.close()
        while written<total:writer.write(card);written+=1
    finally:writer.release()
    return {'file':str(output),'frames':written,'fps':fps,'seconds':duration_s,
            'note':'Scenario montage with title cards; no royalty-free music or voice narration bundled. Performance not guaranteed.'}
