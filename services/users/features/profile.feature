Feature: View own profile

  A logged-in user can view their own account details.
  Access requires a valid token, and a user can only view their own profile —
  not another user's.

  Scenario: Logged-in user views their own profile
    Given Alice has registered and logged in
    When she requests her profile
    Then she sees her name and email address

  Scenario: Request without a token is rejected
    Given a visitor who has not logged in
    When they try to view a profile
    Then they are told they must be logged in

  Scenario: A user cannot view another user's profile
    Given Alice and Bob have both registered and logged in
    When Alice requests Bob's profile
    Then she is told she is not authorised
