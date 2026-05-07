# Design: Login Token and Profile Access

- **Date:** 2026-05-07
- **Decision log:** `docs/decisions-log/1746576000-login-token-and-profile.md`
- **Scenarios:**
  - `services/users/features/registration.feature`
  - `services/users/features/login.feature`
  - `services/users/features/profile.feature`

## Overview

Extend the users service so that:
1. A successful login returns a UUID token.
2. A new profile endpoint returns the authenticated user's own profile.
3. A user cannot view another user's profile.

All state is in-memory; no persistence. Tokens do not expire.

---

## Section 1: Data layer

### `src/users/store.py` (existing — minimal change)

Add one method:

```
get_by_id(user_id: str) -> dict | None
```

Returns the user dict for the given ID, or `None`. Internally iterates `_users.values()` since the dict is keyed by email.

Everything else in `UserStore` is unchanged.

### `src/users/token_store.py` (new file)

```
class TokenStore:
    _tokens: dict[str, str]   # token -> user_id

    def issue(user_id: str) -> str
        # generates uuid4 token, stores mapping, returns token

    def get_user_id(token: str) -> str | None
        # returns user_id for token, or None

    def clear() -> None

_token_store = TokenStore()  # module-level singleton
```

### `shared/src/shared/environment.py` (existing — add clear)

Import `_token_store` from `users.token_store` and call `_token_store.clear()` in `before_scenario`, alongside the existing `_store.clear()`.

---

## Section 2: Service layer (`src/users/service.py`)

### New exception

```
class AuthError(Exception):
    def __init__(self, message: str) -> None
```

### `login(store, token_store, email, password) -> dict`

1. Normalise email: `.strip().lower()`
2. Look up user by email via `store.get(email)`; if `None` or `user["password"] != password` → raise `AuthError("Invalid credentials")`
3. Call `token_store.issue(user["id"])` → get token
4. Return `{"token": token}`

### `get_profile(store, token_store, user_id, token) -> dict`

1. `resolved_id = token_store.get_user_id(token)`; if `None` → raise `AuthError("Not authorised")`
2. If `resolved_id != user_id` → raise `AuthError("Not authorised")`
3. `user = store.get_by_id(user_id)`; if `None` → raise `AuthError("Not authorised")`
4. Return `{"id": user["id"], "name": user["name"], "email": user["email"]}`

All three auth failure paths produce the same error message to avoid information leakage.

---

## Section 3: Route layer (`src/users/routes.py`)

### `POST /login` (update existing)

- Request: `LoginRequest(email: str, password: str)` — unchanged
- Call `login(_store, _token_store, email, password)`
- Success 200: `{"token": "..."}`
- `AuthError` → 401: `{"error": "Invalid credentials"}`
- Import `_token_store` from `users.token_store`

### `GET /users/{user_id}/profile` (new endpoint)

- Extract `Authorization` header; parse `Bearer <token>`; if missing or malformed → 401 `{"error": "Not authorised"}`
- Call `get_profile(_store, _token_store, user_id, token)`
- Success 200: `{"id": ..., "name": ..., "email": ...}`
- `AuthError` → 401: `{"error": "Not authorised"}`

Token is transported as a standard `Authorization: Bearer` header. This detail is hidden from Gherkin — step definitions handle the header construction.

---

## Section 4: Step definitions

### `features/steps/login_steps.py` (new file)

Covers all four scenarios in `login.feature`:

| Scenario | Given | When | Then |
|---|---|---|---|
| Receives token | Register Alice via `context.client.post("/users", ...)` | POST `/login` with correct credentials | Response has `"token"` key; store as `context.token` |
| Unregistered email | No setup | POST `/login` with unknown email | "credentials are invalid" in error message |
| Wrong password | Register Alice | POST `/login` with wrong password | "credentials are invalid" in error message |
| Case-insensitive email | Register with "Alice@Example.com" | POST `/login` with "alice@example.com" | Response has `"token"` key |

Shared given step "Alice has registered an account" registers Alice with fixed credentials. Step "Alice has registered with X" registers Alice with a caller-supplied email.

### `features/steps/profile_steps.py` (new file)

Covers all three scenarios in `profile.feature`:

| Scenario | Given | When | Then |
|---|---|---|---|
| Views own profile | Register + login Alice; store `context.alice_id`, `context.alice_token` | GET `/users/{alice_id}/profile` with `Authorization: Bearer {alice_token}` | Response contains Alice's name and email |
| No token | No login | GET `/users/any-id/profile` (no auth header) | "must be logged in" in error |
| Cross-user | Register + login Alice; register + login Bob; store both IDs and tokens | Alice GETs `/users/{bob_id}/profile` with `alice_token` | "not authorised" in error |

---

## Verification

After implementation, run:

```
uv run --package users --directory services/users behave
```

All 16 scenarios (9 registration + 4 login + 3 profile) must pass with:
- Exit code 0
- Zero undefined steps
- Zero pending steps
- Zero skipped scenarios
