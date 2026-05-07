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
