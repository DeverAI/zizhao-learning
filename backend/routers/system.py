from __future__ import annotations

from fastapi import APIRouter

from config import beijing_today, load_settings, ENABLE_MATERIAL_SYSTEM
from services import agent_bridge, material_service
from models import database as db

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health():
    return {
        "ok": True,
        "service": "zizhao-material-backend",
        "material_system": ENABLE_MATERIAL_SYSTEM,
        "day_key": beijing_today(),
        "shared": agent_bridge.shared_status(),
    }


@router.get("/stats")
async def stats():
    plans = db.list_plan()
    materials = db.list_recent_materials()
    archive = db.list_archive(limit=1000)
    by_status: dict[str, int] = {}
    for p in plans:
        by_status[p.get("status") or "?"] = by_status.get(p.get("status") or "?", 0) + 1
    return {
        "plan_total": len(plans),
        "plan_by_status": by_status,
        "materials_recent_sample": len(materials),
        "archive_total": len(archive),
        "settings": {
            k: load_settings().get(k)
            for k in (
                "material_recent_days",
                "material_dedup_threshold",
                "material_pick_strategy",
                "material_domains",
            )
        },
    }


@router.post("/init")
async def init():
    db.init_db()
    seed = material_service.ensure_seed_plan()
    return {"ok": True, "seed": seed}
