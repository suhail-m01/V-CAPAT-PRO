"""Bounded, timestamped local application log setup."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging(folder):
    dest=Path(folder);dest.mkdir(parents=True,exist_ok=True)
    log=logging.getLogger('vcapat');log.setLevel(logging.INFO)
    if not log.handlers:
        handler=RotatingFileHandler(dest/'application.log',maxBytes=2_000_000,backupCount=3,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
        log.addHandler(handler)
    return log
