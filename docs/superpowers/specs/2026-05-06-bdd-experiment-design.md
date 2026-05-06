# BDD Experiment — Design Spec

**Date:** 2026-05-06

## Purpose

Test whether using BDD (Gherkin) as the primary requirements format is more valuable than prose-based spec-driven development when working with AI agents. The hypothesis: Gherkin is executable, so AI agents get direct feedback from running scenarios, while humans can read and validate requirements written in plain language.

## Approach

Monorepo using `uv` workspaces. Multiple stub services simulate a realistic multi-service system at the scale of ~80 engineers. Each service owns its own BDD scenarios. A top-level `e2e` package owns cross-service scenarios.

## Repository Structure

```
bdd-experiment/
├── pyproject.toml              # workspace root — declares all members
├── Makefile                    # top-level: bdd, bdd-e2e, lint, format, typecheck, setup
├── AGENTS.md                   # repo-wide conventions
│
├── services/
│   ├── users/                  # uv workspace member
│   │   ├── pyproject.toml
│   │   ├── AGENTS.md
│   │   ├── Makefile
│   │   ├── src/users/          # FastAPI app (in-memory, no database)
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── routers/
│   │   │       └── users.py
│   │   └── features/
│   │       ├── registration.feature
│   │       └── steps/
│   │           ├── registration_steps.py
│   │           └── environment.py
│   │
│   ├── orders/                 # uv workspace member
│   │   ├── pyproject.toml
│   │   ├── AGENTS.md
│   │   ├── Makefile
│   │   ├── src/orders/
│   │   └── features/
│   │
│   └── inventory/              # uv workspace member (stub)
│       ├── pyproject.toml
│       ├── AGENTS.md
│       ├── Makefile
│       ├── src/inventory/
│       └── features/
│
├── e2e/                        # uv workspace member
│   ├── pyproject.toml
│   ├── Makefile
│   └── features/
│       ├── place_order.feature
│       └── steps/
│           ├── place_order_steps.py
│           └── environment.py
│
└── shared/                     # uv workspace member — imported by services + e2e
    ├── pyproject.toml
    └── src/shared/
        ├── __init__.py
        ├── client.py           # httpx-based test client helpers
        └── environment.py      # base behave environment hooks (server startup/teardown, state reset)
```

## Scope

Set up the repo structure, tooling, and documentation. No application code, no step definitions, no `.feature` files. At the end of this phase the repo compiles, `uv sync --all-packages` works, and CI is green (nothing to run yet).

Deliverables: `pyproject.toml` (workspace + all members), `Makefile` (root + per-service), `.github/workflows/bdd.yml`, `shared` package skeleton, `AGENTS.md` files, `writing-bdd-scenarios` skill.

Writing Gherkin scenarios and implementing the services are separate efforts, each with their own spec and plan.

## Tooling

- **Package manager:** `uv` — no `pip`, no `venv` directly
- **BDD framework:** `behave`
- **Web framework:** FastAPI with uvicorn
- **HTTP test client:** `httpx` (via `starlette.testclient` or `httpx.TestClient`)
- **Lint/format:** `ruff`
- **Typecheck:** `mypy` (strict)

## Dependency Layout

Root `pyproject.toml` declares the workspace and dev tooling:

```toml
[tool.uv.workspace]
members = ["services/*", "e2e", "shared"]

[tool.uv]
dev-dependencies = ["ruff", "mypy"]

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
strict = true
```

Each service `pyproject.toml` declares its own runtime and test deps:

```toml
[project]
name = "users"
dependencies = ["fastapi", "uvicorn[standard]"]

[project.optional-dependencies]
test = ["behave", "httpx", "shared"]

[tool.behave]
paths = ["features"]
```

`shared` is resolved as a workspace-local path dependency — no publishing required.

## BDD Conventions

### Scenarios express business requirements

Feature files describe what the system does from a user/product perspective. No HTTP status codes, no JSON, no implementation detail in Gherkin. A non-technical stakeholder should be able to read and validate every scenario.

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

### Step definitions own the technical layer

Step implementations use `shared.client` to call the service via HTTP internally. This is invisible to the `.feature` file. If the transport mechanism changes, the Gherkin stays the same.

### Tag policy

No tags by default. Add a tag only when there is a concrete filtering need (e.g. a CI stage that runs a subset, or a feature area that needs targeted runs). Never use tags to indicate test implementation style (`@unit`, `@http` etc.).

### Step file organisation

One step file per feature area, named to match the feature file:

```
features/steps/
├── registration_steps.py
└── environment.py          # behave hooks: before_scenario, after_scenario
```

## Sample Domain

Three services model a simple e-commerce order flow:

- **users** — register and authenticate users
- **orders** — place and view orders
- **inventory** — track stock levels

All services use in-memory state (no database). 2-3 scenarios per service is sufficient to demonstrate conventions.

Example cross-service E2E scenario:

```gherkin
Feature: Placing an order

  Scenario: Registered user places an order for an in-stock item
    Given Alice is a registered user
    And "Widget Pro" has 10 units in stock
    When Alice places an order for 2 "Widget Pro"
    Then her order is confirmed
    And "Widget Pro" has 8 units in stock
```

## Automation

### Root Makefile

```makefile
bdd:
	uv run --package users behave
	uv run --package orders behave
	uv run --package inventory behave
	uv run --package e2e behave

bdd-e2e:
	uv run --package e2e behave

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

setup:
	uv sync --all-packages
```

### Per-service Makefile

```makefile
bdd:
	uv run --package <name> behave

run:
	uv run --package <name> uvicorn <name>.main:app --reload

lint:
	uv run ruff check .
```

### CI — GitHub Actions

```yaml
# .github/workflows/bdd.yml
on: [push, pull_request]

jobs:
  bdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-packages
      - run: make bdd
      - run: make lint
      - run: make typecheck
```

CI runs all tests on every push and pull request. No smoke subsets, no skipping.

## Documentation

- **Root `AGENTS.md`** — repo structure, workspace commands, BDD conventions, tag policy, how to add a new service
- **Per-service `AGENTS.md`** — what the service does, `make run`, `make bdd`, service-specific conventions
- Specs live in `docs/superpowers/specs/`

## writing-bdd-scenarios Skill

Create a `writing-bdd-scenarios` skill that codifies the BDD conventions from this spec. Its purpose: give AI agents clear rules for writing Gherkin correctly so they don't drift toward technical-style scenarios.

The skill should cover:
- Scenarios express business requirements — no HTTP status codes, no JSON, no implementation detail
- Proper Given/When/Then structure and intent (Given = context, When = action, Then = outcome)
- How to name features and scenarios
- Tag policy: no tags by default, add only for concrete filtering needs
- Examples of good and bad scenarios (drawn from this spec)

**When implementing:** invoke the `writing-skills` skill before writing this skill — it provides best practices for authoring skills that AI agents follow reliably.

## Adding a New Service

1. Create `services/<name>/` with the same structure as `services/users/`
2. Add `"services/<name>"` to `[tool.uv.workspace] members` in root `pyproject.toml`
3. Run `uv sync --all-packages`
4. Add `uv run --package <name> behave` to root `Makefile` `bdd` target
5. Write `AGENTS.md` for the new service
