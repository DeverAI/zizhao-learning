"""时间表：CRUD + Agent 可读可写（不依赖邻仓）。"""
from __future__ import annotations

from models import database as db
from services import security

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _fmt_min(m: int) -> str:
    m = max(0, min(int(m), 24 * 60 - 1))
    return f"{m // 60:02d}:{m % 60:02d}"


def parse_hhmm(text: str) -> int:
    t = (text or "").strip()
    if ":" in t:
        h, m = t.split(":", 1)
        return int(h) * 60 + int(m)
    return int(t or 0)


def add_item(
    user_id: str,
    title: str,
    weekday: int,
    start: str | int,
    end: str | int,
    component: str = "",
    note: str = "",
) -> dict:
    title = security.sanitize_text(title, 120)
    if not title:
        raise ValueError("title required")
    wd = max(0, min(int(weekday), 6))
    sm = start if isinstance(start, int) else parse_hhmm(str(start))
    em = end if isinstance(end, int) else parse_hhmm(str(end))
    if em <= sm:
        em = sm + 30
    iid = db.insert_timetable(
        {
            "user_id": user_id,
            "title": title,
            "weekday": wd,
            "start_min": sm,
            "end_min": em,
            "component": security.sanitize_text(component, 40),
            "note": security.sanitize_text(note, 300),
        }
    )
    return {"id": iid, "title": title, "weekday": wd, "start_min": sm, "end_min": em}


def list_items(user_id: str) -> list[dict]:
    out = []
    for it in db.list_timetable(user_id):
        out.append(
            {
                **it,
                "weekday_label": WEEKDAYS[int(it.get("weekday") or 0) % 7],
                "start": _fmt_min(int(it.get("start_min") or 0)),
                "end": _fmt_min(int(it.get("end_min") or 0)),
            }
        )
    return out


def delete_item(user_id: str, item_id: str) -> bool:
    return db.delete_timetable(user_id, item_id)


def as_prompt_block(user_id: str) -> str:
    items = list_items(user_id)
    if not items:
        return "（时间表为空）"
    lines = [f"{WEEKDAYS[i]}：" for i in range(7)]
    for it in items:
        wd = int(it.get("weekday") or 0)
        lines[wd] += f" {it['start']}-{it['end']} {it['title']};"
    return "\n".join(lines)


def bulk_from_text(user_id: str, text: str) -> dict:
    """Agent 整理：每行「周X HH:MM-HH:MM 标题」。"""
    added = 0
    errors = []
    for raw in (text or "").splitlines():
        line = security.sanitize_text(raw, 200)
        if not line or line.startswith("#"):
            continue
        try:
            # 周一 08:00-09:00 数学
            wd = None
            for i, name in enumerate(WEEKDAYS):
                if name in line or name[1] in line[:3]:
                    wd = i
                    break
            if wd is None:
                errors.append(line)
                continue
            import re

            m = re.search(r"(\d{1,2}:\d{2})\s*[-–~]\s*(\d{1,2}:\d{2})", line)
            if not m:
                errors.append(line)
                continue
            title = line[m.end() :].strip(" ·-") or line
            add_item(user_id, title, wd, m.group(1), m.group(2))
            added += 1
        except (ValueError, IndexError):
            errors.append(line)
    return {"added": added, "errors": errors[:10]}
