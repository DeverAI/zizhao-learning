"""平台路由：组件主页、时间表、常驻资料、上传整理。"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from models import database as db
from routers.auth import current_user
from services import (
    component_registry,
    media_service,
    resident_service,
    security,
    timetable_service,
)

router = APIRouter(prefix="/api", tags=["platform"])


@router.get("/home")
async def home(user: dict = Depends(current_user)):
    return component_registry.home_payload(user["id"])


@router.get("/components/catalog")
async def catalog():
    return {"items": component_registry.catalog()}


class ComponentToggleBody(BaseModel):
    component_id: str
    enabled: bool = True
    config: dict = {}


@router.post("/components/toggle")
async def toggle_component(body: ComponentToggleBody, user: dict = Depends(current_user)):
    if not component_registry.get_component(body.component_id):
        raise HTTPException(status_code=404, detail="unknown component")
    component_registry.ensure_user_defaults(user["id"])
    items = db.list_user_components(user["id"])
    found = False
    for it in items:
        if it["component_id"] == body.component_id:
            it["enabled"] = body.enabled
            it["config"] = body.config or it.get("config") or {}
            found = True
    if not found:
        items.append(
            {
                "component_id": body.component_id,
                "enabled": body.enabled,
                "order_index": len(items),
                "config": body.config or {},
            }
        )
    db.set_user_components(user["id"], items)
    return {"ok": True, "components": db.list_user_components(user["id"])}


class ComponentRequestBody(BaseModel):
    title: str
    description: str = ""


@router.post("/components/request")
async def request_component(body: ComponentRequestBody, user: dict = Depends(current_user)):
    title = security.sanitize_text(body.title, 80)
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    rid = db.insert_component_request(
        {
            "user_id": user["id"],
            "title": title,
            "description": security.sanitize_text(body.description, 1000),
        }
    )
    return {"ok": True, "id": rid}


# ---------------------------------------------------------------- timetable

class TimetableAdd(BaseModel):
    title: str
    weekday: int = 0
    start: str = "08:00"
    end: str = "09:00"
    component: str = ""
    note: str = ""


@router.get("/timetable")
async def timetable_list(user: dict = Depends(current_user)):
    return {"items": timetable_service.list_items(user["id"]), "weekdays": timetable_service.WEEKDAYS}


@router.post("/timetable")
async def timetable_add(body: TimetableAdd, user: dict = Depends(current_user)):
    try:
        item = timetable_service.add_item(
            user["id"], body.title, body.weekday, body.start, body.end, body.component, body.note
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "item": item}


class TimetableBulk(BaseModel):
    text: str


@router.post("/timetable/bulk")
async def timetable_bulk(body: TimetableBulk, user: dict = Depends(current_user)):
    return timetable_service.bulk_from_text(user["id"], body.text)


@router.delete("/timetable/{item_id}")
async def timetable_delete(item_id: str, user: dict = Depends(current_user)):
    ok = timetable_service.delete_item(user["id"], item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


# ---------------------------------------------------------------- resident

class ResidentAdd(BaseModel):
    title: str
    body: str = ""
    kind: str = "note"
    tags: list[str] = []
    source: str = ""


@router.get("/resident")
async def resident_list(kind: Optional[str] = None, user: dict = Depends(current_user)):
    return {"items": resident_service.list_items(user["id"], kind=kind)}


@router.post("/resident")
async def resident_add(body: ResidentAdd, user: dict = Depends(current_user)):
    try:
        item = resident_service.add(
            user["id"], body.title, body.body, body.kind, body.tags, body.source
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "item": item}


@router.get("/resident/search")
async def resident_search(q: str = "", user: dict = Depends(current_user)):
    return {"items": resident_service.search(user["id"], q)}


@router.delete("/resident/{item_id}")
async def resident_delete(item_id: str, user: dict = Depends(current_user)):
    if not resident_service.delete(user["id"], item_id):
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True}


# ---------------------------------------------------------------- media upload

@router.post("/media/upload")
async def media_upload(
    request: Request,
    file: UploadFile = File(...),
    make_mp3: bool = Form(True),
    component: str = Form("library"),
    user: dict = Depends(current_user),
):
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("upload", f"{user['id']}:{ip}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many uploads") from exc
    content = await file.read()
    try:
        result = media_service.ingest_upload(
            user["id"], file.filename or "file.bin", content, make_mp3=make_mp3, component=component
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "item": result}


@router.get("/media")
async def media_list(user: dict = Depends(current_user)):
    return {"items": db.list_media_files(user["id"])}


@router.get("/media/{media_id}")
async def media_detail(media_id: str, user: dict = Depends(current_user)):
    rec = db.get_media_file(user["id"], media_id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    rec.pop("path", None)
    return rec


@router.get("/media/{media_id}/download")
async def media_download(media_id: str, user: dict = Depends(current_user)):
    from fastapi.responses import FileResponse

    rec = db.get_media_file(user["id"], media_id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    path = rec.get("mp3_path") or rec.get("path") or ""
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    return FileResponse(path, filename=os.path.basename(path))
