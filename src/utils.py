import logging
import os
from logging.handlers import RotatingFileHandler

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_logger(name: str, logfile: str, level=logging.INFO):
    ensure_dir(os.path.dirname(logfile) or ".")
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=3)
        fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger
