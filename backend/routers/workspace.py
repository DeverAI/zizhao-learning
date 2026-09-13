"""上传 / 收纳 / 英语背诵 / 画像 接口。前台无 Markdown。"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from routers.auth import current_user
from services import agent_tools, persona, recitation, upload_service

router = APIRouter(prefix="/api", tags=["workspace"])


@router.get("/upload/frameworks")
async def frameworks():
    return {"frameworks": persona.FRAMEWORKS}


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    framework: str = Form("素材"),
    title: str = Form(""),
    source: str = Form(""),
    tags: str = Form(""),
    note: str = Form(""),
    user: dict = Depends(current_user),
):
    content = await file.read()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        item = upload_service.save_upload(
            filename=file.filename or "upload.bin",
            content=content,
            framework=framework,
            title=title,
            source=source,
            tags=tag_list,
            note=note,
            user_id=user["id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "item": {k: v for k, v in item.items() if k != "path"}}


@router.get("/upload/list")
async def upload_list(framework: Optional[str] = None, user: dict = Depends(current_user)):
    return {"items": upload_service.list_uploads(framework, user_id=user["id"])}


@router.get("/profile")
async def get_profile(user: dict = Depends(current_user)):
    return persona.load_profile(user["id"])


@router.post("/profile/reset")
async def reset_profile(user: dict = Depends(current_user)):
    persona.save_profile(persona.DEFAULT_PROFILE, user["id"])
    return {"ok": True}


class ToolInvokeBody(BaseModel):
    name: str
    arguments: dict = {}


@router.post("/agent/tool")
async def invoke_tool(body: ToolInvokeBody):
    result = agent_tools.dispatch(body.name, body.arguments)
    return result


class ReciteGradeBody(BaseModel):
    item_id: str
    text: str
    use_llm: bool = False


@router.get("/recitation/next")
async def recitation_next():
    item = recitation.pick_random("pending") or recitation.pick_random("done")
    if not item:
        raise HTTPException(status_code=404, detail="no items")
    # 不把全文以外的内部字段漏出
    pub = {k: item.get(k) for k in ("id", "title", "passage", "source", "status")}
    return pub


@router.post("/recitation/grade")
async def recitation_grade(body: ReciteGradeBody):
    grade = recitation.grade_attempt(body.item_id, body.text)
    if not grade.get("ok"):
        raise HTTPException(status_code=404, detail=grade.get("error"))
    if body.use_llm:
        coach = await recitation.coach_comment(body.item_id, body.text, grade)
        grade["coach"] = coach
    return grade


@router.get("/recitation/items")
async def recitation_items():
    return {"items": recitation.load_items(), "log_tail": recitation.load_log()[-10:]}
