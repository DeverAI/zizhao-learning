"""用户自注册 OpenAI 兼容 API（文本 + TTS），三人各用各的 Key。

不落 git；只写 storage/user_api/{user_id}.json。
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

from config import STORAGE_DIR, atomic_write_json, ensure_dirs

API_DIR_NAME = "user_api"


def _path(user_id: str) -> str:
    uid = re.sub(r"[^\w-]", "_", user_id or "anon")[:64] or "anon"
    return os.path.join(STORAGE_DIR, API_DIR_NAME, f"{uid}.json")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_user_apis(user_id: str) -> dict:
    ensure_dirs()
    path = _path(user_id)
    data = {"text": {}, "tts": {}, "updated_at": ""}
    if not os.path.exists(path):
        return data
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            data["text"] = raw.get("text") or {}
            data["tts"] = raw.get("tts") or {}
            data["updated_at"] = raw.get("updated_at") or ""
    except (json.JSONDecodeError, OSError):
        pass
    return data


def _mask_key(key: str) -> str:
    key = key or ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "…" + key[-4:]


def save_user_apis(user_id: str, text: dict | None = None, tts: dict | None = None) -> dict:
    cur = load_user_apis(user_id)
    if text is not None:
        cur["text"] = {
            "base_url": (text.get("base_url") or "").strip().rstrip("/"),
            "api_key": (text.get("api_key") or "").strip(),
            "model": (text.get("model") or "").strip(),
        }
    if tts is not None:
        cur["tts"] = {
            "base_url": (tts.get("base_url") or "").strip().rstrip("/"),
            "api_key": (tts.get("api_key") or "").strip(),
            "model": (tts.get("model") or "").strip(),
            "voice": (tts.get("voice") or "alloy").strip(),
        }
    cur["updated_at"] = _now()
    atomic_write_json(_path(user_id), cur)
    return public_view(user_id)


def public_view(user_id: str) -> dict:
    """对外只回掩码，不回完整 Key。"""
    data = load_user_apis(user_id)
    t, s = data.get("text") or {}, data.get("tts") or {}
    return {
        "text": {
            "base_url": t.get("base_url") or "",
            "model": t.get("model") or "",
            "api_key_masked": _mask_key(t.get("api_key") or ""),
            "configured": bool(t.get("api_key") and t.get("base_url") and t.get("model")),
        },
        "tts": {
            "base_url": s.get("base_url") or "",
            "model": s.get("model") or "",
            "voice": s.get("voice") or "",
            "api_key_masked": _mask_key(s.get("api_key") or ""),
            "configured": bool(s.get("api_key") and s.get("base_url") and s.get("model")),
        },
        "updated_at": data.get("updated_at") or "",
        "note": "OpenAI 兼容 /v1/chat/completions 与 /v1/audio/speech",
    }


def get_text_creds(user_id: str) -> dict:
    t = load_user_apis(user_id).get("text") or {}
    if t.get("api_key") and t.get("base_url") and t.get("model"):
        return {
            "api_key": t["api_key"],
            "base_url": t["base_url"],
            "model": t["model"],
            "source": "user",
        }
    return {}


def get_tts_creds(user_id: str) -> dict:
    s = load_user_apis(user_id).get("tts") or {}
    if s.get("api_key") and s.get("base_url") and s.get("model"):
        return {
            "api_key": s["api_key"],
            "base_url": s["base_url"],
            "model": s["model"],
            "voice": s.get("voice") or "alloy",
            "source": "user",
        }
    return {}


async def probe_text(user_id: str) -> dict:
    """轻量连通性：发 1 token 请求。失败明确 degraded。"""
    import httpx

    cred = get_text_creds(user_id)
    if not cred:
        return {"ok": False, "degraded": True, "error": "text api not configured"}
    url = cred["base_url"]
    if not url.endswith("/chat/completions"):
        url = url + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {cred['api_key']}"},
                json={
                    "model": cred["model"],
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1,
                },
            )
        ok = r.status_code < 400
        return {"ok": ok, "degraded": not ok, "status": r.status_code, "model": cred["model"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "degraded": True, "error": str(exc)[:200]}


async def probe_tts(user_id: str) -> dict:
    import httpx

    cred = get_tts_creds(user_id)
    if not cred:
        return {"ok": False, "degraded": True, "error": "tts api not configured"}
    url = cred["base_url"]
    if not url.endswith("/audio/speech"):
        url = url + "/audio/speech"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {cred['api_key']}"},
                json={
                    "model": cred["model"],
                    "input": "测试",
                    "voice": cred.get("voice") or "alloy",
                    "response_format": "mp3",
                },
            )
        ok = r.status_code < 400 and len(r.content or b"") > 100
        return {"ok": ok, "degraded": not ok, "status": r.status_code, "bytes": len(r.content or b"")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "degraded": True, "error": str(exc)[:200]}


def compose_chat_url(base_url: str) -> str:
    b = (base_url or "").rstrip("/")
    if b.endswith("/chat/completions"):
        return b
    return b + "/chat/completions"


def compose_tts_url(base_url: str) -> str:
    b = (base_url or "").rstrip("/")
    if b.endswith("/audio/speech"):
        return b
    return b + "/audio/speech"
