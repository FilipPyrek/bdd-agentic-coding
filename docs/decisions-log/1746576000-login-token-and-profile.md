# Login Token and Profile Access

- **Date:** 2026-05-07
- **Type:** modification + new

## Context

The users service had a working login endpoint but returned no token. This session added
token issuance on login and a protected profile endpoint gated by that token.

## Decisions

- Login returns a token on success — enables access to protected endpoints without re-authenticating.
- Profile access is scoped to the authenticated user — a user can only view their own profile, not another user's.
- Token format is a UUID — consistent with how user IDs are already generated in this service.
- A request for a non-existent user ID returns "not authorised" rather than "not found" — avoids leaking whether an ID exists.

## Implementation Notes

- Token is a UUID generated at login time and stored in memory alongside the user record.
- Email comparison at login is case-insensitive (already normalised on registration; same normalisation applies at login).
- The profile endpoint requires both a valid token and a matching user ID; mismatched token/ID is treated identically to no token.

## Out of Scope

- Token expiry — tokens do not expire in this primitive implementation.
- Invalid/malformed token distinction — no scenario distinguishing a garbage token from a missing token.

## Affected Scenarios

- `services/users/features/registration.feature` — updated last step of "Successful registration"
- `services/users/features/login.feature` — new file
- `services/users/features/profile.feature` — new file
