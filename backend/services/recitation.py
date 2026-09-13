"""英语背诵：条目列表、抽背、找茬批改（纯文本）。"""
from __future__ import annotations

import json
import os
import random
from datetime import datetime, timezone
from typing import Optional

from config import atomic_write_json, ensure_dirs
from services import agent_bridge, persona


def _items_path() -> str:
    from config import STORAGE_DIR

    return os.path.join(STORAGE_DIR, "recitation_items.json")


def _log_path() -> str:
    from config import STORAGE_DIR

    return os.path.join(STORAGE_DIR, "recitation_log.json")


DEFAULT_ITEMS = [
    {
        "id": "seed_courage_1",
        "title": "Courage is not the absence of fear",
        "passage": (
            "Courage is not the absence of fear. It is acting in spite of it. "
            "When you face a hard passage, do not wait until you feel ready. "
            "Start the first sentence out loud, then the next."
        ),
        "source": "内置种子·非考试原文",
        "status": "pending",
        "created_at": "",
    },
    {
        "id": "seed_method_1",
        "title": "A method for reciting",
        "passage": (
            "Read once for meaning. Cover the text and try to recall the skeleton. "
            "Check the gaps. Repeat only the gaps. Do not reread the whole line "
            "just because it feels comfortable."
        ),
        "source": "内置种子·方法段",
        "status": "pending",
        "created_at": "",
    },
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_items() -> list[dict]:
    ensure_dirs()
    if os.path.exists(_items_path()):
        try:
            with open(_items_path(), encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    items = [dict(x) for x in DEFAULT_ITEMS]
    atomic_write_json(_items_path(), items)
    return items


def save_items(items: list[dict]) -> None:
    atomic_write_json(_items_path(), items)


def load_log() -> list[dict]:
    if not os.path.exists(_log_path()):
        return []
    try:
        with open(_log_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def pick_random(status: str = "pending") -> Optional[dict]:
    items = [x for x in load_items() if x.get("status", "pending") == status] or load_items()
    if not items:
        return None
    return random.choice(items)


def grade_attempt(item_id: str, user_text: str) -> dict:
    """对用户复述做找茬：错漏、次序、用词。优先规则，可选 LLM。"""
    items = {x.get("id"): x for x in load_items()}
    item = items.get(item_id)
    if not item:
        return {"ok": False, "error": "item not found"}
    passage = item.get("passage") or ""
    user = (user_text or "").strip()

    def words(s: str) -> list[str]:
        return [w.lower().strip(".,!?;:\"'()") for w in s.split() if w.strip()]

    src_w = words(passage)
    usr_w = words(user)
    src_set = set(src_w)
    usr_set = set(usr_w)
    missing = [w for w in src_w if w not in usr_set][:30]
    extra = [w for w in usr_w if w not in src_set][:20]
    coverage = 0.0
    if src_w:
        hit = sum(1 for w in src_w if w in usr_set)
        coverage = round(hit / len(src_w), 3)

    issues = []
    if coverage < 0.55:
        issues.append("覆盖率偏低：先抓主干句，不要整段跳过")
    if missing:
        issues.append("漏词样例：" + ", ".join(missing[:12]))
    if extra:
        issues.append("多出/替换词样例：" + ", ".join(extra[:8]))
    if len(usr_w) < max(3, int(len(src_w) * 0.4)):
        issues.append("输出过短，像在编不是在背")
    # 次序粗检：公共子序列比例
    i = 0
    for w in usr_w:
        if i < len(src_w) and w == src_w[i]:
            i += 1
    order_ratio = round(i / max(1, len(src_w)), 3)
    if order_ratio < 0.4:
        issues.append("词序与原文偏差大：按句群顺序重背，不要打乱")

    ok = coverage >= 0.75 and order_ratio >= 0.6
    if ok:
        item["status"] = "done"
    save_items(list(items.values()))

    log = load_log()
    log.append(
        {
            "date": _now(),
            "item_id": item_id,
            "coverage": coverage,
            "order_ratio": order_ratio,
            "ok": ok,
        }
    )
    atomic_write_json(_log_path(), log[-200:])

    return {
        "ok": True,
        "item_id": item_id,
        "title": item.get("title"),
        "coverage": coverage,
        "order_ratio": order_ratio,
        "passed": ok,
        "issues": issues,
        "next_action": (
            "过关。抽下一段，要求 30 秒内起背。"
            if ok
            else "未过关。只重背漏掉的句群，遮住原文再来一遍。"
        ),
        "no_markdown": True,
    }


async def coach_comment(item_id: str, user_text: str, grade: dict) -> dict:
    """可选 LLM 找茬点评；失败则回退规则结果。"""
    items = {x.get("id"): x for x in load_items()}
    item = items.get(item_id) or {}
    from services import generator

    prompt = (
        "你是严厉但不人身攻击的英语背诵教练。用户在背一段英文。\n"
        f"原文：\n{item.get('passage','')}\n\n"
        f"用户复述：\n{user_text}\n\n"
        f"规则批改：coverage={grade.get('coverage')} order={grade.get('order_ratio')} "
        f"issues={grade.get('issues')}\n"
        "请用纯文本输出：1)最严重3处问题 2)下一句该怎么背 3)一句催办。不要 Markdown，不要夸。"
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
                "（降级：未调用模型。按规则批改执行。）\n"
                + "\n".join(grade.get("issues") or ["无明显规则命中"])
                + f"\n{grade.get('next_action','')}"
            ),
        }
    return {
        "ok": True,
        "degraded": False,
        "provider": provider,
        "comment": persona.strip_markdown(content),
    }
