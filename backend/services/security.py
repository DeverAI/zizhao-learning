"""安全：限流、输入消毒、签名 Cookie、简单注入过滤。"""
from __future__ import annotations

import hashlib
import hmac
import re
import time
from collections import defaultdict, deque
from typing import Deque

from config import RATE_LIMIT, SESSION_SECRET

_buckets: dict[str, Deque[float]] = defaultdict(deque)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SID_RE = re.compile(r"^[A-Za-z0-9_-]{16,80}$")
# 常见注入/遍历特征（粗过滤，不替代参数化 SQL）
_INJECT_RE = re.compile(
    r"(?i)(\bunion\b\s+\bselect\b|\bor\b\s+1\s*=\s*1|;\s*drop\b|;\s*delete\b|<script\b|\.\./|\.\.\\)"
)


class RateLimitError(Exception):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"rate limited, retry in {retry_after}s")


def check_rate_limit(bucket: str, key: str) -> None:
    cfg = RATE_LIMIT.get(bucket) or RATE_LIMIT["default"]
    now = time.time()
    q = _buckets[f"{bucket}:{key}"]
    window = int(cfg["window_sec"])
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= int(cfg["max"]):
        retry = max(1, int(window - (now - q[0])))
        raise RateLimitError(retry)
    q.append(now)


def valid_email(email: str) -> bool:
    e = (email or "").strip().lower()
    return bool(_EMAIL_RE.match(e)) and len(e) <= 254 and not _INJECT_RE.search(e)


def sanitize_text(text: str, max_len: int = 8000) -> str:
    t = (text or "").strip()
    if _INJECT_RE.search(t):
        # 保留原文但去掉危险片段标记供审计；正文仍入库时用参数化
        t = _INJECT_RE.sub(" ", t)
    return t[:max_len]


def safe_sid(sid: str) -> bool:
    return bool(_SID_RE.match(sid or ""))


def sign_sid(sid: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), sid.encode(), hashlib.sha256).hexdigest()[:32]


def make_session_token(sid: str) -> str:
    return f"{sid}.{sign_sid(sid)}"


def verify_session_token(token: str) -> str | None:
    if not token or "." not in token:
        return None
    sid, sig = token.rsplit(".", 1)
    if not safe_sid(sid):
        return None
    if not hmac.compare_digest(sign_sid(sid), sig or ""):
        return None
    return sid


def hash_secret(secret: str) -> str:
    return hashlib.sha256(f"zizhao:{secret}".encode()).hexdigest()


def hmac_public_key(public_key: str, challenge: str) -> str:
    """简化 PassKey 签名：HMAC-SHA256(public_key, challenge) hex。"""
    return hmac.new(
        (public_key or "").encode("utf-8"),
        (challenge or "").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def client_ip(request) -> str:
    """直连时忽略 X-Forwarded-For，防伪造绕过限流。"""
    client = getattr(request, "client", None)
    if client is not None and getattr(client, "host", None):
        return str(client.host)[:64]
    return "unknown"
