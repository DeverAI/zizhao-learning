"""英语背词引擎：三库、会/模糊/不会、错词库、新库（去已会与错词）。"""
from __future__ import annotations

import json
import os
import random
import re
from datetime import datetime, timezone
from typing import Any, Optional

from config import BASE_DIR, STORAGE_DIR, atomic_write_json, ensure_dirs

BANKS_FILE = os.path.join(BASE_DIR, "data", "english_banks.json")
PROGRESS_DIR = "english_progress"

BANK_IDS = ("gaokao", "prep_collocations", "familiar_new_sense")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _progress_path(user_id: str) -> str:
    uid = re.sub(r"[^\w-]", "_", user_id or "anon")[:40] or "anon"
    return os.path.join(STORAGE_DIR, PROGRESS_DIR, f"{uid}.json")


def load_banks() -> dict:
    try:
        with open(BANKS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"banks": {}}
    if not isinstance(data, dict):
        return {"banks": {}}
    data.setdefault("banks", {})
    return data


def bank_items(bank_id: str) -> list[dict]:
    banks = load_banks().get("banks") or {}
    bank = banks.get(bank_id) or {}
    items = bank.get("items") or []
    return [x for x in items if isinstance(x, dict) and x.get("word")]


def load_progress(user_id: str) -> dict:
    ensure_dirs()
    path = _progress_path(user_id)
    data = {
        "user_id": user_id or "",
        "status": {},  # word -> known|vague|wrong
        "wrong_bank": [],  # [{word, cn, bank, sentence, at}]
        "history": [],
        "updated_at": "",
    }
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for k in data:
                    if k in raw:
                        data[k] = raw[k]
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_progress(prog: dict) -> None:
    ensure_dirs()
    path = _progress_path(prog.get("user_id") or "anon")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prog = dict(prog)
    prog["updated_at"] = _now()
    atomic_write_json(path, prog)


def _item_by_word(bank_id: str, word: str) -> Optional[dict]:
    for it in bank_items(bank_id):
        if it.get("word") == word:
            return it
    return None


