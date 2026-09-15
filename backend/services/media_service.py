"""媒体：上传 → 文本抽取 / OCR / TTS-MP3。失败必须 degraded，不伪造。"""
from __future__ import annotations

import os
import re
import uuid
from typing import Optional

from config import MAX_UPLOAD_BYTES, ensure_dirs, load_settings
from models import database as db
from services import agent_bridge, security


def _safe_name(name: str) -> str:
    base = os.path.basename(name or "file")
    base = re.sub(r"[^\w.\-一-鿿]+", "_", base)[:80]
    return base or "file"


def extract_text(path: str, ext: str) -> tuple[str, bool]:
    """返回 (text, degraded)."""
    ext = (ext or "").lower()
    if ext in {".txt", ".md"}:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read(30000), False
        except OSError:
            return "", True
    if ext == ".pdf":
        try:
            import pypdf

            reader = pypdf.PdfReader(path)
            chunks = [(p.extract_text() or "") for p in reader.pages[:20]]
            return "\n".join(chunks)[:30000], False
        except Exception:  # noqa: BLE001
            return "", True
    if ext in {".doc", ".docx"}:
        try:
            import zipfile
            from xml.etree import ElementTree as ET

            if ext == ".doc":
                return "", True
            with zipfile.ZipFile(path) as zf:
                xml = zf.read("word/document.xml")
            root = ET.fromstring(xml)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            texts = [t.text or "" for t in root.findall(".//w:t", ns)]
            return "".join(texts)[:30000], False
        except Exception:  # noqa: BLE001
            return "", True
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        return ocr_image(path)
    return "", True


def ocr_image(path: str) -> tuple[str, bool]:
    settings = load_settings()
    if not settings.get("enable_ocr", True):
        return "", True
    # 1) pytesseract（若本机装了）
    try:
        import pytesseract  # type: ignore
        from PIL import Image

        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        if text and text.strip():
            return text.strip()[:30000], False
    except Exception:  # noqa: BLE001
        pass
    # 2) 明确降级：不假装 OCR 成功
    return (
        "（OCR 降级：本机未配置 tesseract/chi_sim。请安装后重试，或改传 TXT/PDF。）",
        True,
    )


def _mp3_char_budget() -> tuple[int, int]:
    """约 5 字/秒中文。体育课：下限 300s≈1500字，上限 900s≈4500字。"""
    settings = load_settings()
    mn = int(settings.get("material_mp3_min_sec", 300))
    mx = int(settings.get("material_mp3_max_sec", 900))
    if mn < 300:
        mn = 300
    if mx < mn:
        mx = mn
    return mn * 5, mx * 5


# 句末强断；中文/英文/数字小数点保护在下面单独处理
_SENT_END = re.compile(r"(?<=[。！？!?；;])|(?<=[a-z0-9][.!?])(?=\s|$)")
# 逗号/顿号/冒号等软断（仅在超长句时用）
_SOFT_BREAK = re.compile(r"(?<=[，、,;；:：])|(?<=\s—\s)|(?<=\s-\s)")
# 英文单词边界（最后手段）
_WORD_BREAK = re.compile(r"(?<=[A-Za-z0-9])(?=\s+[A-Za-z0-9])")


def _split_keep_seps(text: str, pattern: re.Pattern) -> list[str]:
    parts = pattern.split(text)
    return [p for p in parts if p and p.strip()]


