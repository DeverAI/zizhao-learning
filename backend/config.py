"""自招素材系统配置：本地存储 + 指向学习Agent_new 的共享源。"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
MATERIALS_DIR = os.path.join(STORAGE_DIR, "materials")
AUDIO_DIR = os.path.join(MATERIALS_DIR, "audio")
ARCHIVE_BODY_DIR = os.path.join(MATERIALS_DIR, "archive_bodies")
DB_PATH = os.path.join(STORAGE_DIR, "material.db")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
SESSIONS_DIR = os.path.join(STORAGE_DIR, "sessions")
USERS_DIR = os.path.join(STORAGE_DIR, "users")
FILES_DIR = os.path.join(STORAGE_DIR, "files")
MEDIA_DIR = os.path.join(STORAGE_DIR, "media")
RESIDENT_DIR = os.path.join(STORAGE_DIR, "resident")
TIMETABLE_DIR = os.path.join(STORAGE_DIR, "timetable")
STATIC_DIR = os.path.join(BASE_DIR, "static")
EMAIL_OUTBOX = os.path.join(STORAGE_DIR, "email_outbox.json")

# 会话与设备密钥（可用环境变量覆盖；生产务必改）
SESSION_SECRET = os.environ.get("ZIZHAO_SESSION_SECRET") or "dev-only-change-me-zizhao"
SID_COOKIE_NAME = "zsid"
SID_TTL_DAYS = 30
EMAIL_CODE_TTL_SEC = 600
RATE_LIMIT = {
    "auth": {"window_sec": 60, "max": 10},
    "upload": {"window_sec": 60, "max": 20},
    "chat": {"window_sec": 60, "max": 30},
    # 前端主页会并行拉多个 GET，放宽 default
    "default": {"window_sec": 60, "max": 600},
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# 共享来源：左邻右舍的 学习Agent_new（相对路径，不写死用户目录）
# 可用环境变量 ZIZHAO_SHARED_ROOT 覆盖为绝对路径（本机配置，勿写进仓库）
SHARED_AGENT_ROOT = os.path.normpath(
    os.environ.get("ZIZHAO_SHARED_ROOT")
    or os.path.join(BASE_DIR, "..", "..", "学习Agent_new")
)
SHARED_BACKEND = os.path.join(SHARED_AGENT_ROOT, "backend")
SHARED_CURRICULUM = os.path.join(SHARED_BACKEND, "data", "curriculum_cn_junior.json")
SHARED_HIPPOCAMPUS = os.path.join(SHARED_BACKEND, "hippocampus", "profile.json")
SHARED_KNOWLEDGE_TREE = os.path.join(SHARED_BACKEND, "storage", "knowledge_tree.json")
SHARED_SETTINGS = os.path.join(SHARED_BACKEND, "settings.json")

# 开关
ENABLE_MATERIAL_SYSTEM = True
ENABLE_MATERIAL_AUDIO = False  # 无 TTS 密钥时保持关闭，避免伪造成功
ENABLE_SHARED_SOURCE = True
ENABLE_NIGHT_ARCHIVE = True
# 测试或离线时可置 False，强制走可区分的降级模板，不打真实模型
ENABLE_LLM_GENERATION = True

DEFAULT_SETTINGS = {
    "material_recent_days": 30,
    "material_dedup_threshold": 0.6,
    "material_pick_strategy": "round_robin",
    "material_generate_timeout": 90,
    "material_domains": ["philosophy", "history", "classics", "shared_curriculum"],
    "api_password": "",
    "port": 8010,
    "smtp_host": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from": "",
    "email_code_required": True,
    "enable_ocr": True,
    "enable_tts_mp3": True,
    "material_review_max_rounds": 4,
    "material_auto_optimize": True,
    "material_auto_tts_after_review": True,
    "device_power_enabled": True,
    "device_power_off": "04:30",
    "device_power_on": "06:00",
    "device_boot_idle_sec": 900,
    "device_volume_idle_sec": 600,
    "device_volume_idle_level": 1,
    "material_mp3_min_sec": 90,
    "material_mp3_max_sec": 300,
}

DOMAIN_ORDER = ["philosophy", "history", "classics", "shared_curriculum"]


def ensure_dirs() -> None:
    for path in (
        STORAGE_DIR,
        MATERIALS_DIR,
        AUDIO_DIR,
        ARCHIVE_BODY_DIR,
        SESSIONS_DIR,
        USERS_DIR,
        FILES_DIR,
        MEDIA_DIR,
        RESIDENT_DIR,
        TIMETABLE_DIR,
        STATIC_DIR,
    ):
        os.makedirs(path, exist_ok=True)


def load_settings() -> dict:
    merged = dict(DEFAULT_SETTINGS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8-sig") as f:
                data = json.load(f)
            if isinstance(data, dict):
                merged.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return merged


def save_settings(data: dict) -> None:
    ensure_dirs()
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=BASE_DIR,
            prefix=".settings-",
            suffix=".json",
            delete=False,
        ) as tf:
            temp_path = tf.name
            json.dump(data, tf, ensure_ascii=False, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
        os.replace(temp_path, SETTINGS_FILE)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def atomic_write_json(path: str, data: object) -> None:
    ensure_dirs()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=os.path.dirname(path) or ".",
            prefix=".tmp-",
            suffix=".json",
            delete=False,
        ) as tf:
            temp_path = tf.name
            json.dump(data, tf, ensure_ascii=False, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def beijing_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%Y-%m-%d")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
