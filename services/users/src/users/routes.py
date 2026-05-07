from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from users.service import RegistrationError, register
from users.store import _store

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/users", status_code=201, response_model=None)
def register_user(body: RegisterRequest) -> dict | JSONResponse:
    try:
        return register(_store, body.name, body.email, body.password)
    except RegistrationError as exc:
        return JSONResponse(
            status_code=422,
            content={"field": exc.field, "error": exc.message},
        )


@router.post("/login")
def login(body: LoginRequest) -> JSONResponse:
    email = body.email.strip().lower()
    user = _store.get(email)
    if user is None or user["password"] != body.password:
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    return JSONResponse(status_code=200, content={"id": user["id"], "email": user["email"]})
