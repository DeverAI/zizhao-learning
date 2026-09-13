"""素材生成：优先用共享源资料 + 海马体上下文；有密钥走 LLM，无密钥走可区分的降级模板。"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from services import agent_bridge

DEFAULT_SEEDS = {
    "philosophy": [
        {"title": "苏格拉底·无知之知", "source_hint": "《申辩篇》", "tags": ["认识论", "自省"]},
        {"title": "柏拉图·洞穴隐喻", "source_hint": "《理想国》卷七", "tags": ["现象与本质", "认知局限"]},
        {"title": "亚里士多德·四因说", "source_hint": "《物理学》", "tags": ["因果", "本体"]},
        {"title": "老子·反者道之动", "source_hint": "《道德经》", "tags": ["辩证", "转化"]},
        {"title": "庄子·齐物论要义", "source_hint": "《庄子》", "tags": ["相对性", "视角"]},
    ],
    "history": [
        {"title": "王安石变法·青苗法", "source_hint": "北宋熙宁变法", "tags": ["改革", "制度成本"]},
        {"title": "商鞅变法·军功爵", "source_hint": "战国秦", "tags": ["制度创新", "社会流动"]},
        {"title": "张骞通西域", "source_hint": "西汉", "tags": ["交流", "边疆"]},
        {"title": "郑和下西洋", "source_hint": "明初", "tags": ["航海", "朝贡体系"]},
        {"title": "洋务运动的限度", "source_hint": "晚清", "tags": ["现代化", "制度瓶颈"]},
    ],
    "classics": [
        {"title": "《劝学》· 学不可以已", "source_hint": "《荀子》", "tags": ["学习论", "积累"]},
        {"title": "《师说》· 师道", "source_hint": "韩愈", "tags": ["教育", "从师"]},
        {"title": "《赤壁赋》· 主客问答", "source_hint": "苏轼", "tags": ["变与不变", "主客"]},
        {"title": "宾语前置三型", "source_hint": "文言特殊句式", "tags": ["句法", "否定句"]},
        {"title": "词类活用·使动意动", "source_hint": "文言实词", "tags": ["词法", "句式"]},
    ],
}


def build_plan_seeds_from_shared() -> list[dict]:
    """共享课程体系里的自招条目 → 计划表种子。"""
    items: list[dict] = []
    for i, node in enumerate(agent_bridge.extract_zizhao_nodes("自招"), start=1):
        items.append(
            {
                "domain": "shared_curriculum",
                "seq": i,
                "title": f"{node.get('subject','')}·{node.get('label','')}",
                "source_hint": f"{node.get('grade','')} / {node.get('module','')} / band=自招",
                "tags": [node.get("subject") or "", node.get("module") or "", "自招"],
            }
        )
    return items


def build_gap_seeds_from_curriculum(limit: int = 80) -> list[dict]:
    """补漏种子：中档/难 band 的核心节点（不只自招）。"""
    items: list[dict] = []
    seq = 500
    for band in ("难", "中档"):
        for node in agent_bridge.extract_nodes(band=band, limit=limit):
            seq += 1
            items.append(
                {
                    "domain": "gap_fill",
                    "seq": seq,
                    "title": f"{node.get('subject','')}·{node.get('label','')}",
                    "source_hint": f"{node.get('grade','')} / {node.get('module','')} / band={band}",
                    "tags": [node.get("subject") or "", band, "补漏"],
                    "note": "curriculum_gap",
                }
            )
    return items


def build_gap_seeds_from_weak(limit: int = 15) -> list[dict]:
    """按海马体薄弱点匹配课程节点，生成补漏计划。"""
    weak = agent_bridge.weak_topics(max_n=limit)
    nodes = agent_bridge.extract_nodes(band=None, limit=400)
    by_label = {str(n.get("label") or ""): n for n in nodes}
    items: list[dict] = []
    seq = 800
    for w in weak:
        topic = str(w.get("topic") or "")
        match = by_label.get(topic)
        if not match:
            # 模糊：节点 label 包含主题或反之
            for label, n in by_label.items():
                if topic and (topic in label or label in topic):
                    match = n
                    break
        if not match:
            continue
        seq += 1
        items.append(
            {
                "domain": "gap_fill",
                "seq": seq,
                "title": f"{match.get('subject','')}·{match.get('label','')}",
                "source_hint": (
                    f"weak mastery={w.get('mastery')} / "
                    f"{match.get('grade','')} band={match.get('band','')}"
                ),
                "tags": [match.get("subject") or "", "弱项", "补漏"],
                "note": f"hippocampus_weak topic={topic}",
            }
        )
    return items


def build_default_plan_seeds() -> list[dict]:
    items: list[dict] = []
    seq = 1
    for domain, seeds in DEFAULT_SEEDS.items():
        for seed in seeds:
            items.append(
                {
                    "domain": domain,
                    "seq": seq,
                    "title": seed["title"],
                    "source_hint": seed.get("source_hint", ""),
                    "tags": seed.get("tags") or [],
                }
            )
            seq += 1
    return items


def jaccard(a: list[str] | set[str], b: list[str] | set[str]) -> float:
    sa, sb = set(a or []), set(b or [])
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def make_hard_key(domain: str, source: str, title: str) -> str:
    return f"{domain}|{source}|{title}"


def used_fingerprint_prompt(archive_rows: list[dict], limit: int = 80) -> str:
    lines = []
    for row in archive_rows[:limit]:
        keys = ",".join(row.get("concept_keys") or [])
        lines.append(
            f"- [{row.get('domain','')}] {row.get('title','')} | 概念：{keys}"
        )
    if not lines:
        return ""
    return "已使用过的素材（禁止重复，也不要换皮重出同一概念）：\n" + "\n".join(lines)


def _parse_json_block(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {}
    # 去掉可能的 markdown 围栏
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


async def _chat_completion(
    messages: list[dict],
    temperature: float = 0.4,
    user_id: str = "",
) -> tuple[str, bool, str]:
    """返回 (content, ok, provider)。优先用户自注册 OpenAI Key。"""
    from config import ENABLE_LLM_GENERATION

    if not ENABLE_LLM_GENERATION:
        return "", False, "disabled"
    import httpx

    if user_id:
        try:
            from services import user_api_service

            cred = user_api_service.get_text_creds(user_id)
            if cred:
                try:
                    async with httpx.AsyncClient(timeout=90) as client:
                        resp = await client.post(
                            user_api_service.compose_chat_url(cred["base_url"]),
                            headers={"Authorization": f"Bearer {cred['api_key']}"},
                            json={
                                "model": cred["model"],
                                "messages": messages,
                                "temperature": temperature,
                            },
                        )
                        if resp.status_code < 400:
                            content = (
                                (resp.json().get("choices") or [{}])[0]
                                .get("message", {})
                                .get("content")
                                or ""
                            )
                            if content:
                                return content, True, "user_api"
                except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
                    pass
        except Exception:  # noqa: BLE001
            pass

    creds = agent_bridge.get_ai_credentials()
    if not creds:
        return "", False, "none"

    # 优先 deepseek / custom / 小米
    def _rank(name: str) -> int:
        n = name.lower()
        if n.startswith("deepseek"):
            return 0
        if n.startswith("custom"):
            return 1
        if "xiaomi" in n or "mimo" in n:
            return 2
        return 3

    order = sorted(creds.keys(), key=_rank)
    for name in order:
        cfg = creds[name]
        base = (cfg.get("base_url") or "").rstrip("/")
        if not base:
            continue
        url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {cfg.get('api_key')}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cfg.get("model") or "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
        }
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code >= 400:
                    continue
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if content:
                    return content, True, name
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            continue
    return "", False, "unavailable"


def fallback_material(plan: dict, domain: str) -> dict:
    """无 LLM 时的明确降级产物：结构完整，但 degraded=True。"""
    title = plan.get("title") or "今日素材"
    source = plan.get("source_hint") or "本地大纲"
    keys = list(dict.fromkeys([*(plan.get("tags") or []), domain, "自招"]))
    body = (
        f"【降级模式·未调用外部模型】\n\n"
        f"主题：{title}\n"
        f"来源线索：{source}\n"
        f"领域：{domain}\n\n"
        f"一、核心提要\n"
        f"1. 这是自招素材系统在无法访问共享 AI 密钥时生成的占位讲解。\n"
        f"2. 正文结构、关键点与追问种子已就绪，便于对话挂载与去重链路验证。\n"
        f"3. 配置 学习Agent_new/backend/settings.json 中的 API Key 后，可自动升级为模型生成版。\n\n"
        f"二、与共享记忆的衔接\n"
        f"本条会读取学习Agent_new 的海马体掌握度，优先靠近薄弱主题。\n\n"
        f"三、追问种子\n"
        f"- {title} 的核心定义是什么？\n"
        f"- 它与中考/自招常见考法如何挂钩？\n"
        f"- 有没有容易混淆的近邻概念？\n"
    )
    return {
        "title": title,
        "source": source,
        "body": body,
        "key_points": [
            f"主题：{title}",
            f"来源：{source}",
            "当前为 degraded 生成，内容可作占位与链路验证",
        ],
        "followups": [
            f"{title} 的关键判据？",
            f"{title} 常见误区？",
            f"{title} 与共享课程体系中哪条前置相关？",
        ],
        "concept_keys": keys,
        "fingerprint": {
            "domain": domain,
            "title": title,
            "source": source,
        },
        "degraded": True,
        "provider": "fallback_template",
    }


async def xiaomi_web_search(query: str) -> str:
    """小米模型联网搜索（若共享 settings 提供 token-plan）。失败返回空串，不伪造。"""
    from config import SHARED_SETTINGS
    import os

    if not os.path.exists(SHARED_SETTINGS):
        return ""
    try:
        import json

        with open(SHARED_SETTINGS, encoding="utf-8-sig") as f:
            s = json.load(f)
    except (json.JSONDecodeError, OSError):
        return ""
    key = s.get("xiaomi_token_plan_api_key") or ""
    base = (s.get("xiaomi_token_plan_base_url") or "https://token-plan-cn.xiaomimimo.com/v1").rstrip("/")
    model = s.get("xiaomi_vision_model") or "mimo-v2.5"
    if not key:
        return ""
    import httpx

    messages = [
        {
            "role": "user",
            "content": (
                "请联网检索并用要点回答（标注来源站点名，不要编造 URL）："
                + query[:500]
            ),
        }
    ]
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "temperature": 0.3},
            )
            if resp.status_code < 400:
                data = resp.json()
                return (
                    (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                )[:4000]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return ""
    return ""


async def generate_from_plan(
    plan: dict,
    domain: str,
    negative_list: str = "",
    memory_ctx: Optional[dict] = None,
    user_id: str = "",
) -> dict:
    title = plan.get("title") or "今日素材"
    source = plan.get("source_hint") or ""
    memory_ctx = memory_ctx or {}
    weak = memory_ctx.get("weak_topics") or []
    weak_line = "；".join(
        f"{w.get('topic')}(mastery={w.get('mastery')})" for w in weak[:5]
    ) or "无"

    system = (
        "你是上海中考自主招生备考教练，擅长哲学、历史、高中古诗文与初中拔高知识点。"
        "输出严格 JSON，不要 markdown。字段："
        "title, source, body, key_points, followups, concept_keys, fingerprint。"
        "body 是可朗读讲解稿，800-1500字；concept_keys 为3-8个短概念词。"
        "fingerprint 形如 {person, work, concept, era, syntax}。"
        "可结合提供的检索摘要，但 source 必须可追溯。"
    )
    search_notes = ""
    try:
        from config import ENABLE_LLM_GENERATION as _llm_on

        if _llm_on:
            search_notes = await xiaomi_web_search(f"{title} {source} 自招 知识点")
    except Exception:  # noqa: BLE001
        search_notes = ""
    user = f"""请围绕计划条目展开一份自招素材（不要自由选题）。

domain: {domain}
title: {title}
source_hint: {source}
tags: {json.dumps(plan.get('tags') or [], ensure_ascii=False)}

共享记忆薄弱点：{weak_line}

{f"【联网检索摘要】\n{search_notes}\n" if search_notes else ""}

{negative_list}

要求：
1. 以知识点/篇目/概念为中心，笔试导向；
2. 不要与负例清单重复或换皮；
3. key_points 供对话追溯，followups 是多轮追问火种；
4. source 必须保留出处或检索线索。
"""
    content, ok, provider = await _chat_completion(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        user_id=user_id,
    )
    if ok:
        data = _parse_json_block(content)
        if data.get("body") and data.get("title"):
            keys = data.get("concept_keys") or []
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split(",") if k.strip()]
            fp = data.get("fingerprint") or {}
            if not isinstance(fp, dict):
                fp = {}
            return {
                "title": str(data.get("title") or title),
                "source": str(data.get("source") or source),
                "body": str(data.get("body") or ""),
                "key_points": list(data.get("key_points") or []),
                "followups": list(data.get("followups") or []),
                "concept_keys": [str(x) for x in keys],
                "fingerprint": fp,
                "degraded": False,
                "provider": provider,
            }
    return fallback_material(plan, domain)
