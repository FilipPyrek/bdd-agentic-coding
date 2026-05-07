# Login Token and Profile Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all 7 failing BDD scenarios in `login.feature` and `profile.feature` pass, and keep all 9 registration scenarios passing.

**Architecture:** Add a `TokenStore` class for token→user_id mapping; extend `UserStore` with ID lookup; add `login()` and `get_profile()` service functions following the same pattern as `register()`; update the `/login` route and add `GET /users/{user_id}/profile`; write step definitions for login and profile features.

**Tech Stack:** Python 3.12, FastAPI, behave, httpx/starlette TestClient, uv workspaces.

---

## File Map

| Action | File |
|--------|------|
| Modify | `services/users/src/users/store.py` — add `get_by_id` |
| Create | `services/users/src/users/token_store.py` — `TokenStore` class + singleton |
| Modify | `services/users/src/users/service.py` — add `AuthError`, `login()`, `get_profile()` |
| Modify | `services/users/src/users/routes.py` — update `/login`, add `/users/{user_id}/profile` |
| Modify | `shared/src/shared/environment.py` — clear `_token_store` in `before_scenario` |
| Create | `services/users/features/steps/login_steps.py` — step defs for `login.feature` |
| Create | `services/users/features/steps/profile_steps.py` — step defs for `profile.feature` |

---

### Task 1: Add `get_by_id` to `UserStore`

**Files:**
- Modify: `services/users/src/users/store.py`

- [ ] **Step 1: Add the method**

Open `services/users/src/users/store.py`. After the `get` method, add:

```python
def get_by_id(self, user_id: str) -> dict | None:
    for user in self._users.values():
        if user["id"] == user_id:
            return user
    return None
```

The full file should now look like:

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

    def get_by_id(self, user_id: str) -> dict | None:
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def clear(self) -> None:
        self._users.clear()


_store = UserStore()
```

- [ ] **Step 2: Run existing scenarios to confirm nothing broke**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 3: Commit**

```bash
git add services/users/src/users/store.py
git commit -m "feat(users): add get_by_id to UserStore"
```

---

### Task 2: Create `TokenStore`

**Files:**
- Create: `services/users/src/users/token_store.py`

- [ ] **Step 1: Create the file**

```python
from __future__ import annotations

import uuid


class TokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    def issue(self, user_id: str) -> str:
        token = str(uuid.uuid4())
        self._tokens[token] = user_id
        return token

    def get_user_id(self, token: str) -> str | None:
        return self._tokens.get(token)

    def clear(self) -> None:
        self._tokens.clear()


_token_store = TokenStore()
```

- [ ] **Step 2: Run registration scenarios to confirm nothing broke**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 3: Commit**

```bash
git add services/users/src/users/token_store.py
git commit -m "feat(users): add TokenStore"
```

---

### Task 3: Add `AuthError`, `login()`, and `get_profile()` to `service.py`

**Files:**
- Modify: `services/users/src/users/service.py`

- [ ] **Step 1: Add `AuthError` class after `RegistrationError`**

After the `RegistrationError` class definition (line 16), add:

```python
class AuthError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
```

- [ ] **Step 2: Add `login()` function at the end of the file**

```python
def login(
    store: UserStore,
    token_store,
    email: str | None,
    password: str | None,
) -> dict:
    normalised_email = email.strip().lower() if email is not None else ""
    user = store.get(normalised_email)
    if user is None or user["password"] != password:
        raise AuthError("Invalid credentials")
    token = token_store.issue(user["id"])
    return {"token": token}
```

- [ ] **Step 3: Add `get_profile()` function at the end of the file**

```python
def get_profile(
    store: UserStore,
    token_store,
    user_id: str,
    token: str | None,
) -> dict:
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

- [ ] **Step 4: Verify the full file looks correct**

The complete `service.py` should be:

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


class AuthError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
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


def login(
    store: UserStore,
    token_store,
    email: str | None,
    password: str | None,
) -> dict:
    normalised_email = email.strip().lower() if email is not None else ""
    user = store.get(normalised_email)
    if user is None or user["password"] != password:
        raise AuthError("Invalid credentials")
    token = token_store.issue(user["id"])
    return {"token": token}


