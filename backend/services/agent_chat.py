"""带工具的素材对话 Agent：多轮 function call，纯文本输出。"""
from __future__ import annotations

import json
from typing import Any, Optional

from models import database as db
from services import agent_bridge, agent_tools, generator, material_service, persona


def _parse_tool_calls(message: dict) -> list[dict]:
    """兼容 OpenAI tool_calls 与部分内容里的 JSON 工具块。"""
    calls: list[dict] = []
    for tc in message.get("tool_calls") or []:
        fn = tc.get("function") or {}
        name = fn.get("name") or ""
        args = fn.get("arguments") or "{}"
        calls.append({"id": tc.get("id") or f"call_{len(calls)}", "name": name, "arguments": args})
    return calls


def _maybe_tool_from_text(text: str) -> list[dict]:
    """模型不肯走 tool_calls 时的兜底：识别 ```tool 或 {"tool": ...}。"""
    if not text:
        return []
    if "```tool" in text:
        start = text.find("```tool") + 7
        end = text.find("```", start)
        if end > start:
            chunk = text[start:end].strip()
            try:
                data = json.loads(chunk)
                if isinstance(data, dict) and data.get("name"):
                    return [{"id": "text_tool", "name": data["name"], "arguments": json.dumps(data.get("arguments") or {}, ensure_ascii=False)}]
            except json.JSONDecodeError:
                return []
    return []


