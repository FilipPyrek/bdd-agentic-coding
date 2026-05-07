# Executable BDD Requirements for AI-Driven Development

<p align="center">

  <img width="256" height="256" alt="BDD+Claude" src="https://github.com/user-attachments/assets/adf22a72-5dde-4b82-8bc6-d5a709a57a6a" />
  
</p>


> **TL;DR:** BDD + AI = executable requirements that close the feedback loop. Instead of AI guessing whether its implementation is correct, it runs the scenarios and _knows_. Instead of PMs reviewing code, they review plain-English scenarios. Everyone speaks the same language — Gherkin — and the machine verifies it continuously.

## The Idea

This repository demonstrates how **Behaviour-Driven Development (BDD)** can serve as an executable specification layer in **Spec-Driven Development**. The core insight:

> Gherkin scenarios are requirements that humans can read **and** machines can execute.

When AI agents implement features, they get a built-in feedback loop: run the scenarios, see what passes, iterate until green. No ambiguity about what "done" looks like — the requirements _are_ the acceptance criteria, and they're automated.

### Why not prose specs alone?

Prose specs (design documents, tickets, user stories) tell the AI _what_ to build, but offer no automated way to verify correctness. The AI must rely on the developer to confirm success. With BDD:

1. **Human-readable** — A PM or stakeholder reads the `.feature` files and validates they capture the right behavior
2. **Machine-executable** — `make bdd` gives pass/fail feedback in seconds
3. **Implementation-agnostic** — Gherkin says _what_, never _how_. Transport, storage, and framework details live in step definitions

This creates a closed loop: **Spec → Scenarios → Implementation → Green scenarios → Done.**

## How It Works in Practice

### The Development Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  1. REQUIREMENTS (Gherkin)                                      │
│     - PM + developer + AI collaborate to write .feature files   │
│     - Scenarios express business behavior in plain English       │
│     - No HTTP codes, no JSON, no implementation detail           │
│                                                                  │
│  2. DESIGN (Spec documents)                                     │
│     - Architecture, data flow, validation rules                 │
│     - Lives in docs/superpowers/specs/                           │
│                                                                  │
│  3. IMPLEMENTATION (AI-driven)                                  │
│     - AI writes code, runs `make bdd`, iterates                 │
│     - Scenarios provide continuous pass/fail signal              │
│     - Done when all scenarios pass                              │
└─────────────────────────────────────────────────────────────────┘
```

### The Feedback Loop for AI Agents

When an AI agent picks up a feature task:

1. It reads the `.feature` file — these are the acceptance criteria
2. It reads the design spec — this is the implementation guidance
3. It writes code
4. It runs `make bdd` — red/green feedback
5. It iterates until all scenarios pass

No human-in-the-loop needed for "is this correct?" — the scenarios answer that question automatically.

## Repository Structure

A monorepo with `uv` workspaces simulating a multi-service system (like a team of ~80 engineers would maintain):

```
bdd-experiment/
├── pyproject.toml          # workspace root
├── Makefile                # bdd, lint, format, typecheck
├── AGENTS.md               # conventions for AI agents
├── services/
│   ├── users/              # registration, login, profile
│   ├── orders/             # place and view orders (stub)
│   └── inventory/          # stock levels (stub)
├── e2e/                    # cross-service scenarios
├── shared/                 # test client, environment hooks
└── docs/
    └── superpowers/specs/  # design specifications
```

### Sample Scenario

From `services/users/features/registration.feature`:

```gherkin
Feature: User registration

  Anyone can create an account by providing their name, email address,
  and a password. No email verification is required.

  Scenario: Successful registration
    Given a visitor with a valid name, email, and password
    When they register
    Then their account is created
    And they can log in with their email and password

  Scenario: Duplicate email is rejected
    Given a user has already registered with "alice@example.com"
    When a visitor tries to register with "alice@example.com"
    Then they see an error: "Email already in use"
