"""英语组件 API + 语音计算器 + 邻仓讲题。"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from models import database as db
from routers.auth import current_user
from services import (
    agent_bridge,
    agent_tools,
    english_vocab,
    generator,
    persona,
)

router = APIRouter(prefix="/api", tags=["english_tools"])


# ---------------- English vocab ----------------

@router.get("/english/banks")
async def banks(user: dict = Depends(current_user)):
    return english_vocab.bank_stats(user["id"])


@router.get("/english/card")
async def next_card(
    bank_id: str = "gaokao",
    mode: str = "en2cn",
    source: str = "new",
    sort: str = "freq",
    user: dict = Depends(current_user),
):
    """只出卡面，不带 answer（防泄露）。揭示用 /english/reveal。"""
    return english_vocab.next_card(user["id"], bank_id, mode, source, sort)


@router.get("/english/reveal")
async def reveal(bank_id: str = "gaokao", word: str = "", user: dict = Depends(current_user)):
    if not word:
        raise HTTPException(status_code=400, detail="word required")
    try:
        return english_vocab.reveal_answer(bank_id, word)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class GradeBody(BaseModel):
    bank_id: str = "gaokao"
    word: str
    grade: str  # known|vague|wrong


@router.post("/english/grade")
async def grade(body: GradeBody, user: dict = Depends(current_user)):
    try:
        return english_vocab.grade_card(user["id"], body.bank_id, body.word, body.grade)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/english/vague")
async def vague(word: str, user: dict = Depends(current_user)):
    r = english_vocab.vague_famous_sentence(word)
    if not r.get("ok"):
        raise HTTPException(status_code=404, detail=r.get("error") or "not found")
    return r


class WrongAdd(BaseModel):
    bank_id: str = "gaokao"
    word: str


@router.post("/english/wrong")
async def add_wrong(body: WrongAdd, user: dict = Depends(current_user)):
    try:
        return english_vocab.add_to_wrong_bank(user["id"], body.bank_id, body.word)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------- Voice calculator ----------------

class CalcBody(BaseModel):
    text: str = Field(description="口述或文本，如 3/8 百分之多少再乘12")


async def _speech_to_text(audio_b64: str, user_id: str) -> str:
    """MiMo 语音识别；失败返回空串，不伪造。"""
    if not audio_b64:
        return ""
    from services import user_api_service

    cred = user_api_service.get_text_creds(user_id)  # 未必是 ASR；尝试 shared xiaomi
    # 小米 ASR：优先共享 settings
    from config import SHARED_SETTINGS

    key = ""
    base = ""
    try:
        if os.path.exists(SHARED_SETTINGS):
            with open(SHARED_SETTINGS, encoding="utf-8-sig") as f:
                s = json.load(f)
            key = s.get("xiaomi_token_plan_api_key") or ""
            base = (s.get("xiaomi_token_plan_base_url") or "https://token-plan-cn.xiaomimimo.com/v1").rstrip("/")
    except (json.JSONDecodeError, OSError):
        key = ""
    if not key:
        return ""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{base}/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "mimo-asr", "input": audio_b64[:800000]},
            )
            if r.status_code < 400:
                data = r.json()
                return (data.get("text") or data.get("result") or "").strip()
    except Exception:  # noqa: BLE001
        return ""
    return ""


class CalcVoiceBody(BaseModel):
    audio_base64: Optional[str] = None
    text: Optional[str] = None


@router.post("/tools/calc")
async def calc(body: CalcVoiceBody, user: dict = Depends(current_user)):
    """口述→AI 生成算式→内置 calculator 工具算结果。无网/无语音则要求 text。"""
    text = (body.text or "").strip()
    if not text and body.audio_base64:
        text = await _speech_to_text(body.audio_base64, user["id"])
    if not text:
        raise HTTPException(
            status_code=400,
            detail="需要语音或文本；无网络/无语音服务时不显示录音，请改用文本",
        )
    # LLM 解析成算式
    prompt = (
        "把用户口述转成一行可计算算式。只输出算式本身，不要解释。\n"
        f"口述：{text}\n"
        "示例输入：三除以八再乘一百 → 输出：(3/8)*100"
    )
    content, ok, provider = await generator._chat_completion(
        [{"role": "user", "content": prompt}], temperature=0.0, user_id=user["id"]
    )
    expr = ""
    if ok and content:
        expr = re.sub(r"[`*\n]", "", content).strip()
        # 取第一行像算式的
        for line in expr.splitlines():
            if re.search(r"[\d(]", line):
                expr = line.strip()
                break
    if not expr:
        # 降级：直接从文本抽数字与符号
        expr = re.sub(r"[^\d+\-*/().%]", "", text.replace("×", "*").replace("÷", "/"))
        if not expr:
            raise HTTPException(status_code=422, detail="无法解析算式")
    result = agent_tools.dispatch("calculator", {"expression": expr})
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error") or "calc failed")
    return {
        "ok": True,
        "spoken": text,
        "expression": expr,
        "value": result.get("value"),
        "provider": provider if ok else "fallback_regex",
        "degraded": not ok,
        "no_markdown": True,
    }


# ---------------- 学习Agent 讲题 ----------------

class ExplainBody(BaseModel):
    question_id: str
    ask: str = "讲解这道题"


async def _fetch_neighbor_question(qid: str, user_id: str) -> dict:
    """HTTP 调学习Agent /api 题目详情。"""
    import httpx

    # 服务器/本机 learningAgent 默认 8000；可用 env 覆盖
    import os

    base = os.environ.get("LEARNING_AGENT_URL") or "http://127.0.0.1:8000"
    urls = [
        f"{base}/api/questions/{qid}",
        f"{base}/api/question/{qid}",
        f"{base}/api/ocr/question/{qid}",
    ]
    import httpx as hx

    async with hx.AsyncClient(timeout=20) as client:
        for u in urls:
            try:
                r = await client.get(u)
                if r.status_code == 200:
                    data = r.json()
                    return {"ok": True, "url": u, "data": data}
            except Exception:  # noqa: BLE001
                continue
    return {"ok": False, "error": "learningAgent question not reachable", "tried": urls}


@router.post("/tools/explain_question")
async def explain_question(body: ExplainBody, user: dict = Depends(current_user)):
    """讲邻仓题目：核心干路 + 麦克风确认「对吗」。"""
    q = await _fetch_neighbor_question(body.question_id, user["id"])
    if not q.get("ok"):
        raise HTTPException(status_code=502, detail=q.get("error") or "fetch failed")
    data = q.get("data") or {}
    # 粗取题干
    title = data.get("title") or data.get("question") or data.get("stem") or ""
    if isinstance(title, dict):
        title = json.dumps(title, ensure_ascii=False)[:2000]
    prompt = (
        "你是初三讲题教练。黑板很小，只写核心干路思路（不超过8行），不要展开细节。\n"
        "学生会带卷子，所以不抄原题全文。\n"
        f"题干摘要：{str(title)[:1500]}\n"
        f"用户要求：{body.ask}\n"
        "输出纯文本：\n"
        "1) 核心思路（干路）\n"
        "2) 一个易错点\n"
        "3) 最后单独一行：对吗？\n"
        "禁止 Markdown。"
    )
    content, ok, provider = await generator._chat_completion(
        [{"role": "user", "content": prompt}], temperature=0.3, user_id=user["id"]
    )
    if not ok or not content:
        raise HTTPException(status_code=502, detail="llm unavailable for explain")
    text = persona.strip_markdown(content)
    return {
        "ok": True,
        "question_id": body.question_id,
        "blackboard": text,
        "need_voice_confirm": True,
        "confirm_options": ["对", "问题"],
        "provider": provider,
        "no_markdown": True,
        "note": "板子端：对吗之后必须麦克风说「对」或「问题」",
    }


class ConfirmBody(BaseModel):
    question_id: str
    said: str  # 对 | 问题
    detail: str = ""


@router.post("/tools/explain_confirm")
async def explain_confirm(body: ConfirmBody, user: dict = Depends(current_user)):
    said = (body.said or "").strip()
    if said not in ("对", "问题", "yes", "no", "dui", "wenti"):
        raise HTTPException(status_code=400, detail="said must be 对 or 问题")
    ok = said in ("对", "yes", "dui")
    if ok:
        return {"ok": True, "understood": True, "next": "换下一题或结束本题讲解"}
    prompt = (
        "学生对刚才讲解说「问题」，请用纯文本再讲一次核心干路（更细一步，仍≤8行），并再次只问：对吗？\n"
        f"补充：{body.detail}\n禁止 Markdown。"
    )
    content, llm_ok, provider = await generator._chat_completion(
        [{"role": "user", "content": prompt}], temperature=0.3, user_id=user["id"]
    )
    if not llm_ok:
        return {
            "ok": True,
            "understood": False,
            "blackboard": "（降级）请指出卡在哪一步：条件转化 / 公式选择 / 计算 / 结论。",
            "degraded": True,
            "need_voice_confirm": True,
        }
    return {
        "ok": True,
        "understood": False,
        "blackboard": persona.strip_markdown(content),
        "need_voice_confirm": True,
        "provider": provider,
        "no_markdown": True,
    }
