"""内置组件注册表：主页入口 + 用户可启用/申请新组件。"""
from __future__ import annotations

from models import database as db

BUILTIN_COMPONENTS: list[dict] = [
    {
        "id": "home",
        "name": "主页",
        "icon": "⌂",
        "description": "组件入口与今日概览",
        "entry": "#/home",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "zizhao",
        "name": "自招素材",
        "icon": "哲",
        "description": "哲学/历史/古诗文每日素材 + 挂载对话 + 找茬",
        "entry": "#/zizhao",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "english",
        "name": "英语小组件",
        "icon": "EN",
        "description": "高词/介词搭配/熟词生义；会模糊不会、错词库、新库",
        "entry": "#/english",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "tools",
        "name": "小工具",
        "icon": "工",
        "description": "计算器：口述→算式→结果；板子屏小不点按键",
        "entry": "#/tools",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "classics",
        "name": "古诗文播放",
        "icon": "诗",
        "description": "常驻古诗文条目朗读/分段播放",
        "entry": "#/classics",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "timetable",
        "name": "时间表",
        "icon": "时",
        "description": "周计划与 Agent 整理",
        "entry": "#/timetable",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "library",
        "name": "资料库",
        "icon": "库",
        "description": "常驻资料 + 上传整理（OCR/MP3）",
        "entry": "#/library",
        "builtin": True,
        "default_on": True,
    },
    {
        "id": "devices",
        "name": "设备",
        "icon": "盒",
        "description": "ESP-S3 PassKey 管理",
        "entry": "#/devices",
        "builtin": True,
        "default_on": True,
    },
]


def catalog() -> list[dict]:
    return [dict(c) for c in BUILTIN_COMPONENTS]


def get_component(cid: str) -> dict | None:
    for c in BUILTIN_COMPONENTS:
        if c["id"] == cid:
            return dict(c)
    return None


def ensure_user_defaults(user_id: str) -> list[dict]:
    existing = db.list_user_components(user_id)
    if existing:
        return existing
    items = []
    for i, c in enumerate(BUILTIN_COMPONENTS):
        if c.get("default_on"):
            items.append(
                {
                    "component_id": c["id"],
                    "enabled": True,
                    "order_index": i,
                    "config": {},
                }
            )
    db.set_user_components(user_id, items)
    return db.list_user_components(user_id)


def home_payload(user_id: str) -> dict:
    ensure_user_defaults(user_id)
    enabled = {x["component_id"]: x for x in db.list_user_components(user_id) if x.get("enabled")}
    cards = []
    for c in BUILTIN_COMPONENTS:
        if c["id"] in enabled:
            cards.append({**c, "order_index": enabled[c["id"]].get("order_index", 0)})
    cards.sort(key=lambda x: x.get("order_index") or 0)
    return {
        "user_id": user_id,
        "components": cards,
        "catalog": catalog(),
        "requests": db.list_component_requests(user_id),
    }
