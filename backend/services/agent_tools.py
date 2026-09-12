"""Agent 工具：邻仓检索摘要、计算器、画像记录、刷新素材。禁止一次倾倒全仓。"""
from __future__ import annotations

import ast
import operator
import re
from typing import Any, Callable

from services import agent_bridge, persona

# 安全算术
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("unsupported expression")


def safe_calculate(expr: str) -> dict:
    expr = (expr or "").strip().replace("×", "*").replace("÷", "/").replace("^", "**")
    if not expr:
        return {"ok": False, "error": "empty expression"}
    if len(expr) > 120:
        return {"ok": False, "error": "expression too long"}
    try:
        tree = ast.parse(expr, mode="eval")
        value = _eval_node(tree)
        return {"ok": True, "expression": expr, "value": value}
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError, OverflowError) as exc:
        return {"ok": False, "expression": expr, "error": str(exc)}


def _excerpt_from_hit(hit: dict) -> str:
    parts = []
    if hit.get("kind") == "curriculum":
        parts.append(f"[课程体系] {hit.get('subject','')}/{hit.get('label','')}")
        parts.append(f"年级={hit.get('grade')} 模块={hit.get('module')} band={hit.get('band')}")
        prereq = hit.get("prereq") or []
        if prereq:
            parts.append("前置：" + "、".join(map(str, prereq)))
        parts.append("出处：学习Agent_new/backend/data/curriculum_cn_junior.json")
    else:
        parts.append(f"[知识树] {hit.get('label','')} type={hit.get('type')}")
        parts.append(f"节点 id={hit.get('id')}")
        parts.append("出处：学习Agent_new/backend/storage/knowledge_tree.json")
    return "\n".join(parts)


def tool_search_shared(args: dict) -> dict:
    q = str(args.get("query") or args.get("q") or "").strip()
    limit = int(args.get("limit") or 6)
    limit = max(1, min(limit, 12))  # 硬顶，防止倾倒
    hits = agent_bridge.search_shared_materials(q, limit=limit)
    return {
        "ok": True,
        "query": q,
        "count": len(hits),
        "hits": hits,
        "note": "仅命中摘要；需要细节请再调用 read_shared_excerpt",
    }


def tool_read_shared_excerpt(args: dict) -> dict:
    """按 label/id 取摘要级片段。绝不返回全文件。"""
    label = str(args.get("label") or args.get("query") or "").strip()
    if not label:
        return {"ok": False, "error": "label required"}
    hits = agent_bridge.search_shared_materials(label, limit=5)
    if not hits:
        return {"ok": False, "error": "no hit", "query": label}
    best = hits[0]
    # 海马体相关主题
    memory_extra = {}
    mem = agent_bridge.load_shared_memory(apply_decay=True)
    for topic, data in (mem.get("topics") or {}).items():
        if label in topic or topic in label:
            memory_extra = {
                "hippocampus_topic": topic,
                "mastery": data.get("mastery"),
                "mastery_source": data.get("mastery_source"),
                "weak_points": data.get("weak_points") or [],
                "source": "学习Agent_new/backend/hippocampus/profile.json",
            }
            break
    return {
        "ok": True,
        "excerpt": _excerpt_from_hit(best),
        "hit": best,
        "memory": memory_extra,
        "truncated": True,
    }


def tool_calculator(args: dict) -> dict:
    expr = str(args.get("expression") or args.get("expr") or "")
    result = safe_calculate(expr)
    result["ok"] = bool(result.get("ok"))
    return result


