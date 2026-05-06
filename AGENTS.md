# AGENTS.md

## Repo overview

Python BDD experiment using `behave`. Monorepo with `uv` workspaces. Multiple stub
services simulate a realistic multi-service system. Each service owns its own BDD
scenarios. `e2e/` owns cross-service scenarios.

## Repository structure

```
bdd-experiment/
├── pyproject.toml          # workspace root
├── Makefile                # top-level targets
├── services/
│   ├── users/
│   ├── orders/
│   └── inventory/
├── e2e/
└── shared/                 # path dep imported by services and e2e
```

## Setup

```bash
uv sync --all-packages
```

## Commands

| Task | Command |
|---|---|
| Run all BDD scenarios | `make bdd` |
| Run e2e scenarios only | `make bdd-e2e` |
| Run single service | `uv run --package users behave` |
| Run single feature file | `uv run --package users behave features/registration.feature` |
| Run by tag | `uv run --package users behave --tags=@tag_name` |
| Lint | `make lint` |
| Format | `make format` |
| Typecheck | `make typecheck` |

## BDD conventions

### Scenarios express business requirements

Feature files describe what the system does from a user/product perspective.
No HTTP status codes, no JSON, no implementation detail in Gherkin.

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

Step implementations use `shared.client` internally. Transport details are invisible
to `.feature` files. If transport changes, Gherkin stays the same.

### Tag policy

No tags by default. Add a tag only when there is a concrete filtering need (e.g. a CI
stage that runs a subset, or a feature area needing targeted runs). Never tag by
implementation style (`@unit`, `@http`, etc.).

### Step file organisation

One step file per feature area, named to match the feature file:

```
features/steps/
├── registration_steps.py
└── environment.py          # behave hooks: before_scenario, after_scenario
```

## Adding a new service

1. Create `services/<name>/` with the same structure as `services/users/`
2. Add `"services/<name>"` to `[tool.uv.workspace] members` in root `pyproject.toml`
3. Run `uv sync --all-packages`
4. Add `uv run --package <name> behave` to root `Makefile` `bdd` target
5. Write `AGENTS.md` for the new service

## Notes

- Do not use `pip` or `python -m venv` — always use `uv`
- Check `pyproject.toml` for configured test paths, markers, and plugin settings
