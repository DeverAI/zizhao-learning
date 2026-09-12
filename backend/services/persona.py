"""用户画像与对话人格：不讨好、催做事、绝望才兜底情绪、渐进建立印象。"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any

from config import STORAGE_DIR, atomic_write_json, ensure_dirs

PROFILE_PATH = os.path.join(STORAGE_DIR, "user_profile.json")

# 框架决策：讲解详略与收纳去向
FRAMEWORKS = {
    "讲解": "可朗读的展开讲解，偏口语、可分段",
    "素材": "每日素材库条目，进 plan/archive 去重链路",
    "三观": "价值判断与思辨框架，偏哲学/伦理，不灌鸡汤",
    "知识体系": "概念节点与前置关系，挂课程体系/知识树",
    "英语背诵": "英文段落+中文对照+跟读要点，偏记忆提取",
}

DEFAULT_PROFILE: dict[str, Any] = {
    "version": 1,
    "created_at": "",
    "updated_at": "",
    "impression": {
        "stage": "stranger",  # stranger -> observed -> known
        "traits": [],
        "avoid": [],
        "notes": [],
    },
    "preferences": {
        "tone": "direct",
        "detail_level": "standard",  # brief | standard | deep
        "framework_bias": ["讲解", "素材"],
        "no_markdown": True,
        "emotional_support": "desperate_only",
        "push_action": True,
    },
    "stats": {
        "turns": 0,
        "topics": {},
        "calc_calls": 0,
        "tool_calls": {},
        "evasion_hints": [],
    },
    "agenda": {
        "current_focus": "",
        "next_action": "",
        "deadline_hint": "",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_profile() -> dict:
    ensure_dirs()
    data = dict(DEFAULT_PROFILE)
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(v, dict) and isinstance(data.get(k), dict):
                        data[k] = {**data[k], **v}
                    else:
                        data[k] = v
        except (json.JSONDecodeError, OSError):
            pass
    data["impression"].setdefault("traits", [])
    data["impression"].setdefault("notes", [])
    data["impression"].setdefault("avoid", [])
    return data


def save_profile(data: dict) -> None:
    data = dict(data)
    data["updated_at"] = _now()
    if not data.get("created_at"):
        data["created_at"] = data["updated_at"]
    atomic_write_json(PROFILE_PATH, data)


def strip_markdown(text: str) -> str:
    """前台禁 Markdown：去掉常见标记，避免 ** 变成『美元美元星号』。"""
    if not text:
        return ""
    s = text
    s = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).strip("`"), s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)
    s = re.sub(r"^#{1,6}\s*", "", s, flags=re.M)
    s = re.sub(r"^\s*[-*+]\s+", "· ", s, flags=re.M)
    s = re.sub(r"^\s*\d+\.\s+", lambda m: m.group(0).strip() + " ", s, flags=re.M)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"[*_]{1,3}", "", s)
    return s.strip()


def persona_system_block(profile: dict | None = None) -> str:
    profile = profile or load_profile()
    imp = profile.get("impression") or {}
    pref = profile.get("preferences") or {}
    stage = imp.get("stage") or "stranger"
    traits = "；".join(imp.get("traits") or []) or "尚无"
    avoid = "；".join(imp.get("avoid") or []) or "无"
    detail = pref.get("detail_level") or "standard"
    return f"""你是上海自招备考教练，挂在「今日素材」上工作。人格硬约束（违反即事故）：

1. 不讨好。禁止「你真棒/说得太好了/加油哦」式开场与收尾。
2. 除非用户明显绝望、崩溃、自伤风险，否则不提供情感支持；日常挫折只给步骤。
3. 催做事：每轮尽量落到下一步动作、完成标准、何时检查。能布置就布置。
4. 渐进建立印象，不表演人设。当前画像阶段：{stage}；已观察特质：{traits}；应避免：{avoid}。
5. 输出必须是纯文本：不要使用 Markdown、不要 ** 加粗、不要标题井号、不要代码围栏。
6. 详略档：{detail}。brief=只给结论与动作；standard=短段落+要点；deep=可展开推理但仍分段纯文本。
7. 资料只检索邻仓摘要，禁止假装读过整库。引用要带条目名/路径级出处。
8. 不确定就写不确定，并说明缺哪条证据。不伪造出处。

工作流：
- 先吃当前素材的标题/正文/关键点；
- 需要邻仓事实时调用 search_shared / read_shared_excerpt；
- 算式用 calculator；
- 重要用户特征用 profile_note 记下（少量、可核验、不写恭维话）。
"""


def observe_from_message(profile: dict, message: str) -> dict:
    """从提问里廉价抽取画像信号（不调用模型）。"""
    text = message or ""
    stats = profile.setdefault("stats", {})
    stats["turns"] = int(stats.get("turns") or 0) + 1
    topics = stats.setdefault("topics", {})
    imp = profile.setdefault("impression", {})

    # 简单启发式
    if re.search(r"不会|看不懂|太难|算了|摆烂|放弃", text):
        ev = stats.setdefault("evasion_hints", [])
        ev.append({"date": _now(), "kind": "difficulty_or_evasion", "sample": text[:80]})
        stats["evasion_hints"] = ev[-20:]
    if re.search(r"为什么|凭什么|不对吧|可是|然而|反驳|找茬", text):
        traits = imp.setdefault("traits", [])
        if "会质疑" not in traits:
            traits.append("会质疑")
    if re.search(r"直接|简短|别废话|快说", text):
        pref = profile.setdefault("preferences", {})
        pref["detail_level"] = "brief"
    if re.search(r"详细|展开|讲清楚|推一遍", text):
        pref = profile.setdefault("preferences", {})
        pref["detail_level"] = "deep"
    if re.search(r"难过|撑不住|崩溃|绝望|不想活", text):
        imp["desperate_signal"] = True
    else:
        imp["desperate_signal"] = False

    # 升级画像阶段
    turns = int(stats.get("turns") or 0)
    if turns >= 12 or len(imp.get("traits") or []) >= 3:
        imp["stage"] = "known"
    elif turns >= 4:
        imp["stage"] = "observed"
    else:
        imp["stage"] = imp.get("stage") or "stranger"

    # 精简 notes
    notes = imp.setdefault("notes", [])
    if len(text) >= 8:
        notes.append({"date": _now(), "snippet": text[:100]})
        imp["notes"] = notes[-30:]
    return profile


def set_agenda(profile: dict, focus: str = "", next_action: str = "", deadline: str = "") -> dict:
    agenda = profile.setdefault("agenda", {})
    if focus:
        agenda["current_focus"] = focus
    if next_action:
        agenda["next_action"] = next_action
    if deadline:
        agenda["deadline_hint"] = deadline
    return profile


def detail_instruction(detail: str) -> str:
    return {
        "brief": "只写：结论、依据一句、下一步动作一句。",
        "standard": "短段落+不超过5条要点；每条能执行。",
        "deep": "可展开概念与推理，但仍用纯文本分段，最后必须给动作清单。",
    }.get(detail or "standard", "短段落+可执行要点。")
