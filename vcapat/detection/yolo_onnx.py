"""Optional OpenCV-DNN inference for a compatible beacon-specific ONNX model.

No model is bundled: generic COCO YOLO weights cannot detect a synthetic beacon ID.
Supported exported output must be N×5 rows [x0,y0,x1,y1,confidence] in model pixels.
"""
from pathlib import Path
import cv2
import numpy as np
from .base import Detection

class ONNXBeaconDetector:
    def __init__(self,model_path,input_size=(640,480)):
        path=Path(model_path)
        if not path.is_file():raise FileNotFoundError(f'Beacon ONNX weights not found: {path}. See assets/models/README.md')
        self.net=cv2.dnn.readNetFromONNX(str(path));self.input_size=input_size
    def detect(self,frame,prediction=None,gate_px=None):
        h,w=frame.shape[:2]
        bgr=cv2.cvtColor(frame,cv2.COLOR_GRAY2BGR) if frame.ndim==2 else frame
        blob=cv2.dnn.blobFromImage(bgr,1/255,self.input_size,swapRB=True)
        self.net.setInput(blob);output=np.asarray(self.net.forward()).reshape(-1,5)
        candidates=[]
        for x0,y0,x1,y1,confidence in output:
            if confidence<.25:continue
            x=(x0+x1)*.5*w/self.input_size[0];y=(y0+y1)*.5*h/self.input_size[1]
            if not 0<=x<w or not 0<=y<h:continue
            if prediction is not None and gate_px is not None and np.hypot(x-prediction[0],y-prediction[1])>gate_px:continue
            candidates.append(Detection(float(x),float(y),float(confidence),(int(x0*w/self.input_size[0]),int(y0*h/self.input_size[1]),int((x1-x0)*w/self.input_size[0]),int((y1-y0)*h/self.input_size[1]))))
        return max(candidates,key=lambda d:d.confidence,default=Detection())
