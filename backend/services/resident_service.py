"""常驻资料库：本仓独立存储，不整天只靠邻仓。"""
from __future__ import annotations

from models import database as db
from services import security

KINDS = {"note", "classics", "word", "passage", "source", "other"}


def add(user_id: str, title: str, body: str = "", kind: str = "note", tags: list | None = None, source: str = "") -> dict:
    title = security.sanitize_text(title, 160)
    body = security.sanitize_text(body, 20000)
    if not title:
        raise ValueError("title required")
    if kind not in KINDS:
        kind = "note"
    iid = db.insert_resident(
        {
            "user_id": user_id,
            "kind": kind,
            "title": title,
            "body": body,
            "tags": tags or [],
            "source": source,
        }
    )
    item = db.get_resident(user_id, iid)
    return item or {"id": iid}


def update(user_id: str, item_id: str, **fields) -> dict:
    ok = db.update_resident(user_id, item_id, **fields)
    if not ok:
        raise ValueError("not found")
    return db.get_resident(user_id, item_id) or {}


def list_items(user_id: str, kind: str | None = None) -> list[dict]:
    return db.list_resident(user_id, kind=kind)


def search(user_id: str, q: str, limit: int = 20) -> list[dict]:
    q = (q or "").strip().lower()
    if not q:
        return list_items(user_id)[:limit]
    hits = []
    for it in list_items(user_id):
        hay = f"{it.get('title','')} {it.get('body','')} {' '.join(it.get('tags') or [])}".lower()
        if q in hay:
            hits.append(it)
        if len(hits) >= limit:
            break
    return hits


def as_prompt_block(user_id: str, q: str = "", limit: int = 8) -> str:
    items = search(user_id, q, limit=limit) if q else list_items(user_id)[:limit]
    if not items:
        return "（常驻资料为空）"
    lines = []
    for it in items:
        body = (it.get("body") or "").replace("\n", " ")[:120]
        lines.append(f"- [{it.get('kind')}] {it.get('title')}: {body}")
    return "\n".join(lines)


def delete(user_id: str, item_id: str) -> bool:
    return db.delete_resident(user_id, item_id)
