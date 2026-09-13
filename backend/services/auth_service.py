"""注册/登录：邮箱验证码、PassKey（浏览器+ESP 设备）、sid Cookie 会话。"""
from __future__ import annotations

import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from config import (
    EMAIL_CODE_TTL_SEC,
    SID_COOKIE_NAME,
    SID_TTL_DAYS,
    USERS_DIR,
    atomic_write_json,
    ensure_dirs,
    load_settings,
)
from models import database as db
from services import security


class AuthError(Exception):
    def __init__(self, msg: str, status: int = 400):
        self.status = status
        super().__init__(msg)


def _now() -> float:
    return time.time()


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _user_path(user_id: str) -> str:
    return os.path.join(USERS_DIR, f"{user_id}.json")


def create_user(email: str, display_name: str = "") -> dict:
    email = (email or "").strip().lower()
    if not security.valid_email(email):
        raise AuthError("invalid email")
    existing = db.find_user_by_email(email)
    if existing:
        return existing
    uid = db.gen_id()
    user = {
        "id": uid,
        "email": email,
        "display_name": display_name or email.split("@")[0],
        "created_at": _iso(),
        "components": ["home", "zizhao", "english", "classics"],
    }
    db.insert_user(user)
    atomic_write_json(
        _user_path(uid),
        {"id": uid, "email": email, "created_at": user["created_at"]},
    )
    return user


def issue_email_code(email: str) -> dict:
    email = (email or "").strip().lower()
    if not security.valid_email(email):
        raise AuthError("invalid email")
    code = f"{secrets.randbelow(1000000):06d}"
    db.put_email_code(email, code, expires_at=_now() + EMAIL_CODE_TTL_SEC)
    _send_email(email, "自招学习登录验证码", f"你的验证码是 {code}，{EMAIL_CODE_TTL_SEC // 60} 分钟内有效。")
    # 不回显真实验证码；dev 且未配 SMTP 时 outbox 可读
    settings = load_settings()
    smtp_on = bool(settings.get("smtp_host"))
    from config import EMAIL_OUTBOX

    return {
        "ok": True,
        "email": email,
        "ttl_sec": EMAIL_CODE_TTL_SEC,
        "delivery": "smtp" if smtp_on else "local_outbox",
        "dev_hint": "" if smtp_on else f"dev code stored in {EMAIL_OUTBOX}",
    }


def _send_email(to: str, subject: str, body: str) -> None:
    from config import EMAIL_OUTBOX

    settings = load_settings()
    entry = {"to": to, "subject": subject, "body": body, "at": _iso()}
    # 本地 outbox（脱敏：不进 git，storage 已 ignore）
    outbox = []
    if os.path.exists(EMAIL_OUTBOX):
        try:
            with open(EMAIL_OUTBOX, encoding="utf-8") as f:
                outbox = json.load(f)
            if not isinstance(outbox, list):
                outbox = []
        except (json.JSONDecodeError, OSError):
            outbox = []
    outbox.append(entry)
    atomic_write_json(EMAIL_OUTBOX, outbox[-50:])
    host = settings.get("smtp_host") or ""
    if not host:
        return
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.get("smtp_from") or settings.get("smtp_user") or ""
        msg["To"] = to
        with smtplib.SMTP(host, int(settings.get("smtp_port") or 587), timeout=15) as s:
            s.starttls()
            user = settings.get("smtp_user") or ""
            pwd = settings.get("smtp_password") or ""
            if user:
                s.login(user, pwd)
            s.sendmail(msg["From"], [to], msg.as_string())
    except Exception:  # noqa: BLE001 — 邮件失败不阻断（outbox 已有）
        pass


def verify_email_code(email: str, code: str) -> bool:
    email = (email or "").strip().lower()
    return db.consume_email_code(email, (code or "").strip(), now=_now())


def login_with_email_code(email: str, code: str) -> tuple[dict, str]:
    if not verify_email_code(email, code):
        raise AuthError("invalid or expired code", 401)
    user = create_user(email)
    sid = create_session(user["id"], kind="user")
    return user, sid


def create_session(user_id: str, kind: str = "user", device_id: str = "") -> str:
    sid = secrets.token_urlsafe(24).replace("-", "a").replace("_", "b")
    # 保证匹配 safe_sid
    sid = "s" + "".join(c for c in sid if c.isalnum() or c in "-_")[:40]
    if not security.safe_sid(sid):
        sid = "s" + secrets.token_hex(16)
    expires = datetime.now(timezone.utc) + timedelta(days=SID_TTL_DAYS)
    db.insert_session(
        {
            "sid": sid,
            "user_id": user_id,
            "kind": kind,
            "device_id": device_id,
            "created_at": _iso(),
            "expires_at": expires.isoformat(),
        }
    )
    return sid


def resolve_sid(sid: str) -> Optional[dict]:
    if not security.safe_sid(sid):
        return None
    sess = db.get_session(sid)
    if not sess:
        return None
    try:
        exp = datetime.fromisoformat(str(sess.get("expires_at")).replace("Z", "+00:00"))
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            db.delete_session(sid)
            return None
    except (TypeError, ValueError):
        return None
    user = db.get_user(sess.get("user_id") or "")
    return {"session": sess, "user": user}


