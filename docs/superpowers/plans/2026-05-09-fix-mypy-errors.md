# Fix Mypy Errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all 57 mypy errors so that `make typecheck` passes with zero errors.

**Architecture:** Three independent fix areas: (1) suppress `behave` untyped-import noise via a mypy override, (2) annotate step functions with `behave`'s `Context` type, (3) add generic type arguments to bare `dict` usages in service/store/routes and annotate unannotated helpers. Each area maps to one task and one commit.

**Tech Stack:** Python 3.12, mypy (strict), behave, FastAPI, Starlette TestClient

---

## File Map

| File | Change |
|---|---|
| `pyproject.toml` | Add `[[tool.mypy.overrides]]` to silence `behave` import-untyped |
| `shared/src/shared/client.py` | Annotate `app` parameter and return type |
| `shared/src/shared/environment.py` | Annotate `before_scenario` parameters |
| `services/users/src/users/store.py` | Replace bare `dict` with `dict[str, Any]` |
| `services/users/src/users/service.py` | Replace bare `dict` with `dict[str, Any]`; annotate `token_store` param |
| `services/users/src/users/routes.py` | Replace bare `dict` return annotation |
| `services/users/features/steps/registration_steps.py` | Annotate all step functions |
| `services/users/features/steps/login_steps.py` | Annotate all step functions |
| `services/users/features/steps/profile_steps.py` | Annotate all step functions |

---

### Task 1: Silence `behave` untyped-import and annotate `shared/`

**Files:**
- Modify: `pyproject.toml`
- Modify: `shared/src/shared/client.py`
- Modify: `shared/src/shared/environment.py`

- [ ] **Step 1: Add mypy override for behave in `pyproject.toml`**

The current `pyproject.toml` ends at line 22. Add after the existing `[tool.mypy]` block:

```toml
# pyproject.toml — full file after change
[project]
name = "bdd-experiment"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv]
package = false

[tool.uv.workspace]
members = ["services/*", "e2e", "shared"]

[dependency-groups]
dev = ["ruff", "mypy", "shared"]

[tool.uv.sources]
shared = { workspace = true }

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
strict = true

[[tool.mypy.overrides]]
module = "behave.*"
ignore_missing_imports = true
```

- [ ] **Step 2: Annotate `shared/src/shared/client.py`**