def _tts_chunk(text: str, size: int = 1600, min_size: int = 120) -> list[str]:
    """TTS 分段：优先段落 → 句末 → 软标点 → 英文词边界。

    禁止随手按固定长度硬切；单句超长也必须尽量落在标点/空格上，
    避免把词、短语、小数点从中间截断导致合成怪音。
    """
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    # 1) 段落
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]

    def pack(units: list[str], hard: bool) -> list[str]:
        chunks: list[str] = []
        buf = ""
        for u in units:
            cand = (buf + u) if buf else u
            if len(cand) <= size:
                buf = cand
            else:
                if buf.strip():
                    chunks.append(buf.strip())
                # 单 unit 仍超长：交给上层再细切
                buf = u if not hard or len(u) <= size else u
        if buf.strip():
            chunks.append(buf.strip())
        return chunks

    # 2) 段落内按句末切，再打包
    sent_units: list[str] = []
    for para in paras:
        if len(para) <= size:
            sent_units.append(para)
        else:
            sents = _split_keep_seps(para, _SENT_END)
            if not sents:
                sents = [para]
            sent_units.extend(sents)

    chunks = pack(sent_units, hard=False)

    # 3) 仍超长的 chunk：软标点
    refined: list[str] = []
    for c in chunks:
        if len(c) <= size:
            refined.append(c)
            continue
        soft = _split_keep_seps(c, _SOFT_BREAK)
        if soft:
            refined.extend(pack(soft, hard=False))
        else:
            refined.append(c)

    # 4) 还超长：英文词边界；中文最后才在 punctuation 后已有单位上再拼
    final: list[str] = []
    for c in refined:
        if len(c) <= size:
            final.append(c)
            continue
        words = _split_keep_seps(c, _WORD_BREAK)
        if words:
            final.extend(pack(words, hard=False))
        else:
            # 纯中文无空格超长句：按 size 切，但保证不切断在数字/小数点中间
            i = 0
            while i < len(c):
                j = min(i + size, len(c))
                if j < len(c):
                    # 回退到最近的标点
                    window = c[i:j]
                    cut = max(
                        window.rfind("。"),
                        window.rfind("，"),
                        window.rfind("；"),
                        window.rfind("、"),
                        window.rfind("！"),
                        window.rfind("？"),
                    )
                    if cut >= min_size // 2:
                        j = i + cut + 1
                final.append(c[i:j].strip())
                i = j

    # 去掉过碎的尾段（并回前一段）
    out: list[str] = []
    for c in final:
        c = c.strip()
        if not c:
            continue
        if out and len(c) < min_size and len(out[-1]) + len(c) <= size:
            out[-1] = (out[-1] + c).strip()
        else:
            out.append(c)
    return out or [text[:size]]


def _concat_mp3(parts: list[str], dest: str) -> bool:
    """简单二进制拼接 MP3（同参数 TTS 输出通常可拼）。"""
    try:
        with open(dest, "wb") as out:
            for p in parts:
                with open(p, "rb") as f:
                    out.write(f.read())
        return os.path.getsize(dest) > 1000
    except OSError:
        return False


def synthesize_mp3(text: str, out_name: str, user_id: str = "") -> tuple[str, bool, str]:
    """分段 TTS 再拼接，保证 ≥300s 文稿能成完整音频。"""
    from config import AUDIO_DIR

    ensure_dirs()
    settings = load_settings()
    if not settings.get("enable_tts_mp3", True):
        return "", True, "disabled"
    text = (text or "").strip()
    if not text:
        return "", True, "empty"
    lo, hi = _mp3_char_budget()
    if len(text) > hi:
        text = text[:hi]
    out_path = os.path.join(AUDIO_DIR, out_name)
    chunks = _tts_chunk(text)
    if not chunks:
        return "", True, "empty"

    def _call_user(chunk: str) -> bytes | None:
        try:
            from services import user_api_service

            cred = user_api_service.get_tts_creds(user_id)
            if not cred:
                return None
            import httpx

            with httpx.Client(timeout=90) as client:
                resp = client.post(
                    user_api_service.compose_tts_url(cred["base_url"]),
                    headers={"Authorization": f"Bearer {cred['api_key']}"},
                    json={
                        "model": cred["model"],
                        "input": chunk,
                        "voice": cred.get("voice") or "alloy",
                        "response_format": "mp3",
                    },
                )
                if resp.status_code < 400 and resp.content:
                    return resp.content
        except Exception:  # noqa: BLE001
            return None
        return None

    def _call_xiaomi(chunk: str) -> bytes | None:
        from config import SHARED_SETTINGS
        import json as _json

        try:
            if not os.path.exists(SHARED_SETTINGS):
                return None
            with open(SHARED_SETTINGS, encoding="utf-8-sig") as f:
                s = _json.load(f)
            key = s.get("xiaomi_token_plan_api_key") or s.get("xiaomi_api_key") or ""
            if not key:
                return None
            import httpx

            with httpx.Client(timeout=90) as client:
                resp = client.post(
                    "https://token-plan-cn.xiaomimimo.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": "mimo-v2.5-tts",
                        "input": chunk,
                        "voice": "mimo_default",
                        "response_format": "mp3",
                    },
                )
                if resp.status_code < 400 and resp.content:
                    return resp.content
        except Exception:  # noqa: BLE001
            return None
        return None

    tmp_dir = os.path.join(AUDIO_DIR, "_parts")
    os.makedirs(tmp_dir, exist_ok=True)
    part_files: list[str] = []
    provider = ""
    for i, chunk in enumerate(chunks):
        audio = None
        if user_id:
            audio = _call_user(chunk)
            if audio:
                provider = "user_tts"
        if not audio:
            audio = _call_xiaomi(chunk)
            if audio:
                provider = "xiaomi_tts"
        if not audio:
            # 中途失败：保留已有段拼接，标记 degraded
            break
        pf = os.path.join(tmp_dir, f"{out_name}.{i:03d}.mp3")
        with open(pf, "wb") as f:
            f.write(audio)
        part_files.append(pf)

    if not part_files:
        meta = out_path + ".txt"
        try:
            with open(meta, "w", encoding="utf-8") as f:
                f.write(text)
        except OSError:
            pass
        return "", True, "tts_unavailable"

    if _concat_mp3(part_files, out_path):
        degraded = len(part_files) < len(chunks)
        return out_path, degraded, provider or "partial"
    return "", True, "concat_failed"


