"""Opt-in trusted local plugin discovery, loading and result adaptation."""
import importlib.util
from pathlib import Path
import numpy as np
from ..detection.base import Detection

DEFAULT_FOLDER=Path(__file__).resolve().parents[2]/'plugins'

def discover(folder=DEFAULT_FOLDER):
    root=Path(folder)
    return sorted(p.stem for p in root.glob('*.py') if p.is_file() and p.stem.startswith('example_'))

def load_plugin(name,folder=DEFAULT_FOLDER):
    if not name.isidentifier():raise ValueError('Plugin name must be an identifier')
    file=Path(folder)/(name+'.py')
    if not file.is_file():raise FileNotFoundError(f'Trusted local plugin not found: {name}')
    spec=importlib.util.spec_from_file_location('_vcapat_extension_'+name,file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    kind=getattr(module,'PLUGIN_KIND',None)
    cls=getattr(module,'PLUGIN_CLASS',None)
    if kind not in ('detector','controller') or not isinstance(cls,type):
        raise TypeError('Plugin must export PLUGIN_KIND and PLUGIN_CLASS')
    instance=cls()
    if not callable(getattr(instance,'detect' if kind=='detector' else 'step',None)):
        raise TypeError('Plugin does not implement its declared interface')
    return kind,instance

class DetectorAdapter:
    def __init__(self,name,instance):self.mode='plugin:'+name;self.plugin=instance
    def detect(self,frame,prediction=None,gate_px=None):
        result=self.plugin.detect(frame,prediction,gate_px)
        if isinstance(result,Detection):return result
        if isinstance(result,tuple) and len(result)==3:
            x,y,confidence=result
            return Detection(float(x),float(y),float(np.clip(confidence,0,1)))
        raise TypeError('Detector plugin must return Detection or (x,y,confidence)')