def get_profile(
    store: UserStore,
    token_store,
    user_id: str,
    token: str | None,
) -> dict:
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

- [ ] **Step 5: Run registration scenarios to confirm nothing broke**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 6: Commit**

```bash
git add services/users/src/users/service.py
git commit -m "feat(users): add AuthError, login and get_profile service functions"
```

---

### Task 4: Update routes — `/login` and new `/users/{user_id}/profile`

**Files:**
- Modify: `services/users/src/users/routes.py`

- [ ] **Step 1: Replace the full file contents**

```python
from __future__ import annotations

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from users.service import AuthError, RegistrationError, get_profile, login, register
from users.store import _store
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
def register_user(body: RegisterRequest) -> dict | JSONResponse:
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

- [ ] **Step 2: Run registration scenarios to confirm nothing broke**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 3: Commit**

```bash
git add services/users/src/users/routes.py
git commit -m "feat(users): update /login to return token, add GET /users/{user_id}/profile"
```

---

### Task 5: Clear `_token_store` in `before_scenario`

**Files:**
- Modify: `shared/src/shared/environment.py`

- [ ] **Step 1: Update the file**

```python
"""Base behave environment hooks: server startup/teardown and state reset."""
from __future__ import annotations

from users.main import app
from users.store import _store
from users.token_store import _token_store

from shared.client import make_client


def before_scenario(context, scenario):
    _store.clear()
    _token_store.clear()
    context.client = make_client(app)
```

- [ ] **Step 2: Run registration scenarios to confirm hooks still work**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 3: Commit**

```bash
git add shared/src/shared/environment.py
git commit -m "feat(users): clear token store between scenarios"
```

---

### Task 6: Write step definitions for `login.feature`

**Files:**
- Create: `services/users/features/steps/login_steps.py`

- [ ] **Step 1: Create the file**

```python
from __future__ import annotations

from behave import given, then, when

_ALICE_EMAIL = "alice@example.com"
_ALICE_PASSWORD = "secret123"
_ALICE_NAME = "Alice"


def _register_alice(context, email: str = _ALICE_EMAIL) -> None:
    context.client.post(
        "/users",
        json={"name": _ALICE_NAME, "email": email, "password": _ALICE_PASSWORD},
    )


@given("Alice has registered an account")
def step_alice_registered(context):
    _register_alice(context)


@given('Alice has registered with "{email}"')
def step_alice_registered_with_email(context, email):
    _register_alice(context, email=email)


@when("Alice logs in with her email and password")
def step_alice_logs_in(context):
    context.response = context.client.post(
        "/login",
        json={"email": _ALICE_EMAIL, "password": _ALICE_PASSWORD},
    )


