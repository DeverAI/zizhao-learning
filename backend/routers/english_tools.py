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
    # 小米 ASR：走 get_ai_credentials（含 _access_denied 闸门），撤销后不偷用邻仓 key
    from services import agent_bridge

    xi = agent_bridge.get_ai_credentials().get("xiaomi") or {}
    key = xi.get("api_key") or ""
    base = (xi.get("base_url") or "https://token-plan-cn.xiaomimimo.com/v1").rstrip("/")
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


_CN_DIGIT = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}


def _cn_num(s: str) -> float | None:
    """中文数字 → 数值。支持 十/百/千/万 与混写（如「一百二十」）。"""
    s = (s or "").strip()
    if not s:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    units = {"十": 10, "百": 100, "千": 1000, "万": 10000}
    total, section, num = 0.0, 0.0, 0.0
    seen = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in _CN_DIGIT:
            num = _CN_DIGIT[ch]
            seen = True
            i += 1
            continue
        if ch in units:
            u = units[ch]
            seen = True
            if u == 10000:
                section = (section + num) * u
                total += section
                section, num = 0.0, 0.0
            else:
                # 「一百二」这种省略写法：二 直接乘下级单位
                section += (num if num else 1) * u
                num = 0.0
            i += 1
            continue
        return None
    if not seen:
        return None
    return total + section + num


def _cn_power_expr(text: str) -> str:
    """中文幂表达 → python 幂算式。

    只处理「X 的 N 次方/次幂」这一种说法（含中文数字）。
    其余一律返回空串交给模型，避免规则误伤正常算式。
    """
    m = re.search(r"([\d零〇一二两三四五六七八九十百千万.]+)\s*的\s*"
                  r"([\d零〇一二两三四五六七八九十百千万.]+)\s*次(?:方|幂)", text)
    if not m:
        return ""
    base = _cn_num(m.group(1))
    exp = _cn_num(m.group(2))
    if base is None or exp is None:
        return ""
    return f"{base:g}**{exp:g}"


# 中文运算符 → 算术符号。
# 顺序敏感：长词必须排在短词前面，否则「除以」会被「除」先吃掉变成 "/以"。
_CN_OP = [
    # 先剔除「问句尾巴」：这些词数量多、不含运算语义，早删早干净。
    # 「百分之多少」「占几成」是提问，不是「除以100」——不能当成运算符。
    ("百分之多少", ""), ("百分之几", ""), ("是多少", ""), ("多少", ""),
    ("占几成", ""), ("几成", ""), ("等于", ""), ("然后", ""), ("再", ""),
    # 真运算符
    ("除以", "/"), ("乘以", "*"), ("加上", "+"), ("减去", "-"),
    ("的平方", "**2"), ("的立方", "**3"),
    ("除", "/"), ("乘", "*"), ("加", "+"), ("减", "-"),
]

# 「A分之B」= B/A（中文分数是反的：八分之三 = 3/8）
_FRACTION_RE = re.compile(
    r"([\d零〇一二两三四五六七八九十百千万.]+)\s*分之\s*"
    r"([\d零〇一二两三四五六七八九十百千万.]+)"
)


