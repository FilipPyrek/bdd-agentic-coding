Feature: User login

  Registered users authenticate with their email and password.
  A successful login returns a token that can be used to access
  protected parts of the service.

  Scenario: Registered user receives a token on login
    Given Alice has registered an account
    When Alice logs in with her email and password
    Then she receives a token

  Scenario: Unregistered email is rejected
    Given no account exists for "unknown@example.com"
    When a visitor tries to log in with "unknown@example.com"
    Then they are told their credentials are invalid

  Scenario: Wrong password is rejected
    Given Alice has registered an account
    When Alice tries to log in with the wrong password
    Then she is told her credentials are invalid

  Scenario: Login is case-insensitive for email
    Given Alice has registered with "Alice@Example.com"
    When she logs in with "alice@example.com"
    Then she receives a token