async def _chat_once(messages: list[dict], tools: bool = True, user_id: str = "") -> tuple[str, bool, str, dict]:
    """返回 (content, ok, provider, raw_message)。"""
    from config import ENABLE_LLM_GENERATION

    if not ENABLE_LLM_GENERATION:
        return "", False, "disabled", {}
    import httpx

    # 用户自注册 Key 优先（无 tools 时走 generator；带 tools 用同一 Key）
    if user_id:
        try:
            from services import user_api_service

            cred = user_api_service.get_text_creds(user_id)
            if cred:
                schemas = agent_tools.openai_tool_schemas() if tools else None
                payload: dict[str, Any] = {
                    "model": cred["model"],
                    "messages": messages,
                    "temperature": 0.4,
                }
                if schemas:
                    payload["tools"] = schemas
                    payload["tool_choice"] = "auto"
                try:
                    async with httpx.AsyncClient(timeout=90) as client:
                        resp = await client.post(
                            user_api_service.compose_chat_url(cred["base_url"]),
                            headers={"Authorization": f"Bearer {cred['api_key']}"},
                            json=payload,
                        )
                        if resp.status_code < 400:
                            msg = (resp.json().get("choices") or [{}])[0].get("message") or {}
                            return msg.get("content") or "", True, "user_api", msg
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
                    pass
        except Exception:  # noqa: BLE001
            pass

    creds = agent_bridge.get_ai_credentials()
    if not creds:
        return "", False, "none", {}
    import httpx

    order = [k for k in creds if "deepseek" in k] + [k for k in creds if k.startswith("custom")] + [
        k for k in creds if "deepseek" not in k and not k.startswith("custom")
    ]
    schemas = agent_tools.openai_tool_schemas() if tools else None
    for name in order:
        cfg = creds[name]
        base = (cfg.get("base_url") or "").rstrip("/")
        if not base:
            continue
        url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        payload: dict[str, Any] = {
            "model": cfg.get("model") or "deepseek-chat",
            "messages": messages,
            "temperature": 0.4,
        }
        if schemas:
            payload["tools"] = schemas
            payload["tool_choice"] = "auto"
        headers = {
            "Authorization": f"Bearer {cfg.get('api_key')}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    continue
                data = resp.json()
                msg = (data.get("choices") or [{}])[0].get("message") or {}
                content = msg.get("content") or ""
                return content, True, name, msg
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            continue
    return "", False, "unavailable", {}


def _fallback_reply(material: dict, profile: dict) -> str:
    pref = profile.get("preferences") or {}
    detail = pref.get("detail_level") or "standard"
    agenda = profile.get("agenda") or {}
    nxt = agenda.get("next_action") or "用自己的话复述今日素材三个关键点，写完再继续问"
    title = material.get("title") or "今日素材"
    return persona.strip_markdown(
        "（降级：模型不可用，先给可执行步骤，不装作聊过了。）\n"
        f"素材：{title}\n"
        f"详略档：{detail}\n"
        f"下一步：{nxt}\n"
        "完成后把复述发来，我按找茬标准卡出处和概念边界。"
    )


async def agent_chat(
    session_id: str,
    message: str,
    material_id: Optional[str] = None,
    max_rounds: int = 4,
    user_id: str = "",
) -> dict:
    mid = material_id or db.get_session_material(session_id)
    if not mid:
        material = await material_service.get_or_create_today(user_id=user_id)
        mid = material["id"]
    else:
        material = db.get_material(mid) or await material_service.get_or_create_today(user_id=user_id)
        mid = material["id"]

    db.bind_session_material(session_id, mid)

    profile = persona.load_profile(user_id)
    profile = persona.observe_from_message(profile, message)
    persona.save_profile(profile, user_id)

    db.save_chat(session_id, mid, "user", message)

    history = db.list_chat(session_id, limit=16)
    resident_block = ""
    if user_id:
        try:
            from services import resident_service, timetable_service

            resident_block = (
                "\n\n【本仓常驻资料】\n"
                + resident_service.as_prompt_block(user_id, q="", limit=6)
                + "\n\n【本周时间表】\n"
                + timetable_service.as_prompt_block(user_id)
                + f"\n\n当前登录 user_id={user_id}（timetable_*/resident_* 工具请使用此 id）"
            )
        except Exception:  # noqa: BLE001
            resident_block = ""
    system = (
        persona.persona_system_block(profile, user_id=user_id)
        + "\n\n"
        + persona.detail_instruction(profile.get("preferences", {}).get("detail_level"))
        + "\n\n"
        + material_service.chat_system_prompt(material)
        + resident_block
        + "\n\n当前议程："
        + json.dumps(profile.get("agenda") or {}, ensure_ascii=False)
    )
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})

    tool_trail: list[dict] = []
    final_text = ""
    provider = "none"
    degraded = True
    refreshed = False

    def _inject_uid(args: dict | str) -> dict | str:
        """为本仓工具自动补 user_id，避免模型漏参。"""
        if not user_id:
            return args
        try:
            import json as _json

            data = _json.loads(args) if isinstance(args, str) else dict(args or {})
        except _json.JSONDecodeError:
            return args
        if isinstance(data, dict) and not data.get("user_id"):
            data["user_id"] = user_id
        return data

    for _ in range(max_rounds):
        content, ok, provider, msg = await _chat_once(messages, tools=True, user_id=user_id)
        calls = _parse_tool_calls(msg) if ok else []
        if not calls and content:
            calls = _maybe_tool_from_text(content)
        # 关键：有 tool_calls 时 content 可以为空，不能当失败
        if not ok or (not content and not calls):
            final_text = _fallback_reply(material, profile)
            degraded = True
            provider = provider or "none"
            break

        if not calls:
            final_text = persona.strip_markdown(content)
            degraded = False
            break

        # 把助手轮与工具结果写回
        messages.append(
            {
                "role": "assistant",
                "content": content or "",
                "tool_calls": msg.get("tool_calls")
                or [
                    {
                        "id": c["id"],
                        "type": "function",
                        "function": {"name": c["name"], "arguments": c["arguments"]},
                    }
                    for c in calls
                ],
            }
        )
        for call in calls:
            result = agent_tools.dispatch(call["name"], _inject_uid(call["arguments"]))
            tool_trail.append({"name": call["name"], "ok": result.get("ok"), "summary": str(result)[:200]})
            # 统计
            stats = profile.setdefault("stats", {})
            tool_stats = stats.setdefault("tool_calls", {})
            tool_stats[call["name"]] = int(tool_stats.get(call["name"]) or 0) + 1
            if call["name"] == "calculator":
                stats["calc_calls"] = int(stats.get("calc_calls") or 0) + 1
            if call["name"] == "refresh_material" and result.get("should_refresh"):
                try:
                    material = await material_service.refresh_material(
                        result.get("domain"), user_id=user_id
                    )
                    mid = material["id"]
                    db.bind_session_material(session_id, mid)
                    refreshed = True
                    result = {"ok": True, "refreshed": True, "title": material.get("title"), "material_id": mid}
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "error": f"refresh failed: {exc}"}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["name"],
                    "content": agent_tools.compact_tool_result(call["name"], result),
                }
            )
        persona.save_profile(profile, user_id)
        # 继续下一轮，让模型消费工具结果
        final_text = ""
        degraded = False

    if not final_text:
        # 工具轮后仍无正文：强制再要一轮纯回答
        messages.append(
            {
                "role": "user",
                "content": "根据以上工具结果，用纯文本直接回答用户，并给出下一步行动。不要调用工具。",
            }
        )
        content, ok, provider, _ = await _chat_once(messages, tools=False, user_id=user_id)
        if ok and content:
            final_text = persona.strip_markdown(content)
            degraded = False
        else:
            final_text = _fallback_reply(material, profile)
            degraded = True

    final_text = persona.strip_markdown(final_text)
    # 再保险：去掉残留星号强调
    final_text = final_text.replace("**", "").replace("__", "")

    db.save_chat(session_id, mid, "assistant", final_text)
    persona.save_profile(profile, user_id)

    return {
        "session_id": session_id,
        "material_id": mid,
        "reply": final_text,
        "degraded": degraded,
        "provider": provider,
        "tool_trail": tool_trail,
        "refreshed": refreshed,
        "profile_stage": profile.get("impression", {}).get("stage"),
        "detail_level": profile.get("preferences", {}).get("detail_level"),
        "no_markdown": True,
    }
