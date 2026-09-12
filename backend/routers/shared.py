"""共享源只读接口：资料检索、记忆镜像、课程自招节点。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services import agent_bridge

router = APIRouter(prefix="/api/shared", tags=["shared"])


@router.get("/status")
async def status():
    return agent_bridge.shared_status()


@router.get("/curriculum/zizhao")
async def zizhao_nodes(band: str = "自招"):
    nodes = agent_bridge.extract_zizhao_nodes(band)
    return {"band": band, "count": len(nodes), "nodes": nodes}


@router.get("/memory")
async def memory(apply_decay: bool = True):
    return agent_bridge.load_shared_memory(apply_decay=apply_decay)


@router.get("/memory/weak")
async def weak(limit: int = 8):
    return {"items": agent_bridge.weak_topics(max_n=limit)}


@router.get("/search")
async def search(q: str, limit: int = 10):
    if not q.strip():
        raise HTTPException(status_code=400, detail="q required")
    return {"query": q, "items": agent_bridge.search_shared_materials(q, limit=limit)}
