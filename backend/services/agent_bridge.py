"""学习Agent_new 共享桥：资料（课程体系/知识树）与记忆（海马体）只读接入。"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Optional

from config import (
    SHARED_BACKEND,
    SHARED_CURRICULUM,
    SHARED_HIPPOCAMPUS,
    SHARED_KNOWLEDGE_TREE,
    SHARED_SETTINGS,
    SHARED_AGENT_ROOT,
)


def _read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _access_denied() -> bool:
    letter = os.path.join(SHARED_AGENT_ROOT, "updates", "20260912_自招系统共享调用告知.md")
    # 兼容正本改名或显式拒绝
    for name in os.listdir(os.path.join(SHARED_AGENT_ROOT, "updates")) if os.path.isdir(os.path.join(SHARED_AGENT_ROOT, "updates")) else []:
        if name.endswith("_REVOKED.md") and "自招" in name:
            return True
    try:
        if os.path.exists(letter):
            with open(letter, encoding="utf-8") as f:
                head = f.read(800)
            if "SHARED_ACCESS: denied" in head:
                return True
    except OSError:
        pass
    # AGENTS.md 声明
    agents = os.path.join(SHARED_AGENT_ROOT, "AGENTS.md")
    try:
        if os.path.exists(agents):
            with open(agents, encoding="utf-8") as f:
                text = f.read()
            if "禁止邻仓自招" in text or "SHARED_ACCESS: denied" in text:
                return True
    except OSError:
        pass
    return False


def shared_status() -> dict:
    denied = _access_denied()
    return {
        "agent_root": SHARED_AGENT_ROOT,
        "exists": os.path.isdir(SHARED_AGENT_ROOT),
        "curriculum": os.path.exists(SHARED_CURRICULUM),
        "hippocampus": os.path.exists(SHARED_HIPPOCAMPUS),
        "knowledge_tree": os.path.exists(SHARED_KNOWLEDGE_TREE),
        "settings": os.path.exists(SHARED_SETTINGS),
        "access": "denied" if denied else "readonly",
        "denied": denied,
    }


# ---------------------------------------------------------------- 资料共享

def load_shared_curriculum() -> dict:
    data = _read_json(SHARED_CURRICULUM, {"subjects": []})
    if not isinstance(data, dict):
        return {"subjects": []}
    return data


def extract_nodes(band: str | None = None, limit: int = 500) -> list[dict]:
    """抽取课程体系节点；band=None 表示全部（用于补漏灌种）。"""
    if _access_denied():
        return []
    curriculum = load_shared_curriculum()
    nodes: list[dict] = []
    for subj in curriculum.get("subjects") or []:
        subject = str(subj.get("subject") or "")
        for node in subj.get("nodes") or []:
            node_band = str(node.get("band") or "")
            if band is not None and node_band != band:
                continue
            nodes.append(
                {
                    "subject": subject,
                    "label": node.get("label"),
                    "grade": node.get("grade"),
                    "module": node.get("module"),
                    "band": node_band,
                    "prereq": node.get("prereq") or [],
                }
            )
    return nodes[:limit]


def extract_zizhao_nodes(band: str = "自招") -> list[dict]:
    """从共享课程体系抽取指定难度条目（默认自招）。"""
    return extract_nodes(band=band)


def load_knowledge_tree() -> dict:
    data = _read_json(SHARED_KNOWLEDGE_TREE, {"nodes": [], "edges": []})
    if not isinstance(data, dict):
        return {"nodes": [], "edges": []}
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    return data


def search_shared_materials(query: str, limit: int = 10) -> list[dict]:
    """在共享资料中检索：课程体系 + 知识树。拒绝访问时返回空。"""
    if _access_denied():
        return []
    q = (query or "").strip().lower()
    if not q:
        return []
    hits: list[dict] = []
    curriculum = load_shared_curriculum()
    for subj in curriculum.get("subjects") or []:
        subject = str(subj.get("subject") or "")
        for node in subj.get("nodes") or []:
            label = str(node.get("label") or "")
            hay = f"{subject} {label} {node.get('module','')} {node.get('band','')}".lower()
            if q in hay:
                hits.append(
                    {
                        "kind": "curriculum",
                        "subject": subject,
                        "label": label,
                        "grade": node.get("grade"),
                        "module": node.get("module"),
                        "band": node.get("band"),
                        "prereq": node.get("prereq") or [],
                    }
                )
    tree = load_knowledge_tree()
    for node in tree.get("nodes") or []:
        label = str(node.get("label") or "")
        if q in label.lower():
            hits.append(
                {
                    "kind": "knowledge_tree",
                    "id": node.get("id"),
                    "label": label,
                    "type": node.get("type"),
                }
            )
    return hits[:limit]


# ---------------------------------------------------------------- 记忆共享

def _days_since(iso_timestamp: str) -> float:
    if not iso_timestamp:
        return 0.0
    try:
        dt = datetime.fromisoformat(str(iso_timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    except (TypeError, ValueError):
        return 0.0


def _decay(mastery: float, days: float, memory_baseline: float = 0.5) -> float:
    baseline = max(0.1, min(1.0, float(memory_baseline or 0.5)))
    lam = 0.05 / baseline
    return max(0.0, min(1.0, float(mastery) * math.exp(-lam * days)))


def load_shared_memory(apply_decay: bool = True) -> dict:
    """读取学习Agent_new 海马体记忆（只读，不回写共享文件）。"""
    if _access_denied():
        return {"meta": {}, "topics": {}, "source_available": False, "access": "denied"}
    data = _read_json(SHARED_HIPPOCAMPUS, {})
    if not isinstance(data, dict):
        return {"meta": {}, "topics": {}, "source_available": False}
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    topics_in = data.get("topics") if isinstance(data.get("topics"), dict) else {}
    baseline = float(meta.get("baseline_memory") or 0.5)
    topics: dict[str, dict] = {}
    for topic, raw in topics_in.items():
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        if apply_decay:
            item["mastery"] = _decay(
                float(item.get("mastery") or 0.0),
                _days_since(str(item.get("last_study") or "")),
                baseline,
            )
            item["mastery_source"] = "estimated_decayed"
        topics[str(topic)] = item
    return {
        "meta": meta,
        "topics": topics,
        "source_available": os.path.exists(SHARED_HIPPOCAMPUS),
        "source_path": SHARED_HIPPOCAMPUS,
    }


def weak_topics(max_n: int = 8) -> list[dict]:
    mem = load_shared_memory(apply_decay=True)
    items = []
    for topic, data in mem.get("topics", {}).items():
        items.append(
            {
                "topic": topic,
                "mastery": float(data.get("mastery") or 0.0),
                "weak_points": data.get("weak_points") or [],
                "last_study": data.get("last_study") or "",
            }
        )
    items.sort(key=lambda x: x["mastery"])
    return items[:max_n]


def teaching_context(domain: str = "", title: str = "") -> dict:
    """给生成/对话用的记忆上下文。"""
    mem = load_shared_memory(apply_decay=True)
    weak = weak_topics(5)
    return {
        "baseline_style": mem.get("meta", {}).get("preferred_style", "conceptual"),
        "best_study_time": mem.get("meta", {}).get("best_study_time", ""),
        "weak_topics": weak,
        "focus_title": title,
        "domain": domain,
    }


def write_local_memory_delta(topic: str, delta: float, reason: str = "") -> dict:
    """把自招学习反馈写到本地镜像（不直接改共享海马体，避免双写冲突）。

    共享记忆仍以 学习Agent_new 为源；本地只记增量，供 adaptive 策略与审计。
    """
    from config import STORAGE_DIR, atomic_write_json

    path = os.path.join(STORAGE_DIR, "memory_delta.json")
    data = _read_json(path, {"topics": {}})
    topics = data.setdefault("topics", {})
    item = topics.setdefault(
        topic,
        {"mastery_delta": 0.0, "history": []},
    )
    item["mastery_delta"] = float(item.get("mastery_delta") or 0.0) + float(delta)
    hist = item.setdefault("history", [])
    hist.append(
        {
            "date": datetime.now(timezone.utc).isoformat(),
            "delta": float(delta),
            "reason": reason or "",
        }
    )
    item["history"] = hist[-50:]
    atomic_write_json(path, data)
    return {"topic": topic, "mastery_delta": item["mastery_delta"]}


def get_ai_credentials() -> dict:
    """从共享 settings 读取可用 AI 凭据（不写日志明文）。拒绝访问时不读。"""
    if _access_denied():
        return {}
    settings = _read_json(SHARED_SETTINGS, {})
    if not isinstance(settings, dict):
        return {}
    creds = {}
    for name in ("deepseek", "kimi", "zhipuai"):
        key = settings.get(f"{name}_api_key") or ""
        base = settings.get(f"{name}_base_url") or ""
        model = settings.get(f"{name}_model") or ""
        if key:
            creds[name] = {"api_key": key, "base_url": base, "model": model}
    custom = settings.get("custom_apis") or []
    if isinstance(custom, list):
        for i, item in enumerate(custom):
            if isinstance(item, dict) and item.get("key"):
                creds[f"custom_{i}"] = {
                    "api_key": item.get("key"),
                    "base_url": item.get("url") or "",
                    "model": item.get("model") or "",
                }
    return creds