def destroy_session(sid: str) -> None:
    if sid:
        db.delete_session(sid)


# ---------------------------------------------------------------- PassKey

def register_passkey_begin(user_id: str) -> dict:
    """浏览器 WebAuthn 简化：返回 challenge 与 rp 信息。"""
    challenge = secrets.token_urlsafe(32)
    db.put_pending_passkey(user_id, challenge, _now() + 300)
    return {
        "challenge": challenge,
        "rp_id": "localhost",
        "rp_name": "自招学习",
        "user_id": user_id,
        "timeout_ms": 60000,
    }


def register_passkey_finish(user_id: str, challenge: str, credential_id: str, public_key: str) -> dict:
    ok = db.consume_pending_passkey(user_id, challenge, _now())
    if not ok:
        raise AuthError("passkey challenge expired", 401)
    cred_id = (credential_id or "").strip()
    if len(cred_id) < 8 or len(cred_id) > 200:
        raise AuthError("invalid credential_id")
    db.upsert_passkey(
        {
            "credential_id": cred_id,
            "user_id": user_id,
            "public_key": (public_key or "")[:2000],
            "kind": "web",
            "created_at": _iso(),
        }
    )
    return {"ok": True, "credential_id": cred_id}


def begin_passkey_login(credential_id: str) -> dict:
    """登录前必须先取服务端 challenge（一次性）。"""
    rec = db.get_passkey(credential_id)
    if not rec:
        raise AuthError("unknown credential", 401)
    challenge = secrets.token_urlsafe(32)
    db.put_pending_passkey(rec["user_id"], challenge, _now() + 300)
    return {"challenge": challenge, "credential_id": credential_id, "expires_in_sec": 300}


def login_with_passkey(credential_id: str, challenge: str, signature: str) -> tuple[dict, str]:
    """简化 PassKey：服务端一次性 challenge + HMAC(public_key, challenge)。"""
    rec = db.get_passkey(credential_id)
    if not rec:
        raise AuthError("unknown credential", 401)
    if not challenge or not signature:
        raise AuthError("missing challenge/signature", 401)
    # 必须使用服务端发过且未消费的 challenge（防重放）
    owner_uid = rec.get("user_id") or ""
    if not db.consume_pending_passkey(owner_uid, challenge, _now()):
        raise AuthError("invalid or reused challenge", 401)
    pub = str(rec.get("public_key") or "")
    if not pub:
        raise AuthError("credential has no public_key", 401)
    expected = security.hmac_public_key(pub, challenge)
    if not secrets.compare_digest(expected, signature.strip()):
        raise AuthError("bad passkey signature", 401)
    user = db.get_user(rec["user_id"])
    if not user:
        raise AuthError("user missing", 401)
    sid = create_session(user["id"], kind="passkey")
    return user, sid


# ---------------------------------------------------------------- ESP 设备 PassKey

def provision_device(user_id: str, name: str = "esp-s3") -> dict:
    """为小盒子生成可烧录 PassKey（仅创建时完整返回一次）。"""
    token = secrets.token_urlsafe(32)
    device_id = "dev_" + secrets.token_hex(8)
    rec = {
        "device_id": device_id,
        "user_id": user_id,
        "name": name or "esp-s3",
        "passkey_hash": security.hash_secret(token),
        "created_at": _iso(),
        "revoked": 0,
    }
    db.upsert_device(rec)
    return {
        "device_id": device_id,
        "passkey": token,  # 仅此一次
        "name": rec["name"],
        "note": "烧录到 ESP-S3；丢失请 revoke 后重发",
    }


def revoke_device(user_id: str, device_id: str) -> dict:
    dev = db.get_device(device_id)
    if not dev or dev.get("user_id") != user_id:
        raise AuthError("device not found", 404)
    db.revoke_device(device_id)
    db.delete_sessions_for_device(device_id)
    return {"ok": True, "device_id": device_id}


def login_with_device_passkey(device_id: str, passkey: str) -> tuple[dict, str]:
    dev = db.get_device(device_id)
    if not dev or dev.get("revoked"):
        raise AuthError("device revoked or missing", 401)
    if not hmac_device(dev, passkey):
        raise AuthError("bad passkey", 401)
    user = db.get_user(dev["user_id"])
    if not user:
        raise AuthError("user missing", 401)
    sid = create_session(user["id"], kind="device", device_id=device_id)
    return user, sid


def hmac_device(dev: dict, passkey: str) -> bool:
    return secrets.compare_digest(
        security.hash_secret(passkey or ""), str(dev.get("passkey_hash") or "")
    )


def list_devices(user_id: str) -> list[dict]:
    return [
        {k: v for k, v in d.items() if k != "passkey_hash"}
        for d in db.list_devices(user_id)
    ]


def set_cookie_token() -> str:
    return SID_COOKIE_NAME
