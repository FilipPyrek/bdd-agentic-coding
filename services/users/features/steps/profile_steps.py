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