def next_card(
    user_id: str,
    bank_id: str = "gaokao",
    mode: str = "en2cn",  # en2cn | cn2en
    source: str = "new",  # new | wrong | mixed
    sort: str = "freq",  # freq | alpha
) -> dict:
    """抽一张卡。new=去掉已会+错词库；wrong=只从错词库。"""
    if bank_id not in BANK_IDS:
        bank_id = "gaokao"
    if mode not in ("en2cn", "cn2en"):
        mode = "en2cn"
    prog = load_progress(user_id)
    status = prog.get("status") or {}
    wrong_words = {w.get("word") for w in (prog.get("wrong_bank") or []) if w.get("word")}
    items = bank_items(bank_id)
    if not items:
        return {"ok": False, "error": f"bank {bank_id} empty"}

    if source == "wrong":
        pool = [x for x in items if x.get("word") in wrong_words]
        if not pool:
            # 错词库条目可能来自其它 bank
            pool = []
            for bid in BANK_IDS:
                for x in bank_items(bid):
                    if x.get("word") in wrong_words:
                        pool.append(x)
        if not pool:
            return {"ok": True, "empty": True, "note": "错词库为空", "bank_id": bank_id, "mode": mode}
    elif source == "mixed":
        pool = items
    else:  # new：排除已会与已进错词的
        pool = [
            x
            for x in items
            if status.get(x.get("word")) != "known" and x.get("word") not in wrong_words
        ]
        if not pool:
            pool = [x for x in items if status.get(x.get("word")) != "known"]
        if not pool:
            return {
                "ok": True,
                "empty": True,
                "note": "本库已全部背会，可换库或清进度",
                "bank_id": bank_id,
                "mode": mode,
            }

    if sort == "alpha":
        pool = sorted(pool, key=lambda x: str(x.get("word") or "").lower())
        # 仍随机打散前 40，避免总从 A 开始
        head = pool[:40]
        card = random.choice(head) if head else pool[0]
    else:
        pool = sorted(pool, key=lambda x: -(int(x.get("freq") or 0)))
        # 按频次加权：前 30% 更容易抽到
        top = pool[: max(1, len(pool) // 3)]
        card = random.choice(top) if top and random.random() < 0.7 else random.choice(pool)

    word = card.get("word")
    show = {
        "word": word if mode == "en2cn" else "",
        "cn": card.get("cn") if mode == "cn2en" else "",
        "pos": card.get("pos") or "",
        "mode": mode,
        "bank_id": bank_id,
        "source": source,
        # 不在卡面给整句，避免直接泄露答案；模糊时走 /english/vague
        "has_sentence": bool(card.get("sentence")),
    }
    return {
        "ok": True,
        "card": show,
        # 故意不返回 answer；揭示走 reveal_answer
        "progress": {
            "known": sum(1 for v in status.values() if v == "known"),
            "vague": sum(1 for v in status.values() if v == "vague"),
            "wrong": len(wrong_words),
        },
    }


def grade_card(user_id: str, bank_id: str, word: str, grade: str) -> dict:
    """grade: known | vague | wrong。vague/wrong 进错词库；known 从错词移除。"""
    if grade not in ("known", "vague", "wrong"):
        raise ValueError("grade must be known|vague|wrong")
    prog = load_progress(user_id)
    status = prog.setdefault("status", {})
    wrong_bank = prog.setdefault("wrong_bank", [])
    item = _item_by_word(bank_id, word)
    if not item:
        for bid in BANK_IDS:
            item = _item_by_word(bid, word)
            if item:
                bank_id = bid
                break
    if not item:
        raise ValueError("word not in banks")

    status[word] = grade
    if grade == "known":
        wrong_bank = [w for w in wrong_bank if w.get("word") != word]
        prog["wrong_bank"] = wrong_bank
    else:
        if not any(w.get("word") == word for w in wrong_bank):
            wrong_bank.append(
                {
                    "word": word,
                    "cn": item.get("cn"),
                    "bank": bank_id,
                    "sentence": item.get("sentence") or "",
                    "at": _now(),
                    "grade": grade,
                }
            )
        prog["wrong_bank"] = wrong_bank
    hist = prog.setdefault("history", [])
    hist.append({"at": _now(), "word": word, "grade": grade, "bank": bank_id})
    prog["history"] = hist[-500:]
    save_progress(prog)
    return {
        "ok": True,
        "word": word,
        "grade": grade,
        "in_wrong_bank": word in {w.get("word") for w in prog.get("wrong_bank") or []},
        "known": sum(1 for v in status.values() if v == "known"),
        "wrong_count": len(prog.get("wrong_bank") or []),
    }


def vague_famous_sentence(word: str) -> dict:
    """模糊时：给名句应用 + 两个选择（含正确项）。"""
    item = None
    for bid in BANK_IDS:
        item = _item_by_word(bid, word)
        if item:
            break
    if not item:
        return {"ok": False, "error": "word not found"}
    correct = item.get("cn") or item.get("word")
    # 干扰项：同库随机
    bank_id = item.get("_bank") or "gaokao"
    # 从三库随机取别的释义
    others = []
    for bid in BANK_IDS:
        for x in bank_items(bid):
            if x.get("word") != word and x.get("cn"):
                others.append(x["cn"])
    random.shuffle(others)
    distractor = others[0] if others else "（无干扰项）"
    options = [correct, distractor]
    random.shuffle(options)
    return {
        "ok": True,
        "word": word,
        "sentence": item.get("sentence") or f"Example with {word}.",
        "pos": item.get("pos") or "",
        "options": options,
        "correct_index": options.index(correct),
        "note": "先看名句再选；选完仍会展示正确答案",
    }


def reveal_answer(bank_id: str, word: str) -> dict:
    item = _item_by_word(bank_id, word)
    if not item:
        for bid in BANK_IDS:
            item = _item_by_word(bid, word)
            if item:
                break
    if not item:
        raise ValueError("word not found")
    return {"ok": True, "answer": item}


def add_to_wrong_bank(user_id: str, bank_id: str, word: str) -> dict:
    return grade_card(user_id, bank_id, word, "wrong")


def bank_stats(user_id: str) -> dict:
    prog = load_progress(user_id)
    status = prog.get("status") or {}
    wrong = prog.get("wrong_bank") or []
    return {
        "banks": [
            {"id": bid, "title": (load_banks()["banks"].get(bid) or {}).get("title"), "count": len(bank_items(bid))}
            for bid in BANK_IDS
        ],
        "known": sum(1 for v in status.values() if v == "known"),
        "vague": sum(1 for v in status.values() if v == "vague"),
        "wrong_bank": len(wrong),
        "history_tail": (prog.get("history") or [])[-10:],
        "modes": ["en2cn", "cn2en"],
        "sources": ["new", "wrong", "mixed"],
    }
