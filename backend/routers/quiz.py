"""小测 API（需登录，按用户隔离今日素材）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.auth import current_user
from services import quiz_service

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.get("/build")
async def build(
    material_id: str = "",
    rounds: int = 5,
    user: dict = Depends(current_user),
):
    try:
        return quiz_service.build_quiz(material_id, rounds, user_id=user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class AnswerItem(BaseModel):
    id: str
    text: str


class GradeBody(BaseModel):
    material_id: str = ""
    answers: list[AnswerItem] = []
    use_llm: bool = False


@router.post("/grade")
async def grade(body: GradeBody, user: dict = Depends(current_user)):
    try:
        g = quiz_service.grade_quiz(
            body.material_id,
            [{"id": a.id, "text": a.text} for a in body.answers],
            user_id=user["id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if body.use_llm:
        g["coach"] = await quiz_service.coach_review(body.material_id, body.answers, g)
    return g
