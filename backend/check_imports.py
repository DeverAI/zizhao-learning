"""全模块导入与 OpenAPI 路由检查。"""
from __future__ import annotations

import importlib
import os
import sys
import traceback

BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

MODULES = [
    "config",
    "models.database",
    "services.security",
    "services.persona",
    "services.agent_bridge",
    "services.user_api_service",
    "services.generator",
    "services.agent_tools",
    "services.auth_service",
    "services.component_registry",
    "services.resident_service",
    "services.timetable_service",
    "services.media_service",
    "services.review_service",
    "services.offline_service",
    "services.quiz_service",
    "services.upload_service",
    "services.material_service",
    "services.agent_chat",
    "services.english_vocab",
    "routers.auth",
    "routers.english_tools",
    "routers.material",
    "routers.platform",
    "routers.quiz",
    "routers.review",
    "routers.shared",
    "routers.system",
    "routers.user_api",
    "routers.workspace",
    "main",
]

NEED_PATHS = [
    "/api/material/today",
    "/api/auth/email/login",
    "/api/offline/bundle",
    "/api/review/run",
    "/api/settings/apis/text",
    "/api/device/power",
    "/api/home",
    "/api/english/card",
    "/api/english/reveal",
    "/api/tools/calc",
]


def main() -> int:
    errors = []
    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"OK  {name}")
        except Exception as exc:  # noqa: BLE001
            errors.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")
            traceback.print_exc()
    try:
        from fastapi.testclient import TestClient
        from main import app

        with TestClient(app) as client:
            paths = set((client.get("/openapi.json").json() or {}).get("paths") or {})
            for p in NEED_PATHS:
                if p not in paths:
                    errors.append(("routes", p))
                    print(f"FAIL route {p}")
                else:
                    print(f"OK  route {p}")
    except Exception as exc:  # noqa: BLE001
        errors.append(("app", str(exc)))
        print(f"FAIL app: {exc}")
        traceback.print_exc()
    print(f"\nERRORS={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