def tool_profile_note(args: dict) -> dict:
    profile = persona.load_profile()
    note = str(args.get("note") or args.get("text") or "").strip()
    trait = str(args.get("trait") or "").strip()
    avoid = str(args.get("avoid") or "").strip()
    detail = str(args.get("detail_level") or "").strip()
    if trait and trait not in profile["impression"]["traits"]:
        profile["impression"]["traits"].append(trait)
        profile["impression"]["traits"] = profile["impression"]["traits"][-12:]
    if avoid and avoid not in profile["impression"]["avoid"]:
        profile["impression"]["avoid"].append(avoid)
        profile["impression"]["avoid"] = profile["impression"]["avoid"][-12:]
    if note:
        profile["impression"]["notes"].append({"date": persona._now(), "snippet": note[:160]})
        profile["impression"]["notes"] = profile["impression"]["notes"][-30:]
    if detail in {"brief", "standard", "deep"}:
        profile["preferences"]["detail_level"] = detail
    if int(profile.get("stats", {}).get("turns") or 0) >= 4:
        if profile["impression"]["stage"] == "stranger":
            profile["impression"]["stage"] = "observed"
    persona.save_profile(profile)
    return {
        "ok": True,
        "stage": profile["impression"]["stage"],
        "detail_level": profile["preferences"]["detail_level"],
    }


def tool_set_agenda(args: dict) -> dict:
    profile = persona.load_profile()
    persona.set_agenda(
        profile,
        focus=str(args.get("focus") or ""),
        next_action=str(args.get("next_action") or ""),
        deadline=str(args.get("deadline") or ""),
    )
    persona.save_profile(profile)
    return {"ok": True, "agenda": profile.get("agenda")}


def tool_refresh_material(args: dict) -> dict:
    """由 agent 层注入真实刷新；这里只给元数据。"""
    return {
        "ok": True,
        "should_refresh": True,
        "domain": args.get("domain") or "any",
    }


def tool_challenge_material(args: dict) -> dict:
    """生成找茬式追问清单（规则版，不依赖模型）。"""
    from models import database as db

    mid = str(args.get("material_id") or "")
    rounds = max(1, min(int(args.get("rounds") or 3), 6))
    mat = db.get_material(mid) if mid else None
    if not mat:
        # 今日
        day = __import__("config", fromlist=["x"]).beijing_today()
        mat = db.get_today_material(day)
    if not mat:
        return {"ok": False, "error": "no material"}
    keys = mat.get("key_points") or []
    follows = mat.get("followups") or []
    concepts = mat.get("concept_keys") or []
    questions = []
    questions.append(
        {
            "round": 1,
            "type": "定义边界",
            "ask": f"用不超过40字定义「{mat.get('title')}」。禁止复述原文整句。",
        }
    )
    questions.append(
        {
            "round": 2,
            "type": "出处核对",
            "ask": f"说出本素材来源/篇目；若不确定写「存疑」并说明缺哪条证据。source={mat.get('source')}",
        }
    )
    questions.append(
        {
            "round": 3,
            "type": "概念换皮",
            "ask": f"概念 {concepts or keys[:3]} 与一个近邻概念如何区分？给1个反例。",
        }
    )
    if rounds >= 4:
        questions.append(
            {
                "round": 4,
                "type": "考法挂钩",
                "ask": "若笔试考这个点，最可能的设问方式是什么？写出题干骨架。",
            }
        )
    if rounds >= 5:
        questions.append(
            {
                "round": 5,
                "type": "行动",
                "ask": "列出今晚可完成的2个动作，每个不超过15分钟。",
            }
        )
    return {
        "ok": True,
        "material_id": mat.get("id"),
        "title": mat.get("title"),
        "mode": "challenge",
        "questions": questions[:rounds],
        "followup_seeds": follows[:3],
        "grading": "不讨好；答错指出错在哪一条；答对不夸，直接下一问",
        "no_markdown": True,
    }


def tool_segment_text(args: dict) -> dict:
    """把讲解稿切成可 TTS 的段（P5 文本侧，音频文件另接）。"""
    from models import database as db

    mid = str(args.get("material_id") or "")
    mat = db.get_material(mid) if mid else None
    body = (args.get("text") or (mat or {}).get("body") or "").strip()
    if not body:
        return {"ok": False, "error": "empty body"}
    import re

    parts = [p.strip() for p in re.split(r"\n\s*\n|\r\n\r\n", body) if p.strip()]
    if len(parts) < 2:
        # 按句号粗切，约 120-200 字一段
        sentences = re.split(r"(?<=[。！？.!?])", body)
        parts, buf = [], ""
        for s in sentences:
            buf += s
            if len(buf) >= 160:
                parts.append(buf.strip())
                buf = ""
        if buf.strip():
            parts.append(buf.strip())
    segments = []
    for i, p in enumerate(parts[:30]):
        segments.append(
            {
                "segment_index": i,
                "text": p,
                "chars": len(p),
                "path": "",  # 音频未生成则留空，不伪造
            }
        )
    if mid:
        try:
            db.insert_audio_segments(mid, segments)
        except Exception:  # noqa: BLE001
            pass
    return {
        "ok": True,
        "material_id": mid or None,
        "segment_count": len(segments),
        "segments": segments,
        "audio_ready": False,
        "note": "仅文本分段；TTS/MP3 未接则 audio_ready=false",
    }


