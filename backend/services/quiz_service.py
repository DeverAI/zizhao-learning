"""小测闭环：素材关键点 → 规则/模型出题 → 批改 → 错题进补漏计划。

初三用法：听完今日素材立刻 5 题；错的标题进 gap_fill，明天优先。
"""
from __future__ import annotations

import re
from typing import Optional

from models import database as db
from services import generator, material_service, persona, security


def _material(mid: Optional[str] = None, user_id: str = "") -> dict:
    if mid:
        mat = db.get_material(mid)
        if mat:
            if user_id and mat.get("user_id") and mat.get("user_id") != user_id:
                raise ValueError("forbidden material")
            return mat
    from config import beijing_today

    mat = db.get_today_material(beijing_today(), user_id=user_id)
    if mat:
        return mat
    raise ValueError("no material")


def build_quiz(material_id: str = "", rounds: int = 5, user_id: str = "") -> dict:
    """规则版出题：从关键点/概念/标题生成简答题干（不依赖 LLM 也可用）。"""
    mat = _material(material_id, user_id=user_id)
    keys = [str(x) for x in (mat.get("key_points") or []) if x]
    concepts = [str(x) for x in (mat.get("concept_keys") or []) if x]
    title = mat.get("title") or ""
    questions = []
    if title:
        questions.append(
            {
                "id": "q_def",
                "type": "定义",
                "ask": f"用不超过40字定义「{title}」，禁止整句抄正文。",
                "expect_hints": concepts[:3] or keys[:2],
            }
        )
    if concepts:
        questions.append(
            {
                "id": "q_dist",
                "type": "辨析",
                "ask": f"概念 {concepts[:2]} 与一个近邻概念如何区分？各给1个反例。",
                "expect_hints": concepts[:3],
            }
        )
    if keys:
        questions.append(
            {
                "id": "q_key",
                "type": "要点",
                "ask": "默写今日素材的 2 个关键点（用自己的话）。",
                "expect_hints": keys[:3],
            }
        )
    questions.append(
        {
            "id": "q_exam",
            "type": "考法",
            "ask": "若笔试考这个点，写出题干骨架与判分点。",
            "expect_hints": [title] if title else [],
        }
    )
    questions.append(
        {
            "id": "q_act",
            "type": "行动",
            "ask": "列出今晚 2 个可完成动作，每个≤15分钟。",
            "expect_hints": [],
        }
    )
    questions = questions[: max(1, min(rounds, 8))]
    return {
        "ok": True,
        "material_id": mat.get("id"),
        "title": title,
        "questions": questions,
        "grading": "纯文本作答；按要点命中与是否可执行评分；不讨好",
        "no_markdown": True,
    }


def _hits(answer: str, hints: list[str]) -> int:
    ans = (answer or "").lower()
    n = 0
    for h in hints or []:
        h = (h or "").strip()
        if h and h.lower() in ans:
            n += 1
    return n


def grade_quiz(material_id: str, answers: list[dict], user_id: str = "") -> dict:
    """answers: [{id, text}]。规则批改 + 错题写回补漏计划。"""
    mat = _material(material_id, user_id=user_id)
    quiz = build_quiz(mat.get("id") or "", user_id=user_id)
    by_id = {q["id"]: q for q in quiz["questions"]}
    results = []
    wrong_titles = []
    score = 0
    total = 0
    for ans in answers or []:
        qid = str(ans.get("id") or "")
        text = security.sanitize_text(str(ans.get("text") or ""), 2000)
        q = by_id.get(qid)
        if not q:
            continue
        total += 1
        hints = q.get("expect_hints") or []
        hit = _hits(text, hints)
        length_ok = len(text.strip()) >= 8
        passed = bool(length_ok and (not hints or hit >= 1))
        if passed:
            score += 1
        else:
            wrong_titles.append(f"{mat.get('title','')}·{q.get('type')}")
        results.append(
            {
                "id": qid,
                "passed": passed,
                "hit_hints": hit,
                "hint_count": len(hints),
                "feedback": (
                    "过关，下一题。"
                    if passed
                    else "未过关：补定义边界/反例/可执行动作，写完再交。"
                ),
            }
        )
    # 错题 → gap_fill 计划
    added = 0
    if wrong_titles:
        items = []
        for t in wrong_titles[:5]:
            items.append(
                {
                    "domain": "gap_fill",
                    "seq": 900,
                    "title": t,
                    "source_hint": f"quiz_miss material={mat.get('title')}",
                    "tags": ["错题", "补漏"],
                    "note": "from_quiz",
                }
            )
        added = db.insert_plan(items)
    return {
        "ok": True,
        "material_id": mat.get("id"),
        "score": score,
        "total": total or len(quiz["questions"]),
        "results": results,
        "gap_plan_added": added,
        "next_action": (
            "全对。抽 challenge 再抬杠一轮。"
            if score >= (total or 1)
            else f"错 {len(wrong_titles)} 题已进补漏计划，明早素材优先同主题。"
        ),
        "no_markdown": True,
    }


async def coach_review(material_id: str, answers: list[dict], grade: dict) -> dict:
    """可选 LLM 点评；失败降级为规则结果摘要。"""
    mat = _material(material_id)
    prompt = (
        "你是不讨好的初三自招教练。用户刚做完小测。\n"
        f"素材：{mat.get('title')}\n"
        f"得分：{grade.get('score')}/{grade.get('total')}\n"
        f"明细：{grade.get('results')}\n"
        "用纯文本：1)最大漏洞 2)今晚必须做的1件事 3)一句催办。禁止 Markdown 与夸奖。"
    )
    content, ok, provider = await generator._chat_completion(
        [{"role": "user", "content": prompt}], temperature=0.3
    )
    if not ok or not content:
        return {
            "ok": False,
            "degraded": True,
            "provider": provider,
            "comment": persona.strip_markdown(
                "（降级：未调用模型。）\n" + (grade.get("next_action") or "")
            ),
        }
    return {
        "ok": True,
        "degraded": False,
        "provider": provider,
        "comment": persona.strip_markdown(content),
    }
