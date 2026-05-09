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
