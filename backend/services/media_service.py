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
    """按配置约束 MP3 时长（约 4.5 字/秒中文）。默认 90–300 秒。"""
    settings = load_settings()
    mn = int(settings.get("material_mp3_min_sec", 90))
    mx = int(settings.get("material_mp3_max_sec", 300))
    return max(400, mn * 5), max(600, mx * 5)


def synthesize_mp3(text: str, out_name: str, user_id: str = "") -> tuple[str, bool, str]:
    """返回 (path, degraded, provider). 优先用户自注册 TTS。"""
    from config import AUDIO_DIR

    ensure_dirs()
    settings = load_settings()
    if not settings.get("enable_tts_mp3", True):
        return "", True, "disabled"
    text = (text or "").strip()
    if not text:
        return "", True, "empty"
    lo, hi = _mp3_char_budget()
    if len(text) < lo // 2:
        # 太短不单独成音频，交给段落合并
        pass
    if len(text) > hi:
        text = text[:hi]
    out_path = os.path.join(AUDIO_DIR, out_name)

    # 1) 用户自注册 OpenAI 兼容 TTS
    if user_id:
        try:
            from services import user_api_service

            cred = user_api_service.get_tts_creds(user_id)
            if cred:
                import httpx

                url = user_api_service.compose_tts_url(cred["base_url"])
                try:
                    with httpx.Client(timeout=60) as client:
                        resp = client.post(
                            url,
                            headers={"Authorization": f"Bearer {cred['api_key']}"},
                            json={
                                "model": cred["model"],
                                "input": text[:2000],
                                "voice": cred.get("voice") or "alloy",
                                "response_format": "mp3",
                            },
                        )
                        if resp.status_code < 400 and resp.content:
                            with open(out_path, "wb") as f:
                                f.write(resp.content)
                            return out_path, False, "user_tts"
                except Exception:  # noqa: BLE001
                    pass
        except Exception:  # noqa: BLE001
            pass

    from config import SHARED_SETTINGS
    import json

    xiaomi_key = ""
    try:
        if os.path.exists(SHARED_SETTINGS):
            with open(SHARED_SETTINGS, encoding="utf-8-sig") as f:
                s = json.load(f)
            xiaomi_key = s.get("xiaomi_token_plan_api_key") or s.get("xiaomi_api_key") or ""
    except (json.JSONDecodeError, OSError):
        xiaomi_key = ""

    if xiaomi_key:
        try:
            import httpx

            url = "https://token-plan-cn.xiaomimimo.com/v1/audio/speech"
            headers = {"Authorization": f"Bearer {xiaomi_key}", "Content-Type": "application/json"}
            payload = {
                "model": "mimo-v2.5-tts",
                "input": text[:2000],
                "voice": "mimo_default",
                "response_format": "mp3",
            }
            with httpx.Client(timeout=60) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code < 400 and resp.content:
                    with open(out_path, "wb") as f:
                        f.write(resp.content)
                    return out_path, False, "xiaomi_tts"
        except Exception:  # noqa: BLE001
            pass
    meta = out_path + ".txt"
    try:
        with open(meta, "w", encoding="utf-8") as f:
            f.write(text[:2000])
    except OSError:
        pass
    return "", True, "tts_unavailable"


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
        mp3_path, mp3_degraded, provider = synthesize_mp3(
            text[:1500], f"{safe_uid}_{fid}.mp3", user_id=user_id
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