`make_client` takes a ASGI app; the correct type from Starlette is `typing.Any` for the `app` param (Starlette's `TestClient.__init__` accepts `ASGIApp` but importing that type here adds complexity — `Any` is correct under strict mode when the concrete type is controlled by the caller).

Replace the entire file:

```python
"""httpx-based test client helpers for BDD step definitions."""
from __future__ import annotations

from typing import Any

from starlette.testclient import TestClient


def make_client(app: Any) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
```

- [ ] **Step 3: Annotate `shared/src/shared/environment.py`**

`behave.runner.Context` is the correct type. Import it and annotate:

```python
"""Base behave environment hooks: server startup/teardown and state reset."""
from __future__ import annotations

from behave.runner import Context

from users.main import app
from users.store import _store
from users.token_store import _token_store

from shared.client import make_client


def before_scenario(context: Context, scenario: object) -> None:
    _store.clear()
    _token_store.clear()
    context.client = make_client(app)
```

- [ ] **Step 4: Run typecheck and verify only step-file errors remain**

```bash
make typecheck 2>&1 | grep -v "features/steps"
```

Expected: only errors from `store.py`, `service.py`, `routes.py` remain (no `shared/` errors, no `import-untyped` for behave).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml shared/src/shared/client.py shared/src/shared/environment.py
git commit -m "fix: annotate shared helpers and suppress behave import-untyped"
```

---

### Task 2: Fix bare `dict` generics in service layer

**Files:**
- Modify: `services/users/src/users/store.py`
- Modify: `services/users/src/users/service.py`
- Modify: `services/users/src/users/routes.py`

The in-memory user record is `{"id": str, "name": str, "email": str, "password": str}`. We'll use `dict[str, Any]` throughout (a type alias keeps it DRY).

- [ ] **Step 1: Fix `services/users/src/users/store.py`**

Replace the entire file:

```python
from __future__ import annotations

from typing import Any

UserRecord = dict[str, Any]


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

    def add(self, user: UserRecord) -> None:
        self._users[user["email"].lower()] = user

    def exists(self, email: str) -> bool:
        return email.lower() in self._users

    def get(self, email: str) -> UserRecord | None:
        return self._users.get(email.lower())

    def get_by_id(self, user_id: str) -> UserRecord | None:
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def clear(self) -> None:
        self._users.clear()


_store = UserStore()
```

- [ ] **Step 2: Fix `services/users/src/users/service.py`**

The `token_store` parameter lacks annotation. Import `TokenStore` from `users.token_store` and use `UserRecord`. Replace the entire file:

```python
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
```

- [ ] **Step 3: Fix `services/users/src/users/routes.py`**

The `register_user` route returns `dict | JSONResponse`. Replace `dict` with `UserRecord`:

```python
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
```

- [ ] **Step 4: Run typecheck — verify service-layer errors are gone**

```bash
make typecheck 2>&1 | grep -E "store|service|routes"
```

Expected: no output (no errors from those files).

- [ ] **Step 5: Run BDD to make sure nothing is broken**

```bash
make bdd
```

Expected: all scenarios pass (same count as before).

- [ ] **Step 6: Commit**

```bash
git add services/users/src/users/store.py services/users/src/users/service.py services/users/src/users/routes.py
git commit -m "fix: add generic type arguments and annotate token_store params"
```

---

### Task 3: Annotate behave step functions

**Files:**
- Modify: `services/users/features/steps/registration_steps.py`
- Modify: `services/users/features/steps/login_steps.py`
- Modify: `services/users/features/steps/profile_steps.py`

All behave step callbacks receive `(context: Context) -> None`. Step functions that capture a named group from the step text receive it as an additional `str` parameter. The `scenario` parameter in `before_scenario` is `behave.model.Scenario`.

- [ ] **Step 1: Replace `services/users/features/steps/registration_steps.py`**

```python
from __future__ import annotations

from behave import given, then, when
from behave.runner import Context


@given("a visitor with a valid name, email, and password")
def step_visitor_valid_credentials(context: Context) -> None:
    context.registered_name = "Alice"
    context.registered_email = "alice@example.com"
    context.registered_password = "secret123"


@when("they register")
def step_they_register(context: Context) -> None:
    context.response = context.client.post(
        "/users",
        json={
            "name": context.registered_name,
            "email": context.registered_email,
            "password": context.registered_password,
        },
    )


@then("their account is created")
def step_account_created(context: Context) -> None:
    assert context.response.status_code == 201, (
        f"Expected 201, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "id" in body
    assert body["name"] == context.registered_name
    assert body["email"] == context.registered_email.lower()


@then("they can log in with their email and password")
def step_can_log_in(context: Context) -> None:
    response = context.client.post(
        "/login",
        json={
            "email": context.registered_email,
            "password": context.registered_password,
        },
    )
    assert response.status_code == 200, (
        f"Expected 200 from /login, got {response.status_code}: {response.text}"
    )


@given('a user has already registered with "{email}"')
def step_user_already_registered(context: Context, email: str) -> None:
    context.client.post(
        "/users",
        json={"name": "Existing User", "email": email, "password": "existing123"},
    )


@when('a visitor tries to register with "{email}"')
def step_visitor_tries_register_with_email(context: Context, email: str) -> None:
    context.response = context.client.post(
        "/users",
        json={"name": "New User", "email": email, "password": "newpass123"},
    )


@then('they see an error: "{message}"')
def step_see_error_message(context: Context, message: str) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("error") == message, (
        f"Expected error '{message}', got: {body}"
    )


@given("a visitor with a password shorter than 6 characters")
def step_password_too_short(context: Context) -> None:
    context.registered_name = "Bob"
    context.registered_email = "bob@example.com"
    context.registered_password = "abc"


@given("a visitor with a password longer than 100 characters")
def step_password_too_long(context: Context) -> None:
    context.registered_name = "Bob"
    context.registered_email = "bob@example.com"
    context.registered_password = "x" * 101


@when("they try to register")
def step_they_try_to_register(context: Context) -> None:
    payload = getattr(context, "missing_fields_payload", None)
    if payload is None:
        payload = {
            "name": context.registered_name,
            "email": context.registered_email,
            "password": context.registered_password,
        }
    context.response = context.client.post("/users", json=payload)


@then("they see an error that the password is too short")
def step_error_password_too_short(context: Context) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "password"
    assert "short" in body.get("error", "").lower(), f"Unexpected error: {body}"


@then("they see an error that the password is too long")
def step_error_password_too_long(context: Context) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "password"
    assert "long" in body.get("error", "").lower(), f"Unexpected error: {body}"


@given("a visitor with an invalid email address")
def step_invalid_email(context: Context) -> None:
    context.registered_name = "Carol"
    context.registered_email = "not-an-email"
    context.registered_password = "carol123"


@then("they see an error that the email is invalid")
def step_error_email_invalid(context: Context) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "email"
    assert "invalid" in body.get("error", "").lower(), f"Unexpected error: {body}"


@given("a visitor with a name longer than 100 characters")
def step_name_too_long(context: Context) -> None:
    context.registered_name = "A" * 101
    context.registered_email = "dave@example.com"
    context.registered_password = "dave1234"


@then("they see an error that the name is too long")
def step_error_name_too_long(context: Context) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "name"
    assert "long" in body.get("error", "").lower(), f"Unexpected error: {body}"


@given("a visitor with a blank name")
def step_blank_name(context: Context) -> None:
    context.registered_name = "   "
    context.registered_email = "eve@example.com"
    context.registered_password = "eve12345"


@given("a visitor without all required fields")
def step_missing_fields(context: Context) -> None:
    context.missing_fields_payload = {}


@then("they see errors indicating which fields are missing")
def step_errors_for_missing_fields(context: Context) -> None:
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    detail = body.get("detail", [])
    missing_field_names = {
        entry["loc"][-1] for entry in detail if entry.get("type") == "missing"
    }
    assert missing_field_names, f"Expected missing field errors, got: {body}"
```

- [ ] **Step 2: Replace `services/users/features/steps/login_steps.py`**

```python
from __future__ import annotations

from behave import given, then, when
from behave.runner import Context

_ALICE_EMAIL = "alice@example.com"
_ALICE_PASSWORD = "secret123"
_ALICE_NAME = "Alice"


def _register_alice(context: Context, email: str = _ALICE_EMAIL) -> None:
    context.client.post(
        "/users",
        json={"name": _ALICE_NAME, "email": email, "password": _ALICE_PASSWORD},
    )


@given("Alice has registered an account")
def step_alice_registered(context: Context) -> None:
    _register_alice(context)


@given('Alice has registered with "{email}"')
def step_alice_registered_with_email(context: Context, email: str) -> None:
    _register_alice(context, email=email)


@when("Alice logs in with her email and password")
def step_alice_logs_in(context: Context) -> None:
    context.response = context.client.post(
        "/login",
        json={"email": _ALICE_EMAIL, "password": _ALICE_PASSWORD},
    )


@then("she receives a token")
def step_she_receives_token(context: Context) -> None:
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "token" in body, f"Expected 'token' in response, got: {body}"
    assert body["token"], "Token should be non-empty"
    context.token = body["token"]


@given('no account exists for "{email}"')
def step_no_account_for_email(context: Context, email: str) -> None:
    pass


@when('a visitor tries to log in with "{email}"')
def step_visitor_logs_in_with_email(context: Context, email: str) -> None:
    context.response = context.client.post(
        "/login",
        json={"email": email, "password": "anypassword"},
    )


def _assert_invalid_credentials(context: Context) -> None:
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "invalid" in body.get("error", "").lower(), (
        f"Expected 'invalid credentials' error, got: {body}"
    )


@then("they are told their credentials are invalid")
def step_credentials_invalid(context: Context) -> None:
    _assert_invalid_credentials(context)


@when("Alice tries to log in with the wrong password")
def step_alice_logs_in_wrong_password(context: Context) -> None:
    context.response = context.client.post(
        "/login",
        json={"email": _ALICE_EMAIL, "password": "wrongpassword"},
    )


@then("she is told her credentials are invalid")
def step_alice_credentials_invalid(context: Context) -> None:
    _assert_invalid_credentials(context)


@when('she logs in with "{email}"')
def step_she_logs_in_with_email(context: Context, email: str) -> None:
    context.response = context.client.post(
        "/login",
        json={"email": email, "password": _ALICE_PASSWORD},
    )
```

- [ ] **Step 3: Replace `services/users/features/steps/profile_steps.py`**

```python
from __future__ import annotations

from behave import given, then, when
from behave.runner import Context

_ALICE_EMAIL = "alice@example.com"
_ALICE_PASSWORD = "secret123"
_ALICE_NAME = "Alice"

_BOB_EMAIL = "bob@example.com"
_BOB_PASSWORD = "bobpass1"
_BOB_NAME = "Bob"


def _assert_auth_error(context: Context) -> None:
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    error = body.get("error", "").lower()
    assert "authorised" in error or "authorized" in error, (
        f"Expected 'not authorised' error, got: {body}"
    )


def _register_and_login(
    context: Context, name: str, email: str, password: str
) -> tuple[str, str]:
    reg = context.client.post(
        "/users",
        json={"name": name, "email": email, "password": password},
    )
    assert reg.status_code == 201, f"Registration failed: {reg.text}"
    user_id = reg.json()["id"]

    login_resp = context.client.post(
        "/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["token"]
    return user_id, token


@given("Alice has registered and logged in")
def step_alice_registered_and_logged_in(context: Context) -> None:
    context.alice_id, context.alice_token = _register_and_login(
        context, _ALICE_NAME, _ALICE_EMAIL, _ALICE_PASSWORD
    )


@when("she requests her profile")
def step_she_requests_profile(context: Context) -> None:
    context.response = context.client.get(
        f"/users/{context.alice_id}/profile",
        headers={"Authorization": f"Bearer {context.alice_token}"},
    )


@then("she sees her name and email address")
def step_she_sees_name_and_email(context: Context) -> None:
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("name") == _ALICE_NAME, (
        f"Expected name '{_ALICE_NAME}', got: {body}"
    )
    assert body.get("email") == _ALICE_EMAIL, (
        f"Expected email '{_ALICE_EMAIL}', got: {body}"
    )


@given("a visitor who has not logged in")
def step_visitor_not_logged_in(context: Context) -> None:
    reg = context.client.post(
        "/users",
        json={"name": _ALICE_NAME, "email": _ALICE_EMAIL, "password": _ALICE_PASSWORD},
    )
    assert reg.status_code == 201, f"Registration failed: {reg.text}"
    context.target_user_id = reg.json()["id"]


@when("they try to view a profile")
def step_visitor_tries_view_profile(context: Context) -> None:
    context.response = context.client.get(f"/users/{context.target_user_id}/profile")


@then("they are told they must be logged in")
def step_must_be_logged_in(context: Context) -> None:
    _assert_auth_error(context)


@given("Alice and Bob have both registered and logged in")
def step_alice_and_bob_registered_and_logged_in(context: Context) -> None:
    context.alice_id, context.alice_token = _register_and_login(
        context, _ALICE_NAME, _ALICE_EMAIL, _ALICE_PASSWORD
    )
    context.bob_id, context.bob_token = _register_and_login(
        context, _BOB_NAME, _BOB_EMAIL, _BOB_PASSWORD
    )


@when("Alice requests Bob's profile")
def step_alice_requests_bob_profile(context: Context) -> None:
    context.response = context.client.get(
        f"/users/{context.bob_id}/profile",
        headers={"Authorization": f"Bearer {context.alice_token}"},
    )


@then("she is told she is not authorised")
def step_not_authorised(context: Context) -> None:
    _assert_auth_error(context)
```

- [ ] **Step 4: Run typecheck — expect zero errors**

```bash
make typecheck
```

Expected output:
```
uv run mypy .
Success: no issues found in 16 source files
```

- [ ] **Step 5: Run BDD to confirm nothing is broken**

```bash
make bdd
```

Expected: all scenarios pass.

- [ ] **Step 6: Commit**

```bash
git add services/users/features/steps/registration_steps.py \
        services/users/features/steps/login_steps.py \
        services/users/features/steps/profile_steps.py
git commit -m "fix: annotate behave step functions with Context type"
```

---

## Self-Review

**Spec coverage:**
- `import-untyped` for behave → Task 1 (pyproject.toml override)
- `no-untyped-def` in `shared/client.py` → Task 1
- `no-untyped-def` in `shared/environment.py` → Task 1
- `type-arg` in `store.py` → Task 2
- `type-arg` / `no-untyped-def` in `service.py` → Task 2
- `type-arg` in `routes.py` → Task 2
- `no-untyped-def` in all three step files → Task 3

All 57 errors are covered.

**Placeholder scan:** No TBDs, no "similar to Task N", all code blocks are complete.

**Type consistency:** `UserRecord` is defined in `store.py` (Task 2 Step 1) and imported in `service.py` (Task 2 Step 2) and `routes.py` (Task 2 Step 3). `Context` imported from `behave.runner` consistently across all three step files. `TokenStore` imported in `service.py` for annotation.
