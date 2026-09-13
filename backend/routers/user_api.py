"""用户自注册 API + 组件离线包路由。"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from routers.auth import current_user
from services import offline_service, user_api_service

router = APIRouter(prefix="/api", tags=["user_api"])


class OpenAIBody(BaseModel):
    base_url: str
    api_key: str
    model: str
    voice: str = Field(default="alloy")


@router.get("/settings/apis")
async def get_apis(user: dict = Depends(current_user)):
    return user_api_service.public_view(user["id"])


@router.post("/settings/apis/text")
async def set_text_api(body: OpenAIBody, user: dict = Depends(current_user)):
    if not body.base_url or not body.api_key or not body.model:
        raise HTTPException(status_code=400, detail="base_url/api_key/model required")
    user_api_service.save_user_apis(
        user["id"], text={"base_url": body.base_url, "api_key": body.api_key, "model": body.model}
    )
    return {"ok": True, "view": user_api_service.public_view(user["id"])}


@router.post("/settings/apis/tts")
async def set_tts_api(body: OpenAIBody, user: dict = Depends(current_user)):
    if not body.base_url or not body.api_key or not body.model:
        raise HTTPException(status_code=400, detail="base_url/api_key/model required")
    user_api_service.save_user_apis(
        user["id"],
        tts={
            "base_url": body.base_url,
            "api_key": body.api_key,
            "model": body.model,
            "voice": body.voice or "alloy",
        },
    )
    return {"ok": True, "view": user_api_service.public_view(user["id"])}


@router.post("/settings/apis/probe")
async def probe_apis(user: dict = Depends(current_user)):
    text = await user_api_service.probe_text(user["id"])
    tts = await user_api_service.probe_tts(user["id"])
    return {
        "text": text,
        "tts": tts,
        "ok": bool(text.get("ok") and tts.get("ok")),
        "note": "至少配置文本+TTS 各一个；失败 degraded=true",
    }


@router.get("/offline/manifest")
async def offline_manifest(user: dict = Depends(current_user)):
    """设备/浏览器拉取：组件清单 + 今日离线包索引。"""
    return offline_service.build_manifest(user["id"])


@router.get("/offline/bundle")
async def offline_bundle(user: dict = Depends(current_user)):
    """今日离线内容 JSON（素材正文/分段文本/常驻摘要/时间表）。无音频时 degraded。"""
    return offline_service.build_daily_bundle(user["id"])


@router.get("/offline/component/{component_id}")
async def offline_component(component_id: str, user: dict = Depends(current_user)):
    return offline_service.component_package(component_id, user["id"])