@then("she receives a token")
def step_she_receives_token(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "token" in body, f"Expected 'token' in response, got: {body}"
    assert body["token"], "Token should be non-empty"
    context.token = body["token"]


@given('no account exists for "{email}"')
def step_no_account_for_email(context, email):
    pass


@when('a visitor tries to log in with "{email}"')
def step_visitor_logs_in_with_email(context, email):
    context.response = context.client.post(
        "/login",
        json={"email": email, "password": "anypassword"},
    )


@then("they are told their credentials are invalid")
def step_credentials_invalid(context):
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "invalid" in body.get("error", "").lower(), (
        f"Expected 'invalid credentials' error, got: {body}"
    )


@when("Alice tries to log in with the wrong password")
def step_alice_logs_in_wrong_password(context):
    context.response = context.client.post(
        "/login",
        json={"email": _ALICE_EMAIL, "password": "wrongpassword"},
    )


@then("she is told her credentials are invalid")
def step_alice_credentials_invalid(context):
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "invalid" in body.get("error", "").lower(), (
        f"Expected 'invalid credentials' error, got: {body}"
    )


@when('she logs in with "{email}"')
def step_she_logs_in_with_email(context, email):
    context.response = context.client.post(
        "/login",
        json={"email": email, "password": _ALICE_PASSWORD},
    )
```

- [ ] **Step 2: Run login scenarios**

```bash
uv run --package users --directory services/users behave features/login.feature
```

Expected: `4 scenarios passed, 0 failed`, zero undefined/pending steps.

- [ ] **Step 3: Run registration scenarios to confirm no step conflicts**

```bash
uv run --package users --directory services/users behave features/registration.feature
```

Expected: `9 scenarios passed, 0 failed`

- [ ] **Step 4: Commit**

```bash
git add services/users/features/steps/login_steps.py
git commit -m "feat(users): add login step definitions"
```

---

### Task 7: Write step definitions for `profile.feature`

**Files:**
- Create: `services/users/features/steps/profile_steps.py`

- [ ] **Step 1: Create the file**

```python
from __future__ import annotations

from behave import given, then, when

_ALICE_EMAIL = "alice@example.com"
_ALICE_PASSWORD = "secret123"
_ALICE_NAME = "Alice"

_BOB_EMAIL = "bob@example.com"
_BOB_PASSWORD = "bobpass1"
_BOB_NAME = "Bob"


def _register_and_login(context, name: str, email: str, password: str) -> tuple[str, str]:
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
def step_alice_registered_and_logged_in(context):
    context.alice_id, context.alice_token = _register_and_login(
        context, _ALICE_NAME, _ALICE_EMAIL, _ALICE_PASSWORD
    )


@when("she requests her profile")
def step_she_requests_profile(context):
    context.response = context.client.get(
        f"/users/{context.alice_id}/profile",
        headers={"Authorization": f"Bearer {context.alice_token}"},
    )


@then("she sees her name and email address")
def step_she_sees_name_and_email(context):
    assert context.response.status_code == 200, (
        f"Expected 200, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert body.get("name") == _ALICE_NAME, f"Expected name '{_ALICE_NAME}', got: {body}"
    assert body.get("email") == _ALICE_EMAIL, f"Expected email '{_ALICE_EMAIL}', got: {body}"


@given("a visitor who has not logged in")
def step_visitor_not_logged_in(context):
    pass


@when("they try to view a profile")
def step_visitor_tries_view_profile(context):
    context.response = context.client.get("/users/some-nonexistent-id/profile")


@then("they are told they must be logged in")
def step_must_be_logged_in(context):
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    error = body.get("error", "").lower()
    assert "authorised" in error or "authorized" in error, (
        f"Expected 'not authorised' error, got: {body}"
    )


@given("Alice and Bob have both registered and logged in")
def step_alice_and_bob_registered_and_logged_in(context):
    context.alice_id, context.alice_token = _register_and_login(
        context, _ALICE_NAME, _ALICE_EMAIL, _ALICE_PASSWORD
    )
    context.bob_id, context.bob_token = _register_and_login(
        context, _BOB_NAME, _BOB_EMAIL, _BOB_PASSWORD
    )


@when("Alice requests Bob's profile")
def step_alice_requests_bob_profile(context):
    context.response = context.client.get(
        f"/users/{context.bob_id}/profile",
        headers={"Authorization": f"Bearer {context.alice_token}"},
    )


@then("she is told she is not authorised")
def step_not_authorised(context):
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    error = body.get("error", "").lower()
    assert "authorised" in error or "authorized" in error, (
        f"Expected 'not authorised' error, got: {body}"
    )
```

- [ ] **Step 2: Run profile scenarios**

```bash
uv run --package users --directory services/users behave features/profile.feature
```

Expected: `3 scenarios passed, 0 failed`, zero undefined/pending steps.

- [ ] **Step 3: Run full suite**

```bash
uv run --package users --directory services/users behave
```

Expected: `16 scenarios passed, 0 failed`, zero undefined/pending/skipped.

- [ ] **Step 4: Commit**

```bash
git add services/users/features/steps/profile_steps.py
git commit -m "feat(users): add profile step definitions"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run the full make bdd target**

```bash
make bdd
```

Expected output includes:
```
16 scenarios passed, 0 failed
```
with no undefined, pending, or skipped steps for the users service. Other services may report "no feature files" — that is expected.

- [ ] **Step 2: Run lint**

```bash
make lint
```

Expected: no errors.
