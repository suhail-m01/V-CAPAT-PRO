"""Small synchronous in-process pub/sub with safe subscriber isolation."""
from collections import defaultdict
import logging
from threading import RLock

class EventBus:
    def __init__(self):self._listeners=defaultdict(list);self._lock=RLock()
    def subscribe(self,event_type,callback):
        with self._lock:self._listeners[event_type].append(callback)
        return lambda:self.unsubscribe(event_type,callback)
    def unsubscribe(self,event_type,callback):
        with self._lock:
            if callback in self._listeners[event_type]:self._listeners[event_type].remove(callback)
    def publish(self,event):
        with self._lock:subscribers=tuple(self._listeners[event.get('event')])+tuple(self._listeners['*'])
        for callback in subscribers:
            try:callback(event)
            except Exception:logging.exception('Event subscriber failed for %s',event.get('event'))
