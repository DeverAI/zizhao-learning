"""设备固件清单：仅后台 OTA 拉取，不提供用户升级 UI。"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException

from config import load_settings
from routers.auth import current_user
from services import security

router = APIRouter(prefix="/api/device", tags=["device_fw"])


@router.get("/firmware/latest")
async def firmware_latest(user: dict = Depends(current_user)):
    """
    固件后台更新契约（板端定时拉，**无用户按钮**）。

    部署时把文件放到 storage/firmware/：
      manifest.json  {"version":"1.0.1","url":"http://host:8010/api/device/firmware/bin","sha256":"..."}
      firmware.bin
    未配置则 404，板端静默跳过。
    """
    from config import STORAGE_DIR

    man = os.path.join(STORAGE_DIR, "firmware", "manifest.json")
    if not os.path.exists(man):
        raise HTTPException(status_code=404, detail="no firmware manifest")
    import json

    try:
        with open(man, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(status_code=500, detail="bad manifest") from exc
    if not isinstance(data, dict) or not data.get("version"):
        raise HTTPException(status_code=500, detail="manifest missing version")
    return {
        "version": data.get("version"),
        "url": data.get("url") or "/api/device/firmware/bin",
        "sha256": data.get("sha256") or "",
        "policy": "background_only_no_user_ui",
        "note": "固件只允许后台更新，不允许用户直接更新",
    }


@router.get("/firmware/bin")
async def firmware_bin(user: dict = Depends(current_user)):
    from fastapi.responses import FileResponse
    from config import STORAGE_DIR

    path = os.path.join(STORAGE_DIR, "firmware", "firmware.bin")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="firmware.bin not found")
    return FileResponse(path, filename="firmware.bin", media_type="application/octet-stream")
