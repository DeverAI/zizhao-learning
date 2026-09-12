from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import agent_bridge, material_service
from models import database as db
from config import load_settings

router = APIRouter(prefix="/api/material", tags=["material"])


class RefreshBody(BaseModel):
    domain: Optional[str] = Field(default=None, description="philosophy|history|classics|shared_curriculum|any")


class ChatBody(BaseModel):
    session_id: Optional[str] = None
    material_id: Optional[str] = None
    message: str


class FeedbackBody(BaseModel):
    material_id: str
    vote: str  # up/down/skip
    reason: Optional[str] = ""


class ProgressBody(BaseModel):
    material_id: str
    segment_index: int = 0
    offset_ms: int = 0
    total_ms: int = 0
    finished: bool = False


class PlanImportBody(BaseModel):
    items: list[dict]


def _public_material(mat: dict) -> dict:
    out = dict(mat)
    # 不把超长内部字段原样暴露也没必要裁剪，保持完整便于设备端
    return out


@router.get("/health")
async def material_health():
    return {
        "ok": True,
        "shared": agent_bridge.shared_status(),
        "settings_domains": load_settings().get("material_domains"),
    }


@router.get("/today")
async def today(domain: Optional[str] = None):
    mat = await material_service.get_or_create_today(force_domain=domain)
    return _public_material(mat)


@router.post("/refresh")
async def refresh(body: RefreshBody | None = None):
    domain = body.domain if body else None
    mat = await material_service.refresh_material(domain)
    return _public_material(mat)


@router.post("/chat")
async def chat(body: ChatBody):
    session_id = body.session_id or "default"
    from services import agent_chat

    result = await agent_chat.agent_chat(
        session_id=session_id,
        message=body.message,
        material_id=body.material_id,
    )
    return result


class ChallengeBody(BaseModel):
    material_id: Optional[str] = None
    rounds: int = 3


@router.post("/challenge")
async def challenge(body: ChallengeBody | None = None):
    """找茬式多轮追问清单（规则生成，不依赖模型也可用）。"""
    from services import agent_tools

    payload = {
        "material_id": (body.material_id if body else None) or "",
        "rounds": body.rounds if body else 3,
    }
    result = agent_tools.dispatch("challenge_material", payload)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "challenge failed")
    return result


class SegmentBody(BaseModel):
    material_id: Optional[str] = None
    text: Optional[str] = None


@router.post("/segment")
async def segment(body: SegmentBody | None = None):
    """正文分段（TTS/设备 P5 文本侧）。"""
    from services import agent_tools

    result = agent_tools.dispatch(
        "segment_material_text",
        {
            "material_id": (body.material_id if body else None) or "",
            "text": (body.text if body else None) or "",
        },
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "segment failed")
    return result


@router.get("/archive/{material_id}/body")
async def archive_body(material_id: str):
    """归档正文冷存回读。"""
    from config import ARCHIVE_BODY_DIR
    import os

    path = os.path.join(ARCHIVE_BODY_DIR, f"{material_id}.txt")
    if not os.path.exists(path):
        # 可能尚未归档，直接读 materials
        mat = db.get_material(material_id)
        if mat and mat.get("body"):
            return {"material_id": material_id, "body": mat["body"], "from": "materials", "degraded": False}
        raise HTTPException(status_code=404, detail="body not found")
    try:
        with open(path, encoding="utf-8") as f:
            body = f.read()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"material_id": material_id, "body": body, "from": "archive_bodies", "degraded": False}


@router.post("/feedback")
async def feedback(body: FeedbackBody):
    mat = db.get_material(body.material_id)
    if not mat:
        raise HTTPException(status_code=404, detail="material not found")
    vote = (body.vote or "").lower()
    if vote not in {"up", "down", "skip"}:
        raise HTTPException(status_code=400, detail="vote must be up/down/skip")
    db.update_material_feedback(body.material_id, vote)
    # 记忆增量：up/down 影响本地记忆镜像
    delta = {"up": 0.05, "down": -0.05, "skip": -0.02}.get(vote, 0.0)
    topic = mat.get("title") or mat.get("domain") or "unknown"
    agent_bridge.write_local_memory_delta(topic, delta, reason=f"material_feedback:{vote}")
    if vote in {"down", "skip"} and mat.get("plan_id"):
        db.mark_plan_skipped(mat["plan_id"], note=body.reason or vote)
    return {
        "ok": True,
        "material_id": body.material_id,
        "vote": vote,
        "memory_delta": delta,
    }


@router.get("/archive")
async def archive_list(limit: int = 100):
    return {"items": db.list_archive(limit=limit)}


@router.post("/archive/run")
async def archive_run(recent_days: Optional[int] = None):
    return material_service.run_archive_once(recent_days=recent_days)


@router.get("/plan")
async def plan_list(status: Optional[str] = None):
    items = db.list_plan(status=status)
    return {"items": items, "count": len(items)}


@router.post("/plan/seed")
async def plan_seed():
    return material_service.ensure_seed_plan()


@router.post("/plan/seed_gap")
async def plan_seed_gap(limit: int = 15):
    """从海马体弱项补漏灌计划。"""
    return material_service.seed_gap_from_weak_memory(limit=limit)


@router.post("/plan/recycle")
async def plan_recycle():
    """把 used/skipped 收回 pending（运维，慎用）。"""
    n = db.recycle_all_plans()
    return {"recycled": n, "pending": len(db.list_plan("pending"))}


@router.post("/plan/import")
async def plan_import(body: PlanImportBody):
    n = db.insert_plan(body.items or [])
    return {"imported": n}


@router.get("/progress")
async def progress_get(material_id: str):
    return db.get_progress(material_id) or {}


@router.post("/progress")
async def progress_set(body: ProgressBody):
    return db.upsert_progress(
        material_id=body.material_id,
        segment_index=body.segment_index,
        offset_ms=body.offset_ms,
        total_ms=body.total_ms,
        finished=body.finished,
    )


@router.get("/audio/{material_id}")
async def audio_segments(material_id: str):
    return {"segments": db.list_audio_segments(material_id)}
