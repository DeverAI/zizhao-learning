"""SQLite 数据访问层：material_plan / materials / material_archive / progress / audio。"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable, Optional

from config import utcnow

_lock = threading.RLock()


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


@contextmanager
def get_conn():
    # 运行时再取路径，便于测试隔离与配置热切换
    from config import DB_PATH, ensure_dirs

    ensure_dirs()
    with _lock:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db() -> None:
    with get_conn() as conn:
        # 若旧库带 UNIQUE(day_key) ON CONFLICT IGNORE，会导致静默丢插入；迁移到无该约束
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='materials'"
        ).fetchone()
        if row and "ON CONFLICT IGNORE" in (row["sql"] or ""):
            conn.executescript(
                """
                ALTER TABLE materials RENAME TO materials_legacy;
                CREATE TABLE materials (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT DEFAULT '',
                    domain TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    key_points TEXT DEFAULT '[]',
                    followups TEXT DEFAULT '[]',
                    concept_keys TEXT DEFAULT '[]',
                    fingerprint TEXT DEFAULT '{}',
                    audio_path TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    feedback TEXT DEFAULT '',
                    day_key TEXT,
                    created_at TEXT,
                    used_at TEXT,
                    degraded INTEGER DEFAULT 0
                );
                INSERT INTO materials SELECT * FROM materials_legacy;
                DROP TABLE materials_legacy;
                """
            )
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS material_plan (
                id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                seq INTEGER NOT NULL DEFAULT 0,
                title TEXT NOT NULL,
                source_hint TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                used_at TEXT,
                material_id TEXT DEFAULT '',
                note TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_plan_domain_seq ON material_plan(domain, seq);
            CREATE INDEX IF NOT EXISTS idx_plan_status ON material_plan(status);

            CREATE TABLE IF NOT EXISTS materials (
                id TEXT PRIMARY KEY,
                plan_id TEXT DEFAULT '',
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT DEFAULT '',
                body TEXT DEFAULT '',
                key_points TEXT DEFAULT '[]',
                followups TEXT DEFAULT '[]',
                concept_keys TEXT DEFAULT '[]',
                fingerprint TEXT DEFAULT '{}',
                audio_path TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                feedback TEXT DEFAULT '',
                day_key TEXT,
                created_at TEXT,
                used_at TEXT,
                degraded INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);
            CREATE INDEX IF NOT EXISTS idx_materials_day ON materials(day_key);

            CREATE TABLE IF NOT EXISTS material_archive (
                id TEXT PRIMARY KEY,
                material_id TEXT,
                domain TEXT,
                title TEXT,
                source TEXT DEFAULT '',
                concept_keys TEXT DEFAULT '[]',
                fingerprint TEXT DEFAULT '{}',
                one_line TEXT DEFAULT '',
                hard_key TEXT UNIQUE,
                used_day TEXT,
                archived_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_archive_domain ON material_archive(domain);
            CREATE INDEX IF NOT EXISTS idx_archive_used ON material_archive(used_day);

            CREATE TABLE IF NOT EXISTS material_progress (
                id TEXT PRIMARY KEY,
                material_id TEXT UNIQUE,
                segment_index INTEGER DEFAULT 0,
                offset_ms INTEGER DEFAULT 0,
                total_ms INTEGER DEFAULT 0,
                finished INTEGER DEFAULT 0,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_progress_mat ON material_progress(material_id);

            CREATE TABLE IF NOT EXISTS material_audio (
                id TEXT PRIMARY KEY,
                material_id TEXT,
                segment_index INTEGER DEFAULT 0,
                path TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                bytes INTEGER DEFAULT 0,
                text TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_audio_mat ON material_audio(material_id, segment_index);

            CREATE TABLE IF NOT EXISTS material_chat (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                material_id TEXT DEFAULT '',
                role TEXT,
                content TEXT,
                created_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_chat_session ON material_chat(session_id, created_at);

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                display_name TEXT DEFAULT '',
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS auth_sessions (
                sid TEXT PRIMARY KEY,
                user_id TEXT,
                kind TEXT DEFAULT 'user',
                device_id TEXT DEFAULT '',
                created_at TEXT,
                expires_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sess_user ON auth_sessions(user_id);
            CREATE TABLE IF NOT EXISTS email_codes (
                email TEXT PRIMARY KEY,
                code_hash TEXT,
                expires_at REAL,
                used INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS passkeys (
                credential_id TEXT PRIMARY KEY,
                user_id TEXT,
                public_key TEXT DEFAULT '',
                kind TEXT DEFAULT 'web',
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS passkey_challenges (
                user_id TEXT PRIMARY KEY,
                challenge TEXT,
                expires_at REAL
            );
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT DEFAULT '',
                passkey_hash TEXT,
                created_at TEXT,
                revoked INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS timetable_items (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                weekday INTEGER DEFAULT 0,
                start_min INTEGER DEFAULT 0,
                end_min INTEGER DEFAULT 0,
                component TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_tt_user ON timetable_items(user_id, weekday, start_min);
            CREATE TABLE IF NOT EXISTS resident_items (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                kind TEXT DEFAULT 'note',
                title TEXT,
                body TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_res_user ON resident_items(user_id, kind);
            CREATE TABLE IF NOT EXISTS user_components (
                user_id TEXT,
                component_id TEXT,
                enabled INTEGER DEFAULT 1,
                order_index INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}',
                PRIMARY KEY (user_id, component_id)
            );
            CREATE TABLE IF NOT EXISTS component_requests (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS media_files (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                filename TEXT,
                path TEXT,
                kind TEXT DEFAULT 'file',
                text_preview TEXT DEFAULT '',
                mp3_path TEXT DEFAULT '',
                ocr_text TEXT DEFAULT '',
                status TEXT DEFAULT 'stored',
                degraded INTEGER DEFAULT 0,
                created_at TEXT
            );
            """
        )
        # 多用户隔离：materials.user_id（'' = 遗留/单测）
        try:
            conn.execute("ALTER TABLE materials ADD COLUMN user_id TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_materials_user ON materials(user_id, day_key)"
            )
        except sqlite3.OperationalError:
            pass
        # 审核状态：pending/passed/failed；未 passed 不出音频
        for col, default in (
            ("review_status", "pending"),
            ("review_rounds", "0"),
            ("review_note", ""),
        ):
            try:
                conn.execute(f"ALTER TABLE materials ADD COLUMN {col} TEXT DEFAULT '{default}'")
            except sqlite3.OperationalError:
                pass


