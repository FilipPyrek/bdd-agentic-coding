Feature: User registration

  Anyone can create an account by providing their name, email address,
  and a password. No email verification is required. After registering,
  the visitor must log in separately.

  Scenario: Successful registration
    Given a visitor with a valid name, email, and password
    When they register
    Then their account is created
    And they can log in with their email and password

  Scenario: Duplicate email is rejected
    Given a user has already registered with "alice@example.com"
    When a visitor tries to register with "alice@example.com"
    Then they see an error: "Email already in use"

  Scenario: Password too short is rejected
    Given a visitor with a password shorter than 6 characters
    When they try to register
    Then they see an error that the password is too short

  Scenario: Password too long is rejected
    Given a visitor with a password longer than 100 characters
    When they try to register
    Then they see an error that the password is too long

  Scenario: Invalid email format is rejected
    Given a visitor with an invalid email address
    When they try to register
    Then they see an error that the email is invalid

  Scenario: Name too long is rejected
    Given a visitor with a name longer than 100 characters
    When they try to register
    Then they see an error that the name is too long

  Scenario: Blank name is rejected
    Given a visitor with a blank name
    When they try to register
    Then they see an error: "Name cannot be blank"

  Scenario: Missing required fields are rejected
    Given a visitor without all required fields
    When they try to register
    Then they see errors indicating which fields are missing

  Scenario: Email uniqueness is case-insensitive
    Given a user has already registered with "alice@example.com"
    When a visitor tries to register with "Alice@Example.com"
    Then they see an error: "Email already in use"
