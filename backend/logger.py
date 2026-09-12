"""轻量日志：写 storage/logs/app.log，GBK 控制台安全。"""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from config import STORAGE_DIR, ensure_dirs

_configured = False


def get_logger(name: str = "zizhao") -> logging.Logger:
    global _configured
    ensure_dirs()
    logger = logging.getLogger(name)
    if _configured:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = os.path.join(STORAGE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "app.log")
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    # 避免重复打到 root
    logger.propagate = False
    _configured = True
    return logger


def log_error(where: str, msg: str) -> None:
    get_logger().error("%s: %s", where, msg)
