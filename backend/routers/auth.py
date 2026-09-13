"""鉴权路由：邮箱验证码 / PassKey / ESP 设备 / sid Cookie。"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from config import SID_COOKIE_NAME
from services import auth_service, component_registry, security

router = APIRouter(prefix="/api/auth", tags=["auth"])


class EmailBody(BaseModel):
    email: str


class EmailLoginBody(BaseModel):
    email: str
    code: str = Field(min_length=4, max_length=12)


class PasskeyFinishBody(BaseModel):
    challenge: str
    credential_id: str
    public_key: str = ""


class PasskeyLoginBody(BaseModel):
    credential_id: str
    challenge: str
    signature: str


class DeviceLoginBody(BaseModel):
    device_id: str
    passkey: str


class DeviceProvisionBody(BaseModel):
    name: str = "esp-s3"


def _set_sid_cookie(response: Response, sid: str) -> None:
    token = security.make_session_token(sid)
    response.set_cookie(
        SID_COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )


def current_user(
    request: Request,
    zsid: Optional[str] = Cookie(default=None, alias=SID_COOKIE_NAME),
) -> dict:
    """仅接受带 HMAC 的 sid.signature；禁止裸 sid。"""
    raw = (zsid or request.headers.get("x-zizhao-sid") or "").strip()
    sid = security.verify_session_token(raw)
    if not sid:
        raise HTTPException(status_code=401, detail="not logged in")
    resolved = auth_service.resolve_sid(sid)
    if not resolved or not resolved.get("user"):
        raise HTTPException(status_code=401, detail="session expired")
    return resolved["user"]


@router.post("/email/send-code")
async def send_code(body: EmailBody, request: Request):
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("auth", f"code:{ip}:{body.email}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many requests") from exc
    return auth_service.issue_email_code(body.email)


@router.post("/email/login")
async def email_login(body: EmailLoginBody, request: Request, response: Response):
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("auth", f"login:{ip}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many requests") from exc
    try:
        user, sid = auth_service.login_with_email_code(body.email, body.code)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    _set_sid_cookie(response, sid)
    component_registry.ensure_user_defaults(user["id"])
    return {"ok": True, "user": {"id": user["id"], "email": user["email"], "display_name": user.get("display_name")}, "sid": security.make_session_token(sid)}


@router.post("/passkey/begin")
async def passkey_begin(user: dict = Depends(current_user)):
    return auth_service.register_passkey_begin(user["id"])


@router.post("/passkey/finish")
async def passkey_finish(body: PasskeyFinishBody, user: dict = Depends(current_user)):
    try:
        return auth_service.register_passkey_finish(
            user["id"], body.challenge, body.credential_id, body.public_key
        )
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


class PasskeyLoginBeginBody(BaseModel):
    credential_id: str


@router.post("/passkey/login/begin")
async def passkey_login_begin(body: PasskeyLoginBeginBody, request: Request):
    """登录前取一次性 challenge；客户端对 challenge 做 HMAC 后 login。"""
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("auth", f"pkb:{ip}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many requests") from exc
    try:
        return auth_service.begin_passkey_login(body.credential_id)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@router.post("/passkey/login")
async def passkey_login(body: PasskeyLoginBody, request: Request, response: Response):
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("auth", f"pk:{ip}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many requests") from exc
    try:
        user, sid = auth_service.login_with_passkey(
            body.credential_id, body.challenge, body.signature
        )
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    _set_sid_cookie(response, sid)
    return {"ok": True, "user": {"id": user["id"], "email": user["email"]}, "sid": security.make_session_token(sid)}


@router.post("/device/provision")
async def device_provision(body: DeviceProvisionBody, user: dict = Depends(current_user)):
    return auth_service.provision_device(user["id"], body.name)


@router.post("/device/login")
async def device_login(body: DeviceLoginBody, request: Request, response: Response):
    """ESP-S3：烧录的 device_id + passkey → 签发 sid。"""
    ip = security.client_ip(request)
    try:
        security.check_rate_limit("auth", f"dev:{ip}")
    except security.RateLimitError as exc:
        raise HTTPException(status_code=429, detail="too many requests") from exc
    try:
        user, sid = auth_service.login_with_device_passkey(body.device_id, body.passkey)
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    _set_sid_cookie(response, sid)
    return {
        "ok": True,
        "user_id": user["id"],
        "sid": security.make_session_token(sid),
        "expires_days": 30,
    }


@router.post("/device/revoke")
async def device_revoke(body: dict, user: dict = Depends(current_user)):
    try:
        return auth_service.revoke_device(user["id"], str(body.get("device_id") or ""))
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@router.get("/devices")
async def devices(user: dict = Depends(current_user)):
    return {"items": auth_service.list_devices(user["id"])}


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    component_registry.ensure_user_defaults(user["id"])
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name"),
    }


@router.post("/logout")
async def logout(request: Request, response: Response, zsid: Optional[str] = Cookie(default=None, alias=SID_COOKIE_NAME)):
    token = (zsid or "").strip()
    sid = security.verify_session_token(token) or (token if security.safe_sid(token) else None)
    if sid:
        auth_service.destroy_session(sid)
    response.delete_cookie(SID_COOKIE_NAME, path="/")
    return {"ok": True}
