"""Opt-in annotated camera-feed MP4 recording, with explicit open/close lifecycle."""
from pathlib import Path
import cv2

class SessionRecorder:
    def __init__(self,path,fps,resolution):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.writer=cv2.VideoWriter(str(self.path),cv2.VideoWriter_fourcc(*'mp4v'),float(fps),tuple(resolution))
        if not self.writer.isOpened():raise RuntimeError(f'Cannot create MP4 at {path}')
        self.resolution=tuple(resolution);self.frames=0
    def append(self,annotated_bgr):
        if annotated_bgr.shape[1::-1]!=self.resolution:raise ValueError('Frame dimensions differ from recording resolution')
        self.writer.write(annotated_bgr);self.frames+=1
    def close(self):self.writer.release()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
