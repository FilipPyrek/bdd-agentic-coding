# User Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement user registration for the users service so that all scenarios in `services/users/features/registration.feature` pass.

**Architecture:** Layered FastAPI service — `store.py` (in-memory dict), `service.py` (validation + business logic), `routes.py` (HTTP), `main.py` (app assembly). BDD scenarios run via httpx TestClient (ASGI, in-process). State resets between scenarios via a `before_scenario` hook that clears the module-level store.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, httpx TestClient, behave, uv

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `services/users/src/users/store.py` | Create | UserStore class + module singleton |
| `services/users/src/users/service.py` | Create | register(), RegistrationError |
| `services/users/src/users/routes.py` | Create | POST /users, POST /login (stub) |
| `services/users/src/users/main.py` | Create | FastAPI app assembly |
| `shared/src/shared/client.py` | Modify | make_client() factory |
| `shared/src/shared/environment.py` | Modify | before_scenario hook |
| `services/users/features/environment.py` | Create | behave hooks for users service |
| `services/users/features/steps/registration_steps.py` | Create | All step definitions |

---

## Task 1: UserStore

**Files:**
- Create: `services/users/src/users/store.py`

- [ ] **Step 1: Write `store.py`**

```python
from __future__ import annotations


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}

    def add(self, user: dict) -> None:
        self._users[user["email"].lower()] = user

    def exists(self, email: str) -> bool:
        return email.lower() in self._users

    def get(self, email: str) -> dict | None:
        return self._users.get(email.lower())

    def clear(self) -> None:
        self._users.clear()


_store = UserStore()
```

- [ ] **Step 2: Verify the file is importable**

```bash
uv run --package users python -c "from users.store import _store; print('ok')"
```

Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add services/users/src/users/store.py
git commit -m "feat(users): add UserStore"
```

---

## Task 2: Service layer — RegistrationError and register()

**Files:**
- Create: `services/users/src/users/service.py`

- [ ] **Step 1: Write `service.py`**

```python
from __future__ import annotations

import re
import uuid

from users.store import UserStore

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistrationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


def register(
    store: UserStore,
    name: str | None,
    email: str | None,
    password: str | None,
) -> dict:
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
    user = {
        "id": user_id,
        "name": normalised_name,
        "email": normalised_email,
        "password": password,
    }
    store.add(user)
    return {"id": user_id, "name": normalised_name, "email": normalised_email}
```

- [ ] **Step 2: Verify importable**

```bash
uv run --package users python -c "from users.service import register, RegistrationError; print('ok')"
```

Expected output: `ok`

- [ ] **Step 3: Commit**

```bash
git add services/users/src/users/service.py
git commit -m "feat(users): add register() and RegistrationError"
```

---

## Task 3: HTTP routes

**Files:**
- Create: `services/users/src/users/routes.py`

- [ ] **Step 1: Write `routes.py`**

```python
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


@router.post("/users", status_code=201)
def register_user(body: RegisterRequest) -> dict:
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
```

- [ ] **Step 2: Write `main.py`**

```python
from fastapi import FastAPI

from users.routes import router

app = FastAPI()
app.include_router(router)
```

- [ ] **Step 3: Verify app starts**

```bash
uv run --package users python -c "from users.main import app; print('ok')"
```

Expected output: `ok`

- [ ] **Step 4: Commit**

```bash
git add services/users/src/users/routes.py services/users/src/users/main.py
git commit -m "feat(users): add FastAPI routes and app"
```

---

## Task 4: Shared client and environment hooks

**Files:**
- Modify: `shared/src/shared/client.py`
- Modify: `shared/src/shared/environment.py`

- [ ] **Step 1: Write `shared/client.py`**

```python
"""httpx-based test client helpers for BDD step definitions."""
from __future__ import annotations

from httpx import Client
from starlette.testclient import TestClient


def make_client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
```

- [ ] **Step 2: Write `shared/environment.py`**

```python
"""Base behave environment hooks: server startup/teardown and state reset."""
from __future__ import annotations

from users.main import app
from users.store import _store
from shared.client import make_client


def before_scenario(context, scenario):
    _store.clear()
    context.client = make_client(app)
