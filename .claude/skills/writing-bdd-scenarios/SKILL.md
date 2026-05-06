---
name: writing-bdd-scenarios
description: Use when writing Gherkin feature files or BDD scenarios — before authoring any .feature file content
---

# Writing BDD Scenarios

## Overview

Gherkin is a requirements format, not a test script. Every scenario must be readable
and validatable by a non-technical stakeholder. Implementation details belong in step
definitions, not in feature files.

## Core Rules

### 1. Scenarios express business requirements

No HTTP status codes, no JSON, no endpoint paths, no field names. A product manager
must be able to read every line without technical knowledge.

**Good:**
```gherkin
Scenario: User cannot register twice with the same email
  Given Alice has already registered
  When Alice tries to register again
  Then she sees an error: "Email already in use"
```

**Avoid:**
```gherkin
Scenario: Duplicate registration returns 409
  When I POST to "/users" with body {"email": "alice@example.com"}
  Then the response status is 409
```

### 2. Given / When / Then intent

| Keyword | Intent |
|---------|--------|
| `Given` | Context — the world state before the action |
| `When` | Action — the single thing the actor does |
| `Then` | Outcome — what the actor observes as a result |
| `And` / `But` | Continuation of the preceding keyword's intent |

Use named actors (`Alice`, `Bob`) rather than anonymous `I` or `the user`. It makes
scenarios concrete and easier to follow in multi-actor flows.

### 3. Naming features and scenarios

- **Feature:** noun phrase describing the capability — `User Registration`, `Order Placement`
- **Scenario:** full sentence starting with the business outcome or actor action —
  `User cannot register twice with the same email`
- Avoid technical framing: not `POST /users returns 201`, not `DB stores record`

### 4. Tag policy

No tags by default. Add a tag only when there is a concrete filtering need:
- A CI stage that runs a subset of scenarios
- A feature area that needs targeted local runs

Never tag by implementation style: `@unit`, `@http`, `@integration`, `@slow` are all
wrong. Tags are for filtering, not for labelling.

### 5. Step definitions own the technical layer

The `.feature` file knows nothing about HTTP, JSON, databases, or internal APIs.
Step definitions call `shared.client` internally. If the transport changes, the
Gherkin stays the same.

## Quick Reference

| ✅ Write this | ❌ Not this |
|---|---|
| `Then her order is confirmed` | `Then the response status is 201` |
| `Given Alice is a registered user` | `Given a user exists with email alice@example.com` |
| `When Alice places an order for 2 "Widget Pro"` | `When I POST /orders with {"sku":"widget-pro","qty":2}` |
| `Then she sees an error: "Email already in use"` | `Then the JSON body contains {"error":"duplicate_email"}` |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| HTTP verbs in Gherkin | Move to step definition |
| Status codes in `Then` | Describe the observable outcome instead |
| JSON / field names in steps | Use business language |
| Tags for implementation style | Remove the tag; only add tags when filtering is needed |
| Vague actors (`the user`) | Use named actors (`Alice`) |
