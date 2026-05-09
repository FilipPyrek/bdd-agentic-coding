from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from users.service import AuthError, RegistrationError, get_profile, login, register
from users.store import UserRecord, _store
from users.token_store import _token_store

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/users", status_code=201, response_model=None)
def register_user(body: RegisterRequest) -> UserRecord | JSONResponse:
    try:
        return register(_store, body.name, body.email, body.password)
    except RegistrationError as exc:
        return JSONResponse(
            status_code=422,
            content={"field": exc.field, "error": exc.message},
        )


@router.post("/login")
def login_user(body: LoginRequest) -> JSONResponse:
    try:
        result = login(_store, _token_store, body.email, body.password)
        return JSONResponse(status_code=200, content=result)
    except AuthError as exc:
        return JSONResponse(status_code=401, content={"error": exc.message})


@router.get("/users/{user_id}/profile")
def get_user_profile(user_id: str, request: Request) -> JSONResponse:
    auth_header = request.headers.get("Authorization", "")
    token: str | None = None
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
    try:
        result = get_profile(_store, _token_store, user_id, token)
        return JSONResponse(status_code=200, content=result)
    except AuthError as exc:
        return JSONResponse(status_code=401, content={"error": exc.message})
