"""Minimal Python client for a trusted local V-CAPAT web server.

No authentication is provided by the demo server. Never use across untrusted
networks or treat it as an Internet-facing service.
"""
import json
from urllib.request import Request,urlopen

class Client:
    def __init__(self,base='http://127.0.0.1:8000',timeout=30):
        if not base.startswith(('http://','https://')):raise ValueError('HTTP(S) base required')
        self.base=base.rstrip('/');self.timeout=timeout
    def _call(self,path,data=None):
        req=Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,
                    headers={'Content-Type':'application/json'} if data is not None else {})
        with urlopen(req,timeout=self.timeout) as response:return json.load(response)
    def state(self):return self._call('/api/state')
    def presets(self):return self._call('/api/presets')
    def control(self,action,**kwargs):return self._call('/api/control',{'action':action,**kwargs})
    def select(self,preset_id):return self._call('/api/scenario',{'id':preset_id})
    def configure(self,**sections):return self._call('/api/config',sections)
    def benchmark(self,frames=90):return self._call('/api/baseline',{'frames':frames})
    def query(self,threshold=15,metric='pointing'):
        from urllib.parse import urlencode
        return self._call('/api/query?'+urlencode({'min_error':threshold,'metric':metric}))
