"""自招素材系统后端。

共享来源：`../学习Agent_new`（资料=课程体系/知识树，记忆=海马体 profile）。
本服务只读共享源，本地 SQLite 存素材三态与去重归档。
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import (
    ENABLE_MATERIAL_SYSTEM,
    ENABLE_NIGHT_ARCHIVE,
    BASE_DIR,
    beijing_today,
    ensure_dirs,
    load_settings,
)
from models import database as db
from routers import material as material_router
from routers import shared as shared_router
from routers import system as system_router
from routers import workspace as workspace_router
from services import material_service


async def _night_archive_loop():
    last_date = None
    while True:
        try:
            await asyncio.sleep(60)
            if not ENABLE_NIGHT_ARCHIVE or not ENABLE_MATERIAL_SYSTEM:
                continue
            settings = load_settings()
            if not settings.get("night_patrol_enabled", True):
                continue
            from datetime import datetime, timedelta, timezone

            now = datetime.now(timezone.utc) + timedelta(hours=8)
            today = now.strftime("%Y-%m-%d")
            start = settings.get("night_patrol_start", "01:00")
            end = settings.get("night_patrol_end", "05:00")
            hhmm = now.strftime("%H:%M")
            if start <= end:
                in_window = start <= hhmm <= end
            else:
                in_window = hhmm >= start or hhmm <= end
            if not in_window or last_date == today:
                continue
            last_date = today
            result = material_service.run_archive_once()
            print(f"[night-archive] {result}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 — 后台巡检不应拖垮主服务
            print(f"[night-archive] error: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    db.init_db()
    material_service.ensure_seed_plan()
    task = asyncio.create_task(_night_archive_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="自招素材系统",
    version="0.1.0",
    description="每日自招素材 + 素材挂载对话；资料/记忆共享自 学习Agent_new",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_OPEN_PATHS = {"/", "/docs", "/openapi.json", "/redoc", "/api/system/health"}


@app.middleware("http")
async def optional_bearer_auth(request: Request, call_next):
    """settings.api_password 非空时启用 Bearer；空则本地开放（默认）。"""
    pwd = str(load_settings().get("api_password") or "").strip()
    if not pwd or request.url.path in _OPEN_PATHS or request.url.path.startswith("/static"):
        return await call_next(request)
    auth = request.headers.get("Authorization") or ""
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if token != pwd:
        return JSONResponse({"detail": "unauthorized", "degraded": False}, status_code=401)
    return await call_next(request)

app.include_router(material_router.router)
app.include_router(shared_router.router)
app.include_router(system_router.router)
app.include_router(workspace_router.router)

_static_dir = os.path.join(BASE_DIR, "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
async def root():
    index = os.path.join(_static_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {
        "name": "自招素材系统",
        "day_key": beijing_today(),
        "docs": "/docs",
        "ui": "/static/index.html",
        "today": "/api/material/today",
        "shared": "/api/shared/status",
    }


def create_app() -> FastAPI:
    return app
