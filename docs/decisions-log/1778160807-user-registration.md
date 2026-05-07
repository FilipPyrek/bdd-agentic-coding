# User Registration

- **Date:** 2026-05-07
- **Type:** new

## Context

Adding user registration to the users service. Anyone can self-register with a name, email, and password. No email verification. Login is a separate step after registration.

## Decisions

- Open self-registration (no invites, no admin approval)
- Email + password + name required for registration
- No email verification — conscious simplicity decision; may add later
- Registration does not auto-login; user must log in separately
- Email uniqueness is case-insensitive
- Password length: 6–100 characters
- Name length: 1–100 characters
- Email must look like a valid email address
- Duplicate email produces "Email already in use" (no privacy obfuscation)
- Blank/whitespace-only name produces "Name cannot be blank"
- Missing fields produce field-specific error messages
- Minimum name length reduced from 3 to 1 to accommodate short real names

## Implementation Notes

Decisions that don't warrant their own scenario but must be respected during implementation:

- Email: trim leading/trailing whitespace, then lowercase before validation and storage
- Name: trim leading/trailing whitespace before validation
- Password: never trimmed or modified — store exactly as provided
- Name that is all whitespace after trimming: treat as blank (distinct error "Name cannot be blank", not "Name is required")
- Email duplicate check: compare lowercased versions
- Validation errors: return field-specific messages so the caller knows exactly what's wrong

## Out of Scope

- Email verification / confirmation flow
- Password complexity requirements beyond length (no special char rules)
- Rate limiting on registration attempts
- CAPTCHA or bot protection

## Affected Scenarios

- `services/users/features/registration.feature` (created)