```

- [ ] **Step 3: Verify importable**

```bash
uv run --package users python -c "from shared.environment import before_scenario; print('ok')"
```

Expected output: `ok`

- [ ] **Step 4: Commit**

```bash
git add shared/src/shared/client.py shared/src/shared/environment.py
git commit -m "feat(shared): implement make_client and before_scenario hook"
```

---

## Task 5: behave environment.py for the users feature

**Files:**
- Create: `services/users/features/environment.py`

behave loads `environment.py` from the `features/` directory (not `features/steps/`).

- [ ] **Step 1: Create `services/users/features/environment.py`**

```python
from shared.environment import before_scenario

__all__ = ["before_scenario"]
```

- [ ] **Step 2: Verify behave picks it up (no steps yet, expect 0 scenarios)**

```bash
uv run --package users behave --dry-run 2>&1 | head -5
```

Expected: no import errors; output mentions feature file.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/environment.py
git commit -m "feat(users): wire behave environment hook"
```

---

## Task 6: Step definitions — successful registration

**Files:**
- Create: `services/users/features/steps/registration_steps.py`

These steps cover the "Successful registration" scenario.

- [ ] **Step 1: Write the initial step file with steps for Scenario 1**

```python
from __future__ import annotations

from behave import given, then, when


@given("a visitor with a valid name, email, and password")
def step_visitor_valid_credentials(context):
    context.registered_name = "Alice"
    context.registered_email = "alice@example.com"
    context.registered_password = "secret123"


@when("they register")
def step_they_register(context):
    context.response = context.client.post(
        "/users",
        json={
            "name": context.registered_name,
            "email": context.registered_email,
            "password": context.registered_password,
        },
    )


@then("their account is created")
def step_account_created(context):
    assert context.response.status_code == 201, (
        f"Expected 201, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "id" in body
    assert body["name"] == context.registered_name
    assert body["email"] == context.registered_email.lower()


@then("they can log in with their email and password")
def step_can_log_in(context):
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
```

- [ ] **Step 2: Run only this scenario**

```bash
uv run --package users behave features/registration.feature:7
```

Expected: 1 scenario passes.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/steps/registration_steps.py
git commit -m "feat(users): add steps for successful registration scenario"
```

---

## Task 7: Steps — duplicate email

This covers "Duplicate email is rejected" and "Email uniqueness is case-insensitive".

- [ ] **Step 1: Add steps to `registration_steps.py`**

Append these step definitions to the existing file:

```python
@given('a user has already registered with "{email}"')
def step_user_already_registered(context, email):
    context.client.post(
        "/users",
        json={"name": "Existing User", "email": email, "password": "existing123"},
    )


@when('a visitor tries to register with "{email}"')
def step_visitor_tries_register_with_email(context, email):
    context.response = context.client.post(
        "/users",
        json={"name": "New User", "email": email, "password": "newpass123"},
    )


@then('they see an error: "{message}"')
def step_see_error_message(context, message):
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("error") == message, (
        f"Expected error '{message}', got: {body}"
    )
```

- [ ] **Step 2: Run the two duplicate email scenarios**

```bash
uv run --package users behave features/registration.feature:13 features/registration.feature:48
```

Expected: 2 scenarios pass.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/steps/registration_steps.py
git commit -m "feat(users): add steps for duplicate email scenarios"
```

---

## Task 8: Steps — password validation

Covers "Password too short is rejected" and "Password too long is rejected".

- [ ] **Step 1: Add steps to `registration_steps.py`**

```python
@given("a visitor with a password shorter than 6 characters")
def step_password_too_short(context):
    context.registered_name = "Bob"
    context.registered_email = "bob@example.com"
    context.registered_password = "abc"


@given("a visitor with a password longer than 100 characters")
def step_password_too_long(context):
    context.registered_name = "Bob"
    context.registered_email = "bob@example.com"
    context.registered_password = "x" * 101


@when("they try to register")
def step_they_try_to_register(context):
    context.response = context.client.post(
        "/users",
        json={
            "name": context.registered_name,
            "email": context.registered_email,
            "password": context.registered_password,
        },
    )


@then("they see an error that the password is too short")
def step_error_password_too_short(context):
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "password"
    assert "short" in body.get("error", "").lower(), f"Unexpected error: {body}"


@then("they see an error that the password is too long")
def step_error_password_too_long(context):
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "password"
    assert "long" in body.get("error", "").lower(), f"Unexpected error: {body}"
```

- [ ] **Step 2: Run the two password scenarios**

```bash
uv run --package users behave features/registration.feature:18 features/registration.feature:23
```

