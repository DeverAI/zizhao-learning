"""组件离线包 + 当日离线内容。

板子/浏览器：登录后先拉 manifest，再拉 bundle 与各 component 包；
断网时用本地缓存（设备侧负责存储，服务端只提供可下载产物）。
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from config import beijing_today, load_settings
from models import database as db
from services import component_registry, material_service, resident_service, timetable_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def component_package(component_id: str, user_id: str) -> dict:
    """静态组件壳：描述 UI 入口与所需 API，便于板子/浏览器缓存。"""
    meta = component_registry.get_component(component_id)
    if not meta:
        return {"ok": False, "error": "unknown component", "component_id": component_id}
    # 组件清单：路由、依赖接口、是否需要音频
    needs = {
        "zizhao": ["/api/material/today", "/api/material/chat", "/api/quiz/build"],
        "english": ["/api/recitation/next", "/api/recitation/grade"],
        "classics": ["/api/resident?kind=classics", "/api/media/upload"],
        "timetable": ["/api/timetable"],
        "library": ["/api/resident", "/api/media"],
        "devices": ["/api/auth/devices"],
        "home": ["/api/home"],
    }.get(component_id, [])
    payload = {
        "ok": True,
        "component": meta,
        "apis": needs,
        "ui_bundle": {
            "spa_route": meta.get("entry") or f"#/{component_id}",
            "static": ["/static/app.css", "/static/app.js", "/static/index.html"],
        },
        "version": "1",
        "generated_at": _now(),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    payload["etag"] = _sha(raw)
    return payload


def build_daily_bundle(user_id: str) -> dict:
    """当日离线内容：素材全文 + 分段文本 + 常驻 + 时间表 + 背诵一段。"""
    from services import recitation

    day = beijing_today()
    mat = db.get_today_material(day, user_id=user_id)
    from services import review_service

    review = review_service.get_review_fields(mat or {})
    passed = review_service.audio_allowed(mat or {})
    degraded_audio = True
    segments: list[dict] = []
    audio_segments: list[dict] = []
    if mat:
        from services import agent_tools

        seg = agent_tools.dispatch(
            "segment_material_text", {"material_id": mat.get("id") or ""}
        )
        if seg.get("ok"):
            segments = seg.get("segments") or []
        if passed:
            audio_segments = db.list_audio_segments(mat["id"] or "")
            if mat.get("audio_path") or any(s.get("path") for s in audio_segments):
                degraded_audio = False
        else:
            # 未过审：禁止下发音频
            audio_segments = []
            degraded_audio = True

    rec = recitation.pick_random("pending")
    bundle = {
        "ok": True,
        "day_key": day,
        "user_id": user_id,
        "material": (
            {
                "id": mat.get("id"),
                "title": mat.get("title"),
                "source": mat.get("source"),
                "body": mat.get("body"),
                "key_points": mat.get("key_points"),
                "followups": mat.get("followups"),
                "domain": mat.get("domain"),
                "degraded": bool(mat.get("degraded")),
                "audio_path": (mat.get("audio_path") or "") if passed else "",
                **review,
            }
            if mat
            else None
        ),
        "review": review,
        "segments": segments,
        "audio_segments": [
            {"segment_index": s.get("segment_index"), "path": s.get("path"), "text": s.get("text")}
            for s in audio_segments
        ],
        "audio_ready": bool(passed and not degraded_audio and (audio_segments or (mat or {}).get("audio_path"))),
        "audio_blocked_reason": (
            "" if passed else f"review_status={review.get('review_status')}，多轮挑刺未通过，禁止出音频"
        ),
        "resident_sample": resident_service.list_items(user_id)[:20],
        "timetable": timetable_service.list_items(user_id),
        "english_item": (
            {"id": rec.get("id"), "title": rec.get("title"), "passage": rec.get("passage")}
            if rec
            else None
        ),
        "generated_at": _now(),
        "ttl_hint": "建议当日缓存；次日拉新 bundle",
    }
    raw = json.dumps(
        {k: bundle[k] for k in bundle if k != "generated_at"}, ensure_ascii=False, sort_keys=True
    ).encode()
    bundle["etag"] = _sha(raw)
    if not mat:
        bundle["degraded"] = True
        bundle["note"] = "尚无今日素材，请先联网 GET /api/material/today"
    return bundle


def build_manifest(user_id: str) -> dict:
    comps = component_registry.home_payload(user_id).get("components") or []
    items = []
    for c in comps:
        pkg = component_package(c["id"], user_id)
        items.append(
            {
                "id": c["id"],
                "name": c.get("name"),
                "version": pkg.get("version"),
                "etag": pkg.get("etag"),
                "entry": c.get("entry"),
            }
        )
    bundle = build_daily_bundle(user_id)
    settings = load_settings()
    return {
        "ok": True,
        "day_key": beijing_today(),
        "components": items,
        "daily_bundle_etag": bundle.get("etag"),
        "daily_bundle_ready": bool(bundle.get("material")),
        "audio_ready": bool(bundle.get("audio_ready")),
        "download": {
            "manifest": "/api/offline/manifest",
            "bundle": "/api/offline/bundle",
            "component": "/api/offline/component/{id}",
        },
        "device_policy": {
            "login": "POST /api/auth/device/login",
            "on_boot": ["login_or_local_cache", "manifest", "bundle", "components"],
            "background_refresh_min": 30,
            "volume_idle_sec": settings.get("device_volume_idle_sec", 600),
            "volume_idle_level": settings.get("device_volume_idle_level", 1),
            # 自动开关机（防死锁：关机前停播、flush 进度、再 deep sleep / 定时唤醒）
            "power": {
                "enabled": bool(settings.get("device_power_enabled", True)),
                "shutdown_hhmm": settings.get("device_power_off", "04:30"),
                "boot_hhmm": settings.get("device_power_on", "06:00"),
                # 开机后无有效活动（播音/按键/下载）则再次关机
                "reboot_idle_sec": settings.get("device_boot_idle_sec", 900),
                "valid_activity": ["playing", "button", "download", "volume_change"],
            },
            "provision": {
                "online": "POST /api/auth/device/login",
                "onsite": {
                    "ap_ssid_prefix": "Zizhao-Setup-",
                    "captive_portal": "http://192.168.4.1/",
                    "fields": ["wifi_ssid", "wifi_pass", "server_url", "device_id", "passkey"],
                    "fallback": "串口/NVS 写入 device_id+passkey+server_url，无网也可先缓存",
                },
            },
        },
        "generated_at": _now(),
    }