TOOL_SPECS: list[dict] = [
    {
        "name": "search_shared",
        "description": "在邻仓学习Agent_new的课程体系与知识树中检索。先搜再读，限量返回摘要。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "关键词，如 勾股定理/自招/欧姆定律"},
                "limit": {"type": "integer", "description": "最多返回条数，默认6，上限12"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_shared_excerpt",
        "description": "按条目名读取邻仓摘要片段（含出处路径），不会返回全库。",
        "parameters": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "条目名/主题"},
            },
            "required": ["label"],
        },
    },
    {
        "name": "calculator",
        "description": "安全四则运算。凡涉及分式、百分比、多位数乘除必须先算再答。",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "算式，如 (3/8)*100"},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "profile_note",
        "description": "记录可核验的用户长期画像（特质/避免项/详略）。禁止记恭维话。",
        "parameters": {
            "type": "object",
            "properties": {
                "trait": {"type": "string"},
                "avoid": {"type": "string"},
                "note": {"type": "string"},
                "detail_level": {"type": "string", "enum": ["brief", "standard", "deep"]},
            },
        },
    },
    {
        "name": "set_agenda",
        "description": "设定当前焦点与下一步动作（催办事用）。",
        "parameters": {
            "type": "object",
            "properties": {
                "focus": {"type": "string"},
                "next_action": {"type": "string"},
                "deadline": {"type": "string"},
            },
        },
    },
    {
        "name": "refresh_material",
        "description": "用户明确要换素材/换话题时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "philosophy|history|classics|shared_curriculum|any",
                },
            },
        },
    },
    {
        "name": "challenge_material",
        "description": "对当前/指定素材发起找茬式多轮追问（定义边界/出处/反例/考法）。",
        "parameters": {
            "type": "object",
            "properties": {
                "material_id": {"type": "string"},
                "rounds": {"type": "integer", "description": "1-6，默认3"},
            },
        },
    },
    {
        "name": "segment_material_text",
        "description": "把素材正文切成可朗读分段（供后续 TTS/设备）。",
        "parameters": {
            "type": "object",
            "properties": {
                "material_id": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
]

HANDLERS: dict[str, Callable[[dict], dict]] = {
    "search_shared": tool_search_shared,
    "read_shared_excerpt": tool_read_shared_excerpt,
    "calculator": tool_calculator,
    "profile_note": tool_profile_note,
    "set_agenda": tool_set_agenda,
    "refresh_material": tool_refresh_material,
    "challenge_material": tool_challenge_material,
    "segment_material_text": tool_segment_text,
}


def openai_tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"],
            },
        }
        for spec in TOOL_SPECS
    ]


def dispatch(name: str, arguments: dict | str) -> dict:
    if isinstance(arguments, str):
        import json

        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            arguments = {}
    if not isinstance(arguments, dict):
        arguments = {}
    handler = HANDLERS.get(name)
    if not handler:
        return {"ok": False, "error": f"unknown tool {name}"}
    try:
        return handler(arguments)
    except Exception as exc:  # noqa: BLE001 — 工具失败要可区分，不吞成成功
        return {"ok": False, "error": str(exc)}


def compact_tool_result(name: str, result: dict) -> str:
    """压成可进上下文的纯文本，避免工具结果撑爆。"""
    import json

    text = json.dumps(result, ensure_ascii=False)
    if len(text) > 1800:
        text = text[:1800] + "…[truncated]"
    return f"tool:{name}\n{persona.strip_markdown(text)}"