Expected: 2 scenarios pass.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/steps/registration_steps.py
git commit -m "feat(users): add steps for password validation scenarios"
```

---

## Task 9: Steps — email format and name validation

Covers "Invalid email format is rejected", "Name too long is rejected", "Blank name is rejected".

- [ ] **Step 1: Add steps to `registration_steps.py`**

```python
@given("a visitor with an invalid email address")
def step_invalid_email(context):
    context.registered_name = "Carol"
    context.registered_email = "not-an-email"
    context.registered_password = "carol123"


@then("they see an error that the email is invalid")
def step_error_email_invalid(context):
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "email"
    assert "invalid" in body.get("error", "").lower(), f"Unexpected error: {body}"


@given("a visitor with a name longer than 100 characters")
def step_name_too_long(context):
    context.registered_name = "A" * 101
    context.registered_email = "dave@example.com"
    context.registered_password = "dave1234"


@then("they see an error that the name is too long")
def step_error_name_too_long(context):
    assert context.response.status_code == 422, (
        f"Expected 422, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("field") == "name"
    assert "long" in body.get("error", "").lower(), f"Unexpected error: {body}"


@given("a visitor with a blank name")
def step_blank_name(context):
    context.registered_name = "   "
    context.registered_email = "eve@example.com"
    context.registered_password = "eve12345"
```

- [ ] **Step 2: Run the three scenarios**

```bash
uv run --package users behave features/registration.feature:28 features/registration.feature:33 features/registration.feature:38
```

Expected: 3 scenarios pass.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/steps/registration_steps.py
git commit -m "feat(users): add steps for email format and name validation scenarios"
```

---

## Task 10: Steps — missing required fields

Covers "Missing required fields are rejected".

- [ ] **Step 1: Add steps to `registration_steps.py`**

```python
@given("a visitor without all required fields")
def step_missing_fields(context):
    context.missing_fields_payload = {}


@when("they try to register")  # already defined — behave reuses it
def step_they_try_to_register_missing(context):
    context.response = context.client.post(
        "/users",
        json=getattr(context, "missing_fields_payload", {
            "name": getattr(context, "registered_name", None),
            "email": getattr(context, "registered_email", None),
            "password": getattr(context, "registered_password", None),
        }),
    )


@then("they see errors indicating which fields are missing")
def step_errors_for_missing_fields(context):
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

Note: `"they try to register"` is already defined in Task 8. behave will use the same step for both scenarios. The `step_they_try_to_register_missing` definition above would cause a duplicate step error — **do not add it**. Instead, the `"they try to register"` step from Task 8 already posts `context.registered_name/email/password`. For the missing-fields scenario we need an empty payload. Refactor the existing `"they try to register"` step to handle both cases:

Replace the existing `step_they_try_to_register` (added in Task 8) with this version:

```python
@when("they try to register")
def step_they_try_to_register(context):
    payload = getattr(context, "missing_fields_payload", None)
    if payload is None:
        payload = {
            "name": context.registered_name,
            "email": context.registered_email,
            "password": context.registered_password,
        }
    context.response = context.client.post("/users", json=payload)
```

And add the `step_missing_fields` and `step_errors_for_missing_fields` steps only:

```python
@given("a visitor without all required fields")
def step_missing_fields(context):
    context.missing_fields_payload = {}


@then("they see errors indicating which fields are missing")
def step_errors_for_missing_fields(context):
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

- [ ] **Step 2: Run this scenario**

```bash
uv run --package users behave features/registration.feature:43
```

Expected: 1 scenario passes.

- [ ] **Step 3: Commit**

```bash
git add services/users/features/steps/registration_steps.py
git commit -m "feat(users): add steps for missing required fields scenario"
```

---

## Task 11: Run full suite and verify all scenarios pass

- [ ] **Step 1: Run all registration scenarios**

```bash
uv run --package users behave
```

Expected: 9 scenarios, 9 passed, 0 failed.

- [ ] **Step 2: Run lint**

```bash
make lint
```

Expected: no errors.

- [ ] **Step 3: Commit any lint fixes if needed, then final commit**

```bash
git add -A
git commit -m "feat(users): user registration — all scenarios passing"
```

---

## Quick Reference: Validation error messages

| Condition | Field | Error message |
|---|---|---|
| name missing | name | Name is required |
| name blank after strip | name | Name cannot be blank |
| name > 100 chars | name | Name is too long |
| email missing | email | Email is required |
| email bad format | email | Invalid email address |
| email duplicate | email | Email already in use |
| password missing | password | Password is required |
| password < 6 chars | password | Password is too short |
| password > 100 chars | password | Password is too long |