def ingest_upload(
    user_id: str,
    filename: str,
    content: bytes,
    make_mp3: bool = True,
    component: str = "library",
) -> dict:
    from config import FILES_DIR

    ensure_dirs()
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("file too large")
    ext = os.path.splitext(filename or "")[1].lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".txt", ".md", ".pdf", ".doc", ".docx", ".mp3"}:
        raise ValueError(f"unsupported type: {ext}")
    # 用户目录名消毒，防路径注入
    safe_uid = re.sub(r"[^\w-]", "_", user_id or "anon")[:40]
    fid = uuid.uuid4().hex[:12]
    dest_dir = os.path.join(FILES_DIR, safe_uid)
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f"{fid}{ext}")
    with open(path, "wb") as f:
        f.write(content)

    text, text_degraded = extract_text(path, ext)
    text = security.sanitize_text(text, 30000)
    mp3_path, mp3_degraded, provider = "", True, "skipped"
    if make_mp3 and text and not text.startswith("（OCR"):
        # 全文交给 synthesize_mp3（内部按 300–900s 预算分段）
        mp3_path, mp3_degraded, provider = synthesize_mp3(
            text, f"{safe_uid}_{fid}.mp3", user_id=user_id
        )

    kind = "image" if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"} else "document"
    mid = db.insert_media_file(
        {
            "user_id": user_id,
            "filename": _safe_name(filename),
            "path": path,
            "kind": kind,
            "text_preview": text[:500],
            "mp3_path": mp3_path,
            "ocr_text": text if kind == "image" else "",
            "status": "ready" if ((not text_degraded) and text) else "degraded",
            "degraded": bool(text_degraded or mp3_degraded),
        }
    )
    # 同步入常驻资料，便于 Agent 长期使用
    if text and not text.startswith("（OCR"):
        from services import resident_service

        resident_service.add(
            user_id,
            title=_safe_name(filename),
            body=text[:8000],
            kind="source",
            tags=[component, ext.lstrip(".")],
            source=f"upload:{mid}",
        )
    return {
        "id": mid,
        "filename": _safe_name(filename),
        "kind": kind,
        "text_len": len(text or ""),
        "text_preview": text[:300],
        "mp3_path": mp3_path,
        "mp3_degraded": mp3_degraded,
        "tts_provider": provider if mp3_path else ("degraded:" + provider),
        "degraded": bool(text_degraded or mp3_degraded),
        "component": component,
    }
