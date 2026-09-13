"""资料上传与收纳：PNG/WORD/TXT/PDF → 讲解/素材/三观/知识体系/英语背诵。"""
from __future__ import annotations

import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from typing import Optional

from config import STORAGE_DIR, atomic_write_json, ensure_dirs
from models import database as db
from services import persona

UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
INDEX_PATH = os.path.join(STORAGE_DIR, "upload_index.json")
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".txt", ".md", ".pdf", ".doc", ".docx"}
# 框架：讲解 / 素材 / 三观 / 知识体系 / 英语背诵
FRAMEWORKS = list(persona.FRAMEWORKS.keys())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_upload_dirs() -> None:
    ensure_dirs()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for fw in FRAMEWORKS:
        os.makedirs(os.path.join(UPLOAD_DIR, fw), exist_ok=True)


def load_index() -> list[dict]:
    ensure_upload_dirs()
    if not os.path.exists(INDEX_PATH):
        return []
    try:
        import json

        with open(INDEX_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_index(items: list[dict]) -> None:
    atomic_write_json(INDEX_PATH, items[-500:])


def _slug(name: str) -> str:
    base = os.path.splitext(os.path.basename(name or "file"))[0]
    base = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", base)[:40]
    return base or "file"


def extract_text_from_upload(path: str, ext: str) -> str:
    ext = ext.lower()
    if ext in {".txt", ".md"}:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read(20000)
        except OSError:
            return ""
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in {".doc", ".docx"}:
        return _extract_docx(path)
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        # 图片：不假装 OCR；只登记，文本由后续 OCR/人工补
        return ""
    return ""


def _extract_pdf(path: str) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(path)
        chunks = []
        for page in reader.pages[:20]:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)[:20000]
    except Exception:  # noqa: BLE001
        return ""


def _extract_docx(path: str) -> str:
    try:
        import zipfile
        from xml.etree import ElementTree as ET

        if path.lower().endswith(".doc"):
            return ""
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
        root = ET.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        texts = [t.text or "" for t in root.findall(".//w:t", ns)]
        return "".join(texts)[:20000]
    except Exception:  # noqa: BLE001
        return ""


def save_upload(
    filename: str,
    content: bytes,
    framework: str = "素材",
    title: str = "",
    source: str = "",
    tags: Optional[list[str]] = None,
    note: str = "",
    user_id: str = "",
) -> dict:
    from config import STORAGE_DIR as _ST

    ensure_upload_dirs()
    if framework not in FRAMEWORKS:
        framework = "素材"
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"unsupported extension: {ext}")
    if len(content) > 20 * 1024 * 1024:
        raise ValueError("file too large (>20MB)")

    safe_uid = re.sub(r"[^\w-]", "_", user_id or "anon")[:40] or "anon"
    uid = uuid.uuid4().hex[:12]
    safe_name = f"{_slug(filename)}_{uid}{ext}"
    dest_dir = os.path.join(_ST, "uploads", safe_uid, framework)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, safe_name)
    with open(dest, "wb") as f:
        f.write(content)

    text = extract_text_from_upload(dest, ext)
    title = (title or _slug(filename)).strip()
    source = source or f"upload:{framework}/{safe_name}"
    item = {
        "id": uid,
        "user_id": user_id or "",
        "filename": filename,
        "path": dest,
        "ext": ext,
        "framework": framework,
        "title": title,
        "source": source,
        "tags": tags or [],
        "note": note,
        "text_preview": (text or "")[:500],
        "text_len": len(text or ""),
        "created_at": _now(),
        "ingested": False,
    }
    index = load_index()
    index.append(item)
    save_index(index)

    # 素材框架：直接进计划表，走后续生成/去重
    if framework == "素材":
        db.insert_plan(
            [
                {
                    "domain": "upload",
                    "seq": int(datetime.now(timezone.utc).timestamp()) % 100000,
                    "title": title,
                    "source_hint": source,
                    "tags": tags or ["upload", ext.lstrip(".")],
                    "note": f"upload_id={uid}",
                }
            ]
        )
    if framework == "知识体系" and text:
        # 轻量进本地计划，便于后续灌知识树
        db.insert_plan(
            [
                {
                    "domain": "knowledge",
                    "seq": 1,
                    "title": title,
                    "source_hint": source,
                    "tags": ["knowledge", "upload"],
                    "note": f"待灌知识体系 upload_id={uid}",
                }
            ]
        )
    if framework == "英语背诵" and text:
        _seed_recitation_from_text(uid, title, text, source)
    return item


def _seed_recitation_from_text(upload_id: str, title: str, text: str, source: str) -> None:
    # 按空行/句号粗切段，生成可背诵条目
    paras = [p.strip() for p in re.split(r"\n\s*\n|\r\n\r\n", text) if p.strip()]
    if not paras:
        paras = [text.strip()[:500]]
    items = []
    for i, p in enumerate(paras[:12]):
        items.append(
            {
                "id": f"{upload_id}_{i}",
                "upload_id": upload_id,
                "title": title if i == 0 else f"{title}·段{i+1}",
                "passage": p[:800],
                "source": source,
                "created_at": _now(),
                "status": "pending",
            }
        )
    path = os.path.join(STORAGE_DIR, "recitation_items.json")
    existing = []
    if os.path.exists(path):
        try:
            import json

            with open(path, encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []
    atomic_write_json(path, existing + items)


def list_uploads(framework: Optional[str] = None, user_id: str = "") -> list[dict]:
    items = load_index()
    if user_id:
        items = [x for x in items if (x.get("user_id") or "") == user_id]
    if framework:
        items = [x for x in items if x.get("framework") == framework]
    out = []
    for x in items:
        y = dict(x)
        y.pop("path", None)
        out.append(y)
    return out


def get_upload(upload_id: str) -> Optional[dict]:
    for x in load_index():
        if x.get("id") == upload_id:
            return x
    return None