def _dumps(value: Any, default: Any) -> str:
    if value is None:
        value = default
    return json.dumps(value, ensure_ascii=False)


def _loads(raw: Any, default: Any):
    if raw in (None, ""):
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default


def _row_material(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["key_points"] = _loads(data.get("key_points"), [])
    data["followups"] = _loads(data.get("followups"), [])
    data["concept_keys"] = _loads(data.get("concept_keys"), [])
    data["fingerprint"] = _loads(data.get("fingerprint"), {})
    data["degraded"] = bool(data.get("degraded"))
    return data


def _row_plan(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["tags"] = _loads(data.get("tags"), [])
    return data


def _row_archive(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["concept_keys"] = _loads(data.get("concept_keys"), [])
    data["fingerprint"] = _loads(data.get("fingerprint"), {})
    return data


# ---------------------------------------------------------------- plan

def insert_plan(items: Iterable[dict]) -> int:
    count = 0
    with get_conn() as conn:
        for item in items:
            title = (item.get("title") or "").strip()
            domain = item.get("domain") or "shared_curriculum"
            if not title:
                continue
            exists = conn.execute(
                "SELECT 1 FROM material_plan WHERE domain=? AND title=?",
                (domain, title),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """
                INSERT INTO material_plan
                (id, domain, seq, title, source_hint, tags, status, note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("id") or gen_id(),
                    domain,
                    int(item.get("seq") or 0),
                    title,
                    item.get("source_hint") or "",
                    _dumps(item.get("tags"), []),
                    item.get("status") or "pending",
                    item.get("note") or "",
                ),
            )
            count += 1
    return count


def list_plan(status: Optional[str] = None) -> list[dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM material_plan WHERE status=? ORDER BY domain, seq",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM material_plan ORDER BY domain, seq"
            ).fetchall()
    return [_row_plan(r) for r in rows]


def pick_next_plan(domain: Optional[str] = None) -> Optional[dict]:
    with get_conn() as conn:
        if domain and domain != "any":
            rows = conn.execute(
                "SELECT * FROM material_plan WHERE status='pending' AND domain=? "
                "ORDER BY seq, rowid LIMIT 5",
                (domain,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM material_plan WHERE status='pending' ORDER BY seq, rowid LIMIT 20"
            ).fetchall()
        # pending 耗尽：回收 skipped（仍避开 used）
        if not rows:
            conn.execute(
                "UPDATE material_plan SET status='pending', note='' WHERE status='skipped'"
            )
            if domain and domain != "any":
                rows = conn.execute(
                    "SELECT * FROM material_plan WHERE status='pending' AND domain=? "
                    "ORDER BY seq, rowid LIMIT 5",
                    (domain,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM material_plan WHERE status='pending' ORDER BY seq, rowid LIMIT 20"
                ).fetchall()
    if not rows:
        return None
    pending = [_row_plan(r) for r in rows]
    if domain and domain != "any":
        return pending[0]
    # round_robin：按最近已用 domain 轮换
    used = last_used_domains()
    for plan in pending:
        if plan["domain"] not in used[:1]:
            return plan
    return pending[0]


def recycle_all_plans() -> int:
    """运维：把 used/skipped 全部收回 pending（慎用）。"""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE material_plan SET status='pending', note='' WHERE status!='pending'"
        )
        return cur.rowcount or 0


def last_used_domains(limit: int = 3) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT domain FROM materials WHERE domain IS NOT NULL AND domain != '' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [r["domain"] for r in rows]


def mark_plan_used(plan_id: str, material_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE material_plan SET status='used', used_at=?, material_id=? WHERE id=?",
            (utcnow().isoformat(), material_id, plan_id),
        )


def mark_plan_skipped(plan_id: str, note: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE material_plan SET status='skipped', note=? WHERE id=?",
            (note or "skipped", plan_id),
        )


# ---------------------------------------------------------------- materials

def get_today_material(day_key: str, user_id: str = "") -> Optional[dict]:
    """按用户取今日素材；user_id 为空时取遗留全局行（兼容旧测试）。"""
    with get_conn() as conn:
        if user_id:
            row = conn.execute(
                "SELECT * FROM materials WHERE day_key=? AND user_id=? "
                "AND status IN ('active','recent') ORDER BY created_at DESC LIMIT 1",
                (day_key, user_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM materials WHERE day_key=? AND (user_id='' OR user_id IS NULL) "
                "AND status IN ('active','recent') ORDER BY created_at DESC LIMIT 1",
                (day_key,),
            ).fetchone()
    return _row_material(row) if row else None


def get_material(material_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM materials WHERE id=?", (material_id,)
        ).fetchone()
    return _row_material(row) if row else None


def list_recent_materials(days_key_prefix: Optional[str] = None) -> list[dict]:
    with get_conn() as conn:
        if days_key_prefix:
            rows = conn.execute(
                "SELECT * FROM materials WHERE day_key LIKE ? ORDER BY day_key DESC",
                (f"{days_key_prefix}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM materials ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
    return [_row_material(r) for r in rows]


def insert_material(data: dict) -> dict:
    mid = data.get("id") or gen_id()
    now = utcnow().isoformat()
    day_key = data.get("day_key") or ""
    status = data.get("status") or "active"
    user_id = data.get("user_id") or ""
    with get_conn() as conn:
        # 应用层保证：同一用户同一天只有一条 active/recent 占用 day_key
        if day_key and status in ("active", "recent"):
            conn.execute(
                "UPDATE materials SET day_key='' WHERE day_key=? AND user_id=? AND id!=? "
                "AND status IN ('active','recent')",
                (day_key, user_id, mid),
            )
        conn.execute(
            """
            INSERT INTO materials
            (id, plan_id, domain, title, source, body, key_points, followups,
             concept_keys, fingerprint, audio_path, status, feedback, day_key,
             created_at, used_at, degraded, user_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                mid,
                data.get("plan_id") or "",
                data.get("domain") or "philosophy",
                data.get("title") or "未命名素材",
                data.get("source") or "",
                data.get("body") or "",
                _dumps(data.get("key_points"), []),
                _dumps(data.get("followups"), []),
                _dumps(data.get("concept_keys"), []),
                _dumps(data.get("fingerprint"), {}),
                data.get("audio_path") or "",
                status,
                data.get("feedback") or "",
                day_key,
                now,
                data.get("used_at") or now,
                1 if data.get("degraded") else 0,
                user_id,
            ),
        )
    out = get_material(mid)
    if out is None:
        raise RuntimeError(f"insert_material failed for id={mid}")
    return out


def update_material_status(material_id: str, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE materials SET status=? WHERE id=?", (status, material_id)
        )


def update_material_feedback(material_id: str, vote: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE materials SET feedback=? WHERE id=?", (vote, material_id)
        )


def demote_old_active(except_id: str, user_id: str = "") -> None:
    with get_conn() as conn:
        # 空 uid 只动本机遗留行，绝不能 demote 所有用户
        conn.execute(
            "UPDATE materials SET status='recent' WHERE status='active' AND user_id=? AND id != ?",
            (user_id, except_id),
        )


# ---------------------------------------------------------------- archive

def hard_key_exists(hard_key: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM material_archive WHERE hard_key=?", (hard_key,)
        ).fetchone()
        if row:
            return True
        parts = (hard_key or "").split("|")
        if len(parts) >= 3:
            source, title = parts[1], "|".join(parts[2:])
            row = conn.execute(
                "SELECT 1 FROM materials WHERE title=? AND source=? AND status!='failed'",
                (title, source),
            ).fetchone()
            return bool(row)
        return False


def archive_concept_sets(domain: Optional[str] = None, limit: int = 400) -> list[list[str]]:
    with get_conn() as conn:
        if domain:
            rows = conn.execute(
                "SELECT concept_keys FROM material_archive WHERE domain=? "
                "ORDER BY archived_at DESC LIMIT ?",
                (domain, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT concept_keys FROM material_archive ORDER BY archived_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [set(_loads(r["concept_keys"], [])) for r in rows]


def list_archive(limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM material_archive ORDER BY archived_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_archive(r) for r in rows]


def insert_archive(data: dict) -> Optional[str]:
    hard_key = data.get("hard_key") or ""
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM material_archive WHERE hard_key=?", (hard_key,)
        ).fetchone()
        if exists:
            return None
        aid = gen_id()
        conn.execute(
            """
            INSERT INTO material_archive
            (id, material_id, domain, title, source, concept_keys, fingerprint,
             one_line, hard_key, used_day, archived_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                aid,
                data.get("material_id") or "",
                data.get("domain") or "",
                data.get("title") or "",
                data.get("source") or "",
                _dumps(data.get("concept_keys"), []),
                _dumps(data.get("fingerprint"), {}),
                data.get("one_line") or "",
                hard_key,
                data.get("used_day") or "",
                utcnow().isoformat(),
            ),
        )
        return aid


def materials_ready_for_archive(recent_days: int) -> list[dict]:
    """status=recent 且 day_key 早于 N 天前的素材。"""
    from datetime import timedelta, timezone

    cutoff = (datetime.now(timezone.utc) - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM materials WHERE status='recent' AND day_key IS NOT NULL "
            "AND day_key < ? ORDER BY day_key",
            (cutoff,),
        ).fetchall()
    return [_row_material(r) for r in rows]


# ---------------------------------------------------------------- chat / progress

def save_chat(session_id: str, material_id: str, role: str, content: str) -> None:
    sid = safe_session_id(session_id)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO material_chat (id, session_id, material_id, role, content, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (gen_id(), sid, material_id, role, content, utcnow().isoformat()),
        )


def list_chat(session_id: str, limit: int = 20) -> list[dict]:
    sid = safe_session_id(session_id)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, material_id, created_at FROM material_chat "
            "WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
            (sid, limit),
        ).fetchall()
    return [dict(r) for r in reversed(list(rows))]


def safe_session_id(session_id: str) -> str:
    import hashlib
    import re

    sid = (session_id or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", sid):
        return sid
    return "s_" + hashlib.sha256(sid.encode("utf-8")).hexdigest()[:24]


def bind_session_material(session_id: str, material_id: str) -> None:
    from config import SESSIONS_DIR, atomic_write_json
    import os

    sid = safe_session_id(session_id)
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    data = {"session_id": sid, "material_id": material_id, "updated_at": utcnow().isoformat()}
    atomic_write_json(path, data)


def get_session_material(session_id: str) -> str:
    from config import SESSIONS_DIR
    import os

    sid = safe_session_id(session_id)
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("material_id") or ""
    except (json.JSONDecodeError, OSError):
        return ""


def upsert_progress(material_id: str, segment_index: int, offset_ms: int = 0,
                    total_ms: int = 0, finished: bool = False) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM material_progress WHERE material_id=?", (material_id,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE material_progress SET segment_index=?, offset_ms=?, total_ms=?, "
                "finished=?, updated_at=? WHERE material_id=?",
                (segment_index, offset_ms, total_ms, 1 if finished else 0,
                 utcnow().isoformat(), material_id),
            )
        else:
            conn.execute(
                "INSERT INTO material_progress "
                "(id, material_id, segment_index, offset_ms, total_ms, finished, updated_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (gen_id(), material_id, segment_index, offset_ms, total_ms,
                 1 if finished else 0, utcnow().isoformat()),
            )
        row = conn.execute(
            "SELECT * FROM material_progress WHERE material_id=?", (material_id,)
        ).fetchone()
    return dict(row)


def get_progress(material_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM material_progress WHERE material_id=?", (material_id,)
        ).fetchone()
    return dict(row) if row else None


def insert_audio_segments(material_id: str, segments: list[dict]) -> int:
    n = 0
    with get_conn() as conn:
        conn.execute("DELETE FROM material_audio WHERE material_id=?", (material_id,))
        for seg in segments:
            conn.execute(
                "INSERT INTO material_audio (id, material_id, segment_index, path, duration_ms, bytes, text) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    gen_id(),
                    material_id,
                    int(seg.get("segment_index") or 0),
                    seg.get("path") or "",
                    int(seg.get("duration_ms") or 0),
                    int(seg.get("bytes") or 0),
                    seg.get("text") or "",
                ),
            )
            n += 1
    return n


def list_audio_segments(material_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM material_audio WHERE material_id=? ORDER BY segment_index",
            (material_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- platform / auth / components

def insert_user(user: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, display_name, created_at) VALUES (?,?,?,?)",
            (user["id"], user["email"], user.get("display_name") or "", user.get("created_at") or ""),
        )


def find_user_by_email(email: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    return dict(row) if row else None


def get_user(user_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def put_email_code(email: str, code: str, expires_at: float) -> None:
    import hashlib

    h = hashlib.sha256(code.encode()).hexdigest()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO email_codes (email, code_hash, expires_at, used) VALUES (?,?,?,0) "
            "ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash, expires_at=excluded.expires_at, used=0",
            (email, h, expires_at),
        )


def consume_email_code(email: str, code: str, now: float) -> bool:
    import hashlib

    h = hashlib.sha256((code or "").encode()).hexdigest()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT code_hash, expires_at, used FROM email_codes WHERE email=?",
            (email,),
        ).fetchone()
        if not row or row["used"]:
            return False
        if float(row["expires_at"] or 0) < now:
            return False
        if row["code_hash"] != h:
            return False
        conn.execute("UPDATE email_codes SET used=1 WHERE email=?", (email,))
        return True


def insert_session(sess: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auth_sessions (sid, user_id, kind, device_id, created_at, expires_at) VALUES (?,?,?,?,?,?)",
            (
                sess["sid"],
                sess.get("user_id") or "",
                sess.get("kind") or "user",
                sess.get("device_id") or "",
                sess.get("created_at") or "",
                sess.get("expires_at") or "",
            ),
        )


def get_session(sid: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM auth_sessions WHERE sid=?", (sid,)).fetchone()
    return dict(row) if row else None


def delete_session(sid: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE sid=?", (sid,))


def put_pending_passkey(user_id: str, challenge: str, expires_at: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO passkey_challenges (user_id, challenge, expires_at) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET challenge=excluded.challenge, expires_at=excluded.expires_at",
            (user_id, challenge, expires_at),
        )


def consume_pending_passkey(user_id: str, challenge: str, now: float) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT challenge, expires_at FROM passkey_challenges WHERE user_id=?",
            (user_id,),
        ).fetchone()
        if not row or row["challenge"] != challenge:
            return False
        if float(row["expires_at"] or 0) < now:
            return False
        conn.execute("DELETE FROM passkey_challenges WHERE user_id=?", (user_id,))
        return True


def delete_sessions_for_device(device_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE device_id=?", (device_id,))


def upsert_passkey(rec: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO passkeys (credential_id, user_id, public_key, kind, created_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(credential_id) DO UPDATE SET user_id=excluded.user_id, public_key=excluded.public_key",
            (
                rec["credential_id"],
                rec["user_id"],
                rec.get("public_key") or "",
                rec.get("kind") or "web",
                rec.get("created_at") or "",
            ),
        )


def get_passkey(credential_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM passkeys WHERE credential_id=?", (credential_id,)
        ).fetchone()
    return dict(row) if row else None


def upsert_device(rec: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO devices (device_id, user_id, name, passkey_hash, created_at, revoked) VALUES (?,?,?,?,?,0) "
            "ON CONFLICT(device_id) DO UPDATE SET name=excluded.name, passkey_hash=excluded.passkey_hash, revoked=0",
            (
                rec["device_id"],
                rec["user_id"],
                rec.get("name") or "",
                rec.get("passkey_hash") or "",
                rec.get("created_at") or "",
            ),
        )


def get_device(device_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM devices WHERE device_id=?", (device_id,)).fetchone()
    return dict(row) if row else None


def revoke_device(device_id: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE devices SET revoked=1 WHERE device_id=?", (device_id,))


def list_devices(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM devices WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def insert_timetable(item: dict) -> str:
    iid = item.get("id") or gen_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO timetable_items (id, user_id, title, weekday, start_min, end_min, component, note, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                iid,
                item["user_id"],
                item.get("title") or "",
                int(item.get("weekday") or 0),
                int(item.get("start_min") or 0),
                int(item.get("end_min") or 0),
                item.get("component") or "",
                item.get("note") or "",
                item.get("created_at") or utcnow().isoformat(),
            ),
        )
    return iid


def list_timetable(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM timetable_items WHERE user_id=? ORDER BY weekday, start_min",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_timetable(user_id: str, item_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM timetable_items WHERE user_id=? AND id=?", (user_id, item_id)
        )
        return bool(cur.rowcount)


def insert_resident(item: dict) -> str:
    iid = item.get("id") or gen_id()
    now = utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO resident_items (id, user_id, kind, title, body, tags, source, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (
                iid,
                item["user_id"],
                item.get("kind") or "note",
                item.get("title") or "",
                item.get("body") or "",
                _dumps(item.get("tags"), []),
                item.get("source") or "",
                now,
                now,
            ),
        )
    return iid


def update_resident(user_id: str, item_id: str, **fields) -> bool:
    allowed = {"title", "body", "tags", "kind", "source"}
    sets, vals = [], []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "tags":
            v = _dumps(v, [])
        sets.append(f"{k}=?")
        vals.append(v)
    if not sets:
        return False
    vals.extend([utcnow().isoformat(), user_id, item_id])
    with get_conn() as conn:
        cur = conn.execute(
            f"UPDATE resident_items SET {', '.join(sets)}, updated_at=? WHERE user_id=? AND id=?",
            vals,
        )
        return bool(cur.rowcount)


def list_resident(user_id: str, kind: str | None = None, limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        if kind:
            rows = conn.execute(
                "SELECT * FROM resident_items WHERE user_id=? AND kind=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, kind, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM resident_items WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["tags"] = _loads(d.get("tags"), [])
        out.append(d)
    return out


def get_resident(user_id: str, item_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM resident_items WHERE user_id=? AND id=?", (user_id, item_id)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["tags"] = _loads(d.get("tags"), [])
    return d


def delete_resident(user_id: str, item_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM resident_items WHERE user_id=? AND id=?", (user_id, item_id)
        )
        return bool(cur.rowcount)


def set_user_components(user_id: str, items: list[dict]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM user_components WHERE user_id=?", (user_id,))
        for i, it in enumerate(items):
            conn.execute(
                "INSERT INTO user_components (user_id, component_id, enabled, order_index, config) VALUES (?,?,?,?,?)",
                (
                    user_id,
                    it.get("component_id") or "",
                    1 if it.get("enabled", True) else 0,
                    int(it.get("order_index") or i),
                    _dumps(it.get("config"), {}),
                ),
            )


def list_user_components(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM user_components WHERE user_id=? ORDER BY order_index",
            (user_id,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["config"] = _loads(d.get("config"), {})
        d["enabled"] = bool(d.get("enabled"))
        out.append(d)
    return out


def insert_component_request(req: dict) -> str:
    rid = req.get("id") or gen_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO component_requests (id, user_id, title, description, status, created_at) VALUES (?,?,?,?,?,?)",
            (
                rid,
                req["user_id"],
                req.get("title") or "",
                req.get("description") or "",
                "pending",
                utcnow().isoformat(),
            ),
        )
    return rid


def list_component_requests(user_id: str | None = None) -> list[dict]:
    with get_conn() as conn:
        if user_id:
            rows = conn.execute(
                "SELECT * FROM component_requests WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM component_requests ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
    return [dict(r) for r in rows]


def insert_media_file(rec: dict) -> str:
    mid = rec.get("id") or gen_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO media_files (id, user_id, filename, path, kind, text_preview, mp3_path, ocr_text, status, degraded, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                mid,
                rec["user_id"],
                rec.get("filename") or "",
                rec.get("path") or "",
                rec.get("kind") or "file",
                rec.get("text_preview") or "",
                rec.get("mp3_path") or "",
                rec.get("ocr_text") or "",
                rec.get("status") or "stored",
                1 if rec.get("degraded") else 0,
                utcnow().isoformat(),
            ),
        )
    return mid


def list_media_files(user_id: str, limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_id, filename, kind, text_preview, mp3_path, status, degraded, created_at "
            "FROM media_files WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["degraded"] = bool(d.get("degraded"))
        out.append(d)
    return out


def get_media_file(user_id: str, media_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM media_files WHERE user_id=? AND id=?", (user_id, media_id)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["degraded"] = bool(d.get("degraded"))
    return d