def _cn_arith_expr(text: str) -> str:
    """纯中文口述 → 算式（无模型时的确定性兜底）。

    处理「三除以八再乘一百」这类：中文数字逐个转阿拉伯数字，
    中文运算符换符号。转不出来就返回空串，让上层报错，绝不猜。
    """
    s = (text or "").strip()
    if not s:
        return ""
    # 1) 「X的N次方」——必须最先做，「的」不能被后面的规则啃掉
    s = re.sub(
        r"([\d零〇一二两三四五六七八九十百千万.]+)\s*的\s*"
        r"([\d零〇一二两三四五六七八九十百千万.]+)\s*次(?:方|幂)",
        lambda m: f"{_cn_num(m.group(1)) or 0:g}**{_cn_num(m.group(2)) or 0:g}",
        s,
    )
    # 2) 「A分之B」= B/A。中文分数是反着说的：
    #    「八分之三」= 3/8。不处理的话「八分之三」会被抽成 83（灾难性错值）。
    def _frac(m: "re.Match[str]") -> str:
        den = _cn_num(m.group(1))
        num = _cn_num(m.group(2))
        if den in (None, 0) or num is None:
            return ""
        return f"({num:g}/{den:g})"

    s = _FRACTION_RE.sub(_frac, s)
    # 3) 中文运算符
    for cn, op in _CN_OP:
        s = s.replace(cn, op)
    # 中文数字 → 阿拉伯数字（长词优先，避免「一百」被「一」先切走）
    def _num_repl(m: "re.Match[str]") -> str:
        v = _cn_num(m.group(0))
        return f"{v:g}" if v is not None else m.group(0)

    s = re.sub(r"[\d零〇一二两三四五六七八九十百千万]+(?:\.[\d]+)?", _num_repl, s)
    # 只留算式字符；** 要保住
    s = re.sub(r"[^0-9+\-*/().]", "", s)
    return s if re.search(r"\d", s) else ""


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
    # 先本地抽「幂」：模型会把「二的一百次方」写成 2100（把"一百"当数字拼上去），
    # 数字对了算式全错，而且不会报错 —— 静默错结果比报错更坏。
    # 这里一次性拦截中文幂表达，交给下面的安全求值器（支持 **）。
    pow_expr = _cn_power_expr(text)
    content, ok, provider = "", False, "cn_power_rule"
    if not pow_expr:
        # LLM 解析成算式
        prompt = (
            "把用户口述转成一行可计算算式。只输出算式本身，不要解释。\n"
            f"口述：{text}\n"
            "示例输入：三除以八再乘一百 → 输出：(3/8)*100\n"
            "示例输入：二的一百次方 → 输出：2**100\n"
            "示例输入：根号二 → 输出：2**0.5\n"
            "硬规则：\n"
            "1) 幂用 ** 表示，绝不允许把「二的一百次方」写成 2100；\n"
            "2) 禁止出现 % 号（百分比写成 /100 或 *100）；\n"
            "3) 禁止中文与单位，只使用 0-9 + - * / ( ) . 这些字符（幂额外用 **）。\n"
            "4) 「百分之多少」「占几成」这类是问句，不是运算；"
            "按字面把前面的算式照抄，不要额外补 /100。"
        )
        content, ok, provider = await generator._chat_completion(
            [{"role": "user", "content": prompt}], temperature=0.0, user_id=user["id"]
        )
    # 本地幂规则命中就直接用；否则走模型输出解析。不能无条件重置 expr，
    # 否则会把上面算好的 pow_expr 冲掉（这个 bug 真发生过：改了规则却一点不生效）。
    expr = pow_expr or ""
    if not expr and ok and content:
        # 只剥 Markdown 外壳（反引号 / **加粗** / 列表符号），
        # 绝不能全局删 * —— 那会把乘法运算符一起删掉，(3/8)*100 变成 (3/8)100。
        cleaned = content.replace("```", "").replace("`", "")
        cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
        for line in cleaned.splitlines():
            line = re.sub(r"^\s*[*\-]\s+", "", line).strip()
            if re.search(r"[\d(]", line):
                expr = line
                break
    if not expr:
        # 降级 1：再扫一遍幂表达（模型可能把「的/次方」也照抄出来）
        expr = _cn_power_expr(text)
        if expr:
            provider = "cn_power_rule"
    if not expr:
        # 降级 2：中文数字 + 中文运算符整句转换（「三除以八再乘一百」）
        expr = _cn_arith_expr(text)
        if expr:
            provider = "cn_rule"
    if not expr:
        raise HTTPException(
            status_code=422,
            detail=f"无法解析算式（原文：{text}）",
        )

    def _try(e: str) -> dict:
        try:
            return agent_tools.dispatch("calculator", {"expression": e})
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    result = _try(expr)
    if not result.get("ok"):
        # 模型爱写 "3/8*100%"：% 是取模运算符，后面没有操作数 → 直接语法错误。
        # 清洗后再试一次，别让用户为一个百分号拿不到结果。
        # 注意保留 * 与 **：原来的字符类会连幂运算符一起删掉，2**100 变 2100。
        cleaned = expr.replace("%", "").replace(" ", "").replace("×", "*").replace("÷", "/")
        cleaned = re.sub(r"[^\d+\-*/().]", "", cleaned)
        if cleaned and cleaned != expr:
            retry = _try(cleaned)
            if retry.get("ok"):
                expr = cleaned
                result = retry
    if not result.get("ok"):
        raise HTTPException(
            status_code=422,
            detail=f"{result.get('error') or 'calc failed'}（算式：{expr}）",
        )
    # provider 语义：
    #   user_api / shared_api —— 模型给的算式
    #   cn_power_rule        —— 本地中文幂规则命中（不走模型，确定性最高）
    #   fallback_regex       —— 模型不可用，正则兜底抽的算式
    if not ok and provider in ("", None):
        provider = "fallback_regex"
    return {
        "ok": True,
        "spoken": text,
        "expression": expr,
        "value": result.get("value"),
        "provider": provider,
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
