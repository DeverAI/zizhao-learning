"""轻量日志：写 storage/logs/app.log，GBK 控制台安全。

外加项目强制的 **Err.log 存错机制**（见根 AGENT.txt）：
运行时错误不得被吞没，必须落到项目根 Err.log；
修复前先 read_errlog()，修复后 clear_errlog()。
"""
from __future__ import annotations

import logging
import os
import threading
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from config import BASE_DIR, ensure_dirs

# 项目根 Err.log（文档单套制：全项目只此一份）
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ERR_LOG_PATH = os.path.join(PROJECT_ROOT, "Err.log")

_configured = False
_err_lock = threading.Lock()


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
    record_error(where, msg)


# ---------------------------------------------------------------- Err.log

def _stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def record_error(where: str, exc_or_msg: object = "", level: str = "ERROR") -> str:
    """把错误追加到项目根 Err.log。返回写入的一行（便于测试与回显）。"""
    if isinstance(exc_or_msg, BaseException):
        detail = f"{type(exc_or_msg).__name__}: {exc_or_msg}"
        tb = traceback.format_exception(type(exc_or_msg), exc_or_msg, exc_or_msg.__traceback__)
        if tb:
            detail += "\n" + "".join(tb[-6:]).rstrip()
    else:
        detail = str(exc_or_msg or "")
    line = f"[{_stamp()}] {level} {where}: {detail}"
    try:
        with _err_lock:
            with open(ERR_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError:
        pass
    try:
        get_logger().error("%s", line)
    except Exception:  # noqa: BLE001 — 日志本身不得再抛
        pass
    return line


def read_errlog() -> str:
    """修复前必读。文件不存在返回空串。"""
    if not os.path.exists(ERR_LOG_PATH):
        return ""
    try:
        with open(ERR_LOG_PATH, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def clear_errlog() -> bool:
    """修复完成后清空内容（不删除文件）。"""
    try:
        with _err_lock:
            with open(ERR_LOG_PATH, "w", encoding="utf-8") as f:
                f.write("")
        return True
    except OSError:
        return False
