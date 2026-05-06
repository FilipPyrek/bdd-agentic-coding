# BDD Experiment Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the monorepo structure, tooling, and documentation so `uv sync --all-packages` works and CI is green — no application code, no step definitions, no `.feature` files yet.

**Architecture:** `uv` workspace with root `pyproject.toml` declaring members `services/*`, `e2e`, and `shared`. Each member is an independent package. `shared` is a path dependency consumed by services and `e2e` via `[project.optional-dependencies]`.

**Tech Stack:** Python, uv (workspace), behave, FastAPI, uvicorn, httpx, ruff, mypy (strict)

---

## File Map

### Created

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Workspace root — declares members, dev tooling (ruff, mypy) |
| `Makefile` | Root targets: bdd, bdd-e2e, lint, format, typecheck, setup |
| `.github/workflows/bdd.yml` | CI: checkout → uv sync → make bdd → lint → typecheck |
| `shared/pyproject.toml` | `shared` package metadata; no runtime deps |
| `shared/src/shared/__init__.py` | Empty package marker |
| `shared/src/shared/client.py` | Stub: httpx test client helpers (empty public API) |
| `shared/src/shared/environment.py` | Stub: base behave environment hooks (empty) |
| `services/users/pyproject.toml` | `users` package; deps: fastapi, uvicorn; test extras: behave, httpx, shared |
| `services/users/Makefile` | Per-service targets: bdd, run, lint |
| `services/users/AGENTS.md` | What users service does, make commands, service conventions |
| `services/users/src/users/__init__.py` | Empty package marker |
| `services/orders/pyproject.toml` | `orders` package; same dep shape as users |
| `services/orders/Makefile` | Per-service targets |
| `services/orders/AGENTS.md` | What orders service does |
| `services/orders/src/orders/__init__.py` | Empty package marker |
| `services/inventory/pyproject.toml` | `inventory` package; same dep shape |
| `services/inventory/Makefile` | Per-service targets |
| `services/inventory/AGENTS.md` | What inventory service does |
| `services/inventory/src/inventory/__init__.py` | Empty package marker |
| `e2e/pyproject.toml` | `e2e` package; deps: behave, httpx, shared, fastapi, uvicorn |
| `e2e/Makefile` | Per-service targets |
| `~/.claude/skills/writing-bdd-scenarios/SKILL.md` | Skill codifying BDD conventions for AI agents |

### Modified

| File | Change |
|------|--------|
| `AGENTS.md` | Replace stub content with full repo conventions |

---

