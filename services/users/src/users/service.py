from __future__ import annotations

import re
import uuid

from users.store import UserRecord, UserStore
from users.token_store import TokenStore

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistrationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


class AuthError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def register(
    store: UserStore,
    name: str | None,
    email: str | None,
    password: str | None,
) -> UserRecord:
    normalised_name = name.strip() if name is not None else None
    normalised_email = email.strip().lower() if email is not None else None

    if normalised_name is None:
        raise RegistrationError("name", "Name is required")
    if normalised_name == "":
        raise RegistrationError("name", "Name cannot be blank")
    if len(normalised_name) > 100:
        raise RegistrationError("name", "Name is too long")

    if normalised_email is None:
        raise RegistrationError("email", "Email is required")
    if not _EMAIL_RE.match(normalised_email):
        raise RegistrationError("email", "Invalid email address")
    if store.exists(normalised_email):
        raise RegistrationError("email", "Email already in use")

    if password is None:
        raise RegistrationError("password", "Password is required")
    if len(password) < 6:
        raise RegistrationError("password", "Password is too short")
    if len(password) > 100:
        raise RegistrationError("password", "Password is too long")

    user_id = str(uuid.uuid4())
    user: UserRecord = {
        "id": user_id,
        "name": normalised_name,
        "email": normalised_email,
        "password": password,
    }
    store.add(user)
    return {"id": user_id, "name": normalised_name, "email": normalised_email}


def login(
    store: UserStore,
    token_store: TokenStore,
    email: str | None,
    password: str | None,
) -> UserRecord:
    normalised_email = email.strip().lower() if email is not None else ""
    user = store.get(normalised_email)
    if user is None or user["password"] != password:
        raise AuthError("Invalid credentials")
    token = token_store.issue(user["id"])
    return {"token": token}


def get_profile(
    store: UserStore,
    token_store: TokenStore,
    user_id: str,
    token: str | None,
) -> UserRecord:
    resolved_id = token_store.get_user_id(token) if token is not None else None
    if resolved_id is None:
        raise AuthError("Not authorised")
    if resolved_id != user_id:
        raise AuthError("Not authorised")
    user = store.get_by_id(user_id)
    if user is None:
        raise AuthError("Not authorised")
    return {"id": user["id"], "name": user["name"], "email": user["email"]}
