"""审核 API + 设备现场配网配置。"""
from __future__ import annotations

import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config import SETTINGS_FILE, STORAGE_DIR, atomic_write_json, load_settings, save_settings
from models import database as db
from routers.auth import current_user
from services import review_service, user_api_service

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/review/run")
async def run_review(user: dict = Depends(current_user), material_id: str = ""):
    """立刻对今日（或指定）素材跑多轮挑刺；audio_allowed 仅 passed 时 true。"""
    if material_id:
        result = await review_service.run_review_loop(material_id, user_id=user["id"])
    else:
        result = await review_service.review_today(user_id=user["id"])
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "review failed")
    return result


@router.get("/review/today")
async def review_status(user: dict = Depends(current_user)):
    from config import beijing_today

    mat = db.get_today_material(beijing_today(), user_id=user["id"])
    if not mat:
        return {"ok": False, "error": "no material"}
    fields = review_service.get_review_fields(mat)
    return {
        "ok": True,
        "material_id": mat["id"],
        "title": mat.get("title"),
        **fields,
        "audio_allowed": review_service.audio_allowed(mat),
        "audio_path": (mat.get("audio_path") or "") if review_service.audio_allowed(mat) else "",
    }


class DevicePowerBody(BaseModel):
    enabled: bool = True
    shutdown_hhmm: str = Field(default="04:30", pattern=r"^\d{1,2}:\d{2}$")
    boot_hhmm: str = Field(default="06:00", pattern=r"^\d{1,2}:\d{2}$")
    boot_idle_sec: int = Field(default=900, ge=60, le=3600)
    volume_idle_sec: int = Field(default=600, ge=60, le=3600)


@router.get("/device/power")
async def get_power(user: dict = Depends(current_user)):
    s = load_settings()
    return {
        "enabled": bool(s.get("device_power_enabled", True)),
        "shutdown_hhmm": s.get("device_power_off", "04:30"),
        "boot_hhmm": s.get("device_power_on", "06:00"),
        "boot_idle_sec": int(s.get("device_boot_idle_sec", 900)),
        "volume_idle_sec": int(s.get("device_volume_idle_sec", 600)),
        "note": "板端执行；关机前停播并保存 progress，RTC/定时唤醒再开机",
    }


@router.post("/device/power")
async def set_power(body: DevicePowerBody, user: dict = Depends(current_user)):
    s = load_settings()
    s["device_power_enabled"] = body.enabled
    s["device_power_off"] = body.shutdown_hhmm
    s["device_power_on"] = body.boot_hhmm
    s["device_boot_idle_sec"] = body.boot_idle_sec
    s["device_volume_idle_sec"] = body.volume_idle_sec
    save_settings(s)
    return {"ok": True, **(await get_power(user))}


class OnsiteConfigBody(BaseModel):
    wifi_ssid: str
    wifi_pass: str = ""
    server_url: str = Field(description="http://host:port")
    device_id: str
    passkey: str


@router.post("/device/onsite-config")
async def onsite_config(body: OnsiteConfigBody, user: dict = Depends(current_user)):
    """生成现场配网文件（板子 AP 门户提交后服务端也可校验凭据）。

    真正烧进 NVS 由板端完成；这里校验 device 归属并返回可下载 JSON。
    """
    dev = db.get_device(body.device_id)
    if not dev or dev.get("revoked") or dev.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="device not owned or revoked")
    # 不回显 passkey 明文到日志；文件仅供一次性配网
    import json as _json

    payload = {
        "wifi_ssid": body.wifi_ssid[:64],
        "wifi_pass": body.wifi_pass[:64],
        "server_url": body.server_url.rstrip("/"),
        "device_id": body.device_id,
        "passkey": body.passkey,
        "generated_for": user["id"],
    }
    path = os.path.join(STORAGE_DIR, "device_provision", f"{body.device_id}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    atomic_write_json(path, payload)
    return {
        "ok": True,
        "device_id": body.device_id,
        "hint": "板子开 AP Zizhao-Setup-* → 门户粘贴或串口写入；勿把 passkey 提交到 git",
    }
