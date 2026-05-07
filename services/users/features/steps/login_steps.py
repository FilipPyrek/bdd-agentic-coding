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


def _assert_invalid_credentials(context) -> None:
    assert context.response.status_code == 401, (
        f"Expected 401, got {context.response.status_code}: {context.response.text}"
    )
    body = context.response.json()
    assert "invalid" in body.get("error", "").lower(), (
        f"Expected 'invalid credentials' error, got: {body}"
    )


@then("they are told their credentials are invalid")
def step_credentials_invalid(context):
    _assert_invalid_credentials(context)


@when("Alice tries to log in with the wrong password")
def step_alice_logs_in_wrong_password(context):
    context.response = context.client.post(
        "/login",
        json={"email": _ALICE_EMAIL, "password": "wrongpassword"},
    )


@then("she is told her credentials are invalid")
def step_alice_credentials_invalid(context):
    _assert_invalid_credentials(context)


@when('she logs in with "{email}"')
def step_she_logs_in_with_email(context, email):
    context.response = context.client.post(
        "/login",
        json={"email": email, "password": _ALICE_PASSWORD},
    )