## Task 1: Root `pyproject.toml` and workspace declaration

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "bdd-experiment"
version = "0.1.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["services/*", "e2e", "shared"]

[dependency-groups]
dev = ["ruff", "mypy"]

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.mypy]
strict = true
```

- [ ] **Step 2: Verify uv recognises the workspace**

```bash
uv sync --all-packages
```

Expected: resolves without error. Lock file written. No packages installed yet because members don't exist — uv will error on missing members. That's expected; we'll fix it in subsequent tasks.

> **Note:** If uv errors on missing members, that is expected. Continue to Task 2.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add workspace root pyproject.toml"
```

---

## Task 2: `shared` package skeleton

**Files:**
- Create: `shared/pyproject.toml`
- Create: `shared/src/shared/__init__.py`
- Create: `shared/src/shared/client.py`
- Create: `shared/src/shared/environment.py`

- [ ] **Step 1: Write `shared/pyproject.toml`**

```toml
[project]
name = "shared"
version = "0.1.0"
requires-python = ">=3.12"
```

- [ ] **Step 2: Write `shared/src/shared/__init__.py`**

```python
```

(empty file)

- [ ] **Step 3: Write `shared/src/shared/client.py`**

```python
"""httpx-based test client helpers for BDD step definitions."""
```

- [ ] **Step 4: Write `shared/src/shared/environment.py`**

```python
"""Base behave environment hooks: server startup/teardown and state reset."""
```

- [ ] **Step 5: Verify uv picks up `shared`**

```bash
uv sync --all-packages
```

Expected: resolves without error (other members still missing — still expected).

- [ ] **Step 6: Commit**

```bash
git add shared/
git commit -m "chore: add shared package skeleton"
```

---

## Task 3: `users` service skeleton

**Files:**
- Create: `services/users/pyproject.toml`
- Create: `services/users/Makefile`
- Create: `services/users/AGENTS.md`
- Create: `services/users/src/users/__init__.py`

- [ ] **Step 1: Write `services/users/pyproject.toml`**

```toml
[project]
name = "users"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi", "uvicorn[standard]"]

[project.optional-dependencies]
test = ["behave", "httpx", "shared"]

[tool.uv.sources]
shared = { workspace = true }

[tool.behave]
paths = ["features"]
```

- [ ] **Step 2: Write `services/users/Makefile`**

```makefile
bdd:
	uv run --package users behave

run:
	uv run --package users uvicorn users.main:app --reload

lint:
	uv run ruff check .
```

> **Important:** Makefile indentation MUST use tabs, not spaces.

- [ ] **Step 3: Write `services/users/AGENTS.md`**

```markdown
# users service

Manages user registration and authentication. In-memory state only — no database.

## Commands

| Task | Command |
|------|---------|
| Run BDD scenarios | `make bdd` |
| Start dev server | `make run` |
| Lint | `make lint` |

## Service conventions

- All state lives in a module-level dict; reset between scenarios via `environment.py` hooks
- No database, no persistence across restarts
- Feature files live in `features/`; step files in `features/steps/`
- One step file per feature area, named to match the feature file
```

- [ ] **Step 4: Write `services/users/src/users/__init__.py`**

```python
```

(empty file)

- [ ] **Step 5: Commit**

```bash
git add services/users/
git commit -m "chore: add users service skeleton"
```

---

## Task 4: `orders` service skeleton

**Files:**
- Create: `services/orders/pyproject.toml`
- Create: `services/orders/Makefile`
- Create: `services/orders/AGENTS.md`
- Create: `services/orders/src/orders/__init__.py`

- [ ] **Step 1: Write `services/orders/pyproject.toml`**

```toml
[project]
name = "orders"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi", "uvicorn[standard]"]

[project.optional-dependencies]
test = ["behave", "httpx", "shared"]

[tool.uv.sources]
shared = { workspace = true }

[tool.behave]
paths = ["features"]
```

- [ ] **Step 2: Write `services/orders/Makefile`**

```makefile
bdd:
	uv run --package orders behave

run:
	uv run --package orders uvicorn orders.main:app --reload

lint:
	uv run ruff check .
```

- [ ] **Step 3: Write `services/orders/AGENTS.md`**

```markdown
# orders service

Manages order placement and order history. In-memory state only — no database.

## Commands

| Task | Command |
|------|---------|
| Run BDD scenarios | `make bdd` |
| Start dev server | `make run` |
| Lint | `make lint` |

## Service conventions

- All state lives in a module-level dict; reset between scenarios via `environment.py` hooks
- No database, no persistence across restarts
- Feature files live in `features/`; step files in `features/steps/`
- One step file per feature area, named to match the feature file
```

- [ ] **Step 4: Write `services/orders/src/orders/__init__.py`**

```python
```

(empty file)

- [ ] **Step 5: Commit**

```bash
git add services/orders/
git commit -m "chore: add orders service skeleton"
```

---

## Task 5: `inventory` service skeleton

**Files:**
- Create: `services/inventory/pyproject.toml`
- Create: `services/inventory/Makefile`
- Create: `services/inventory/AGENTS.md`
- Create: `services/inventory/src/inventory/__init__.py`

- [ ] **Step 1: Write `services/inventory/pyproject.toml`**

```toml
[project]
name = "inventory"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi", "uvicorn[standard]"]

[project.optional-dependencies]
test = ["behave", "httpx", "shared"]

[tool.uv.sources]
shared = { workspace = true }

[tool.behave]
paths = ["features"]
```

- [ ] **Step 2: Write `services/inventory/Makefile`**

```makefile
bdd:
	uv run --package inventory behave

run:
	uv run --package inventory uvicorn inventory.main:app --reload

lint:
	uv run ruff check .
```

- [ ] **Step 3: Write `services/inventory/AGENTS.md`**

```markdown
# inventory service

Tracks stock levels for products. In-memory state only — no database.

## Commands

| Task | Command |
|------|---------|
| Run BDD scenarios | `make bdd` |
| Start dev server | `make run` |
| Lint | `make lint` |

## Service conventions

- All state lives in a module-level dict; reset between scenarios via `environment.py` hooks
- No database, no persistence across restarts
- Feature files live in `features/`; step files in `features/steps/`
- One step file per feature area, named to match the feature file
```

- [ ] **Step 4: Write `services/inventory/src/inventory/__init__.py`**

```python
```

(empty file)

- [ ] **Step 5: Commit**

```bash
git add services/inventory/
git commit -m "chore: add inventory service skeleton"
```

---

## Task 6: `e2e` package skeleton

**Files:**
- Create: `e2e/pyproject.toml`
- Create: `e2e/Makefile`

- [ ] **Step 1: Write `e2e/pyproject.toml`**

```toml
[project]
name = "e2e"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi", "uvicorn[standard]", "behave", "httpx", "shared"]

[tool.uv.sources]
shared = { workspace = true }

[tool.behave]
paths = ["features"]
```

- [ ] **Step 2: Write `e2e/Makefile`**

```makefile
bdd:
	uv run --package e2e behave

lint:
	uv run ruff check .
```

- [ ] **Step 3: Commit**

```bash
git add e2e/
git commit -m "chore: add e2e package skeleton"
```

---

## Task 7: Root `Makefile`

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Write `Makefile`**

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

> **Important:** Makefile indentation MUST use tabs, not spaces.

- [ ] **Step 2: Verify `uv sync --all-packages` succeeds end-to-end**

```bash
uv sync --all-packages
```

Expected: all five workspace members resolve cleanly, lock file written.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add root Makefile"
```

---

## Task 8: GitHub Actions CI

**Files:**
- Create: `.github/workflows/bdd.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Write `.github/workflows/bdd.yml`**

```yaml
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

- [ ] **Step 3: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflow"
```

---

## Task 9: Update root `AGENTS.md`

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Replace the stub `AGENTS.md` with full repo conventions**

Write the following content to `AGENTS.md`:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update root AGENTS.md with full repo conventions"
```

---

## Task 10: `writing-bdd-scenarios` skill

**Files:**
- Create: `~/.claude/skills/writing-bdd-scenarios/SKILL.md`

> **Before writing:** The spec says to invoke the `writing-skills` skill. In this plan you are executing steps mechanically, so follow the SKILL.md content below directly. The content is derived from the BDD conventions in the spec.

- [ ] **Step 1: Create the skill directory**

```bash
mkdir -p ~/.claude/skills/writing-bdd-scenarios
```

- [ ] **Step 2: Write `~/.claude/skills/writing-bdd-scenarios/SKILL.md`**

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add ~/.claude/skills/writing-bdd-scenarios/
git commit -m "docs: add writing-bdd-scenarios skill"
```

> **Note:** If `~/.claude/skills/` is outside the repo, skip the git commit for this file. The skill lives in the agent's personal skills directory.

---

## Task 11: Final verification

- [ ] **Step 1: Run `uv sync --all-packages`**

```bash
uv sync --all-packages
```

Expected: exits 0, all workspace members resolved.

- [ ] **Step 2: Run lint**

```bash
make lint
```

Expected: exits 0, no lint errors. The only Python files at this point are empty `__init__.py` and stub docstring-only files — ruff should pass cleanly.

- [ ] **Step 3: Run typecheck**

```bash
make typecheck
```

Expected: exits 0. With only empty and stub files, mypy should pass.

- [ ] **Step 4: Verify `make bdd` fails gracefully (no feature files yet)**

```bash
make bdd
```

Expected: behave exits with "no features found" or similar — not a crash. This confirms behave is installed and the runner works. A non-zero exit here is acceptable; the spec says no `.feature` files exist yet.

- [ ] **Step 5: Final commit if anything was missed**

```bash
git status
```

If any untracked files remain, add and commit them.
