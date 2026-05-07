# User Registration — Implementation Design

- **Date:** 2026-05-07
- **Decision log:** docs/decisions-log/1778160807-user-registration.md
- **Feature file:** services/users/features/registration.feature

---

## Overview

Implement user registration for the users service. Scenarios are verified via
httpx TestClient (ASGI, in-process HTTP). No external server is started. State is
in-memory and reset between scenarios via behave hooks.

---

## Architecture

### File layout

```
services/users/src/users/
├── __init__.py          # empty
├── store.py             # UserStore: in-memory dict, clearable
├── service.py           # register(): validation + delegates to store
├── routes.py            # FastAPI APIRouter with POST /users and POST /login (stub)
└── main.py              # FastAPI app assembly

shared/src/shared/
├── client.py            # make_client(app) → TestClient factory
└── environment.py       # before_scenario hook: reset store + attach client

services/users/features/steps/
└── registration_steps.py
```

### Data flow

```
TestClient (step) → POST /users (routes.py) → service.register() → store.add()
                                                      ↓
                                              validate inputs
                                              → raise RegistrationError on failure
```

---

## Components

### `store.py` — UserStore

A `UserStore` class wraps a `dict[str, dict]` keyed by lowercased email.

| Method | Description |
|---|---|
| `add(user: dict) → None` | Stores user dict; key = lowercased email |
| `exists(email: str) → bool` | Case-insensitive lookup |
| `get(email: str) → dict \| None` | Retrieve stored user by email |
| `clear() → None` | Empty the store (used by test hooks) |

Module-level singleton: `_store = UserStore()`.

### `service.py` — Business logic

```python
def register(store: UserStore, name: str | None, email: str | None, password: str | None) -> dict
```

1. Normalise: strip `name`, strip+lowercase `email`, leave `password` unchanged
2. Validate fields in order (first failure raises `RegistrationError`)
3. On success: generate UUID, store user (without password), return `{id, name, email}`

`RegistrationError(field: str, message: str)` — raised for all validation failures.

### `routes.py` — HTTP layer

**`POST /users`**
- Request body: `{name: str, email: str, password: str}` (Pydantic model)
- Success: `201 Created` with `{id, name, email}`
- `RegistrationError`: `422 Unprocessable Entity` with `{field: str, error: str}`
- Missing Pydantic fields: FastAPI's native 422 with field-level detail

**`POST /login`** (stub for "can log in" scenario step)
- Request body: `{email: str, password: str}`
- Looks up stored user; returns `200` if credentials match, `401` otherwise
- Password comparison is against the raw stored password (plain text acceptable for stub)

### `main.py`

Creates `FastAPI()`, includes the router from `routes.py`. No middleware.

---

## Shared package

### `shared/client.py`

```python
def make_client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
```

### `shared/environment.py`

```python
from users.store import _store
from users.main import app
from shared.client import make_client

def before_scenario(context, scenario):
    _store.clear()
    context.client = make_client(app)
```

---

## Validation rules

Input normalisation applied before validation:

| Field | Normalisation |
|---|---|
| `name` | strip whitespace |
| `email` | strip whitespace, then lowercase |
| `password` | none |

Validation order and error messages (first failure wins):

| Field | Condition | Error message |
|---|---|---|
| `name` | missing/None | `"Name is required"` |
| `name` | blank after strip | `"Name cannot be blank"` |
| `name` | len > 100 | `"Name is too long"` |
| `email` | missing/None | `"Email is required"` |
| `email` | invalid format | `"Invalid email address"` |
| `email` | already in use (case-insensitive) | `"Email already in use"` |
| `password` | missing/None | `"Password is required"` |
| `password` | len < 6 | `"Password is too short"` |
| `password` | len > 100 | `"Password is too long"` |

---

## Error response shape

Single-field error (from service layer):

```json
{ "field": "email", "error": "Email already in use" }
```

Missing-field error (FastAPI native 422):

```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "missing" }
  ]
}
```

Step definitions parse the native 422 detail list to assert which fields are reported missing.

---

## Step file: `registration_steps.py`

State held on `context` between steps:

| Attribute | Purpose |
|---|---|
| `context.client` | httpx TestClient (set in environment hook) |
| `context.response` | Last HTTP response |
| `context.registered_name` | Name used in current scenario |
| `context.registered_email` | Email used in current scenario |
| `context.registered_password` | Password used in current scenario |

Steps translate business-level Gherkin into `POST /users` calls. No HTTP status
codes or JSON structure appear in the feature file. Assertions check business
outcomes: account created, error message visible.

---

## Out of scope

- Full login/auth implementation (login stub only)
- Email verification
- Password hashing
- Rate limiting / CAPTCHA
- Persistence across restarts