```

Notice: no HTTP verbs, no status codes, no JSON. Just business behavior.

## Key Principles

### Scenarios are requirements, not tests

They describe _what the system does_ from the user's perspective. A PM should be able to read every scenario and confirm "yes, that's the product we want."

### Step definitions own the technical layer

The glue code in `features/steps/` translates business language into HTTP calls via `shared.client`. If the transport changes from REST to gRPC, the Gherkin stays identical — only step definitions change.

### One scenario, one business trigger

Each scenario validates a single cause-and-effect. Complex workflows use multiple scenarios in sequence.

### Roles, not "the user"

Scenarios use named actors (Alice, Bob) or roles. This communicates permissions and context without relying on a generic "I" or "the user."

## AI Skills (`.claude/skills/`)

This repo includes custom AI skills that encode the development workflow. They are loaded automatically when an AI agent works in this codebase, ensuring consistent process regardless of which session or which human is involved.

### `writing-bdd-scenarios` — Requirements Capture

**Location:** `.claude/skills/writing-bdd-scenarios/SKILL.md`

The entry point of the development lifecycle. This skill orchestrates a collaborative PM + developer + AI session to produce Gherkin scenarios as executable requirements. It enforces a structured 12-phase process:

| Phase | Purpose |
|-------|---------|
| INTAKE | Collect user's intent in their own words |
| RECON | Silently explore the target service's codebase |
| DISCOVER | Ask one question at a time until readiness criteria are met |
| ANALYZE | Review existing scenarios relevant to the requirement |
| CHALLENGE | Push back on assumptions (mandatory — at least one pushback) |
| DRAFT ROUND 1 | AI proposes happy-path scenarios |
| DRAFT ROUND 2 | AI pushes for edge cases (mandatory, cannot be skipped) |
| IMPLEMENTATION NOTES | Capture non-scenario decisions (trimming, case sensitivity, etc.) |
| REVIEW | Check all scenarios for contradictions, duplication, consistency |
| WRITE | Write `.feature` file(s) + decision log |
| SELF-REVIEW | Dispatch a subagent to review outputs against guardrails |
| PROPOSE COMMIT | Ask user before committing |

**Key guardrails enforced by the skill:**

- No implementation detail in Gherkin (no HTTP, no JSON, no DB references)
- Round 2 (edge cases) is mandatory — cannot be skipped for any reason
- Use roles for actors, never "the user" or "I"
- One business trigger per scenario
- Each scenario tells a complete story without needing to read other scenarios
- AI proposes first, team edits (not the other way around)
- One question per message during DISCOVER (no batched questions)

**Hard gate:** The skill produces ONLY `.feature` files and a decision log. It never writes step definitions, implementation code, or invokes any implementation skill.

**Output artifacts:**
- `.feature` files in the relevant service's `features/` directory
- Decision log at `docs/decisions-log/<unix-timestamp>-<feature-area>.md`

### `brainstorming-from-bdd` — Implementation Kickoff

**Location:** `.claude/skills/brainstorming-from-bdd/SKILL.md`

A bridge skill that loads a completed feature specification (decision log + scenarios) from the `writing-bdd-scenarios` output and kicks off brainstorming for how to implement it.

**Process:**

1. **Select** — Presents the 3 most recent decision logs for the user to pick
2. **Load** — Reads the decision log and all referenced `.feature` files
3. **Invoke** — Launches the `brainstorming` skill with full context pre-loaded, focused on making `behave` scenarios pass

**Success criteria it sets for the brainstorming session:**
- All scenarios pass (exit code 0)
- Zero undefined steps
- Zero pending steps
- No skipped scenarios

This creates the complete handoff: requirements (BDD skill) → design (brainstorming) → implementation.

### How the Skills Chain Together

```
┌──────────────────────────┐     ┌──────────────────────────┐     ┌─────────────────┐
│  writing-bdd-scenarios   │────▶│  brainstorming-from-bdd  │────▶│  Implementation  │
│                          │     │                          │     │                  │
│  Produces:               │     │  Loads:                  │     │  Guided by:      │
│  • .feature files        │     │  • decision log          │     │  • design spec   │
│  • decision log          │     │  • .feature files        │     │  • BDD feedback  │
│                          │     │                          │     │  • make bdd      │
└──────────────────────────┘     └──────────────────────────┘     └─────────────────┘
```

The key insight: each phase produces artifacts the next phase consumes. Requirements are never lost between sessions because they're encoded as executable `.feature` files and decision logs — not chat history.

## Setup & Commands

```bash
# Install all dependencies
uv sync --all-packages

# Run all BDD scenarios
make bdd

# Run only e2e scenarios
make bdd-e2e

# Run a single service
uv run --package users behave

# Lint / format / typecheck
make lint
make format
make typecheck
```

## Tooling

| Tool | Purpose |
|------|---------|
| `uv` | Package manager (replaces pip/venv) |
| `behave` | BDD framework (Gherkin → Python steps) |
| `FastAPI` | Web framework for stub services |
| `httpx` | In-process test client (ASGI, no server needed) |
| `ruff` | Linting and formatting |
| `mypy` | Type checking (strict mode) |

## Design Specs

Detailed design documents live in `docs/superpowers/specs/`:

| Spec | Description |
|------|-------------|
| `2026-05-06-bdd-experiment-design.md` | Overall architecture, conventions, and rationale |
| `2026-05-07-user-registration-design.md` | Registration feature: data layer, service layer, routes, validation rules |
| `2026-05-07-login-token-and-profile-design.md` | Login tokens, profile access, authorization |
| `2026-05-07-writing-bdd-scenarios-skill-design.md` | The AI skill for collaborative scenario writing |
