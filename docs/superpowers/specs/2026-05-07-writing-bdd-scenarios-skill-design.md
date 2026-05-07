# Writing BDD Scenarios Skill — Design Spec

## Purpose

Replace the existing `writing-bdd-scenarios` skill with a comprehensive process skill that serves as the SDLC entry point for any feature work. The skill orchestrates a collaborative PM + developer + AI session to produce Gherkin scenarios as executable requirements.

## Philosophy

- BDD scenarios are **requirements**, not tests
- They are PM-readable, implementation-free, and serve as feedback for AI agents during implementation
- The Gherkin layer knows nothing about HTTP, JSON, databases, or internal APIs
- Step definitions own the technical verification layer
- This is the beginning of the development lifecycle — scenarios are written before any implementation code

## Trigger Conditions

The skill activates when:

- Someone wants to add a new feature or capability
- Someone wants to change existing behavior
- Someone wants to remove/deprecate a feature
- Any `.feature` file is about to be created or edited

## Process Flow

Seven phases, executed in order:

### Phase 1: DETECT

Determine the type of change:

- **New feature** → full flow (all phases)
- **Modification** → ANALYZE existing scenarios first, then full flow
- **Deprecation** → shortened flow: DETECT → ANALYZE → DISCOVER (confirm intent) → REVIEW (ripple effects) → WRITE (remove scenarios, write decision log)

### Phase 2: ANALYZE

- Read existing `.feature` files in the relevant service/area
- Summarize current scenario landscape
- For modifications/deprecations: identify affected scenarios
- Skipped only if greenfield with zero existing scenarios

### Phase 3: DISCOVER

Conversational extraction — AI asks one question at a time (multiple choice preferred):

- What capability are we adding/changing?
- Who are the actors (roles)?
- What triggers this behavior?
- What's the expected outcome?
- Are there constraints or dependencies on other services?

Continues until the AI has enough context to draft.

### Phase 4: DRAFT ROUND 1 (happy paths)

- AI proposes Feature description + scenarios
- Only business-meaningful happy paths
- Team reviews, adjusts, approves

### Phase 5: DRAFT ROUND 2 (edge cases — mandatory)

AI systematically pushes:

- "What if this fails?"
- "What if the actor doesn't have permission?"
- "What if the input is invalid/missing?"
- "What about concurrency/timing?"
- "What about boundaries (zero, max, empty)?"

For each: team says "add it" or "out of scope" (logged in decision log). Round cannot be skipped.

### Phase 6: REVIEW

- Read back all scenarios as a whole
- Check for: contradictions with existing scenarios, duplication, consistent domain language, each scenario telling a complete story

### Phase 7: WRITE

- Write `.feature` file(s)
- Write decision log to `docs/decisions-log/<timestamp>-<feature-area>.md`
- Commit both artifacts

## Guardrails

Eight opinionated rules the skill enforces:

### 1. No implementation detail in Gherkin

Describe what the system does, not how. Step definitions own transport/protocol/mechanics. Even for API-only products — describe what the API delivers, not HTTP mechanics.

### 2. Round 2 is mandatory

AI always pushes for edge cases after happy paths. Team can defer items as "out of scope" (recorded in decision log) but cannot skip the round. No exceptions: not for "obvious" features, not for single-scenario features, not when running short on time.

### 3. Use roles for actors, never "the user" or "I"

The role communicates why the actor matters (permissions, responsibilities). For system-initiated processes (batch jobs, scheduled tasks, events), the job/event is the actor.

### 4. One business trigger per scenario

Each scenario validates one cause-and-effect. Complex workflows use multiple scenarios in sequence within the same feature file.

### 5. Each scenario tells a complete story

A PM should understand the scenario without reading other scenarios or scrolling up.

Techniques (in preference order):
1. Declarative Given steps — state the situation in business terms, not setup mechanics
2. Feature description — use the prose block under `Feature:` for shared domain context
3. Short Background — max 3-4 lines of truly universal setup
4. Scenario Outlines — for behavioral variations on a theme

Anti-patterns:
- Background longer than 5 lines
- Scenario with 6+ Given steps
- Scenario that references another scenario

### 6. Then steps describe outcomes, not mechanics

What should be true — not how the system achieves it. Step definitions decide how to verify.

### 7. Use consistent domain language

Same concept = same word everywhere. Clarify ambiguous terms in the Feature description when needed.

### 8. AI proposes first, team edits

AI drafts scenarios based on what it learned in DISCOVER. Team reacts and adjusts. This is faster and gives the team something concrete to react to.

## Output Artifacts

### .feature files

Written to the appropriate service's `features/` directory (or `e2e/features/` for cross-service scenarios).

### Decision Log

Location: `docs/decisions-log/<unix-timestamp>-<feature-area>.md`

Template:

```markdown
# <Feature Area>

- **Date:** YYYY-MM-DD
- **Type:** new | modification | deprecation

## Context

<1-3 sentences: why this session happened>

## Decisions

- <Decision 1> — <brief rationale>
- <Decision 2> — <brief rationale>

## Out of Scope

- <Item consciously deferred>

## Affected Scenarios

- <path to .feature file(s) created/modified/removed>
```

## File Structure

```
.claude/skills/writing-bdd-scenarios/
├── SKILL.md              (~300 lines, everything essential)
└── EXAMPLE-SESSION.md    (~80 lines, compressed conversation walkthrough)
```

### SKILL.md Internal Structure

1. Frontmatter (trigger-only description, no workflow summary)
2. Overview (2-3 sentences, philosophy)
3. When to Use / When NOT to Use
4. Guardrails (the 8 rules, compact)
5. Process Flow (DOT flowchart + 2-3 line summary per phase)
6. Decision Log Template
7. Good/Bad Gherkin Example (enterprise-style, inline)
8. Red Flags / Rationalization Table
9. Exit Criteria

### EXAMPLE-SESSION.md

A compressed conversation walkthrough (~80 lines) showing all 7 phases in action. Demonstrates how the AI guides the session, what questions it asks, how it drafts and iterates. Referenced from SKILL.md but only loaded when needed.

## Exit Criteria

The skill is "done" when:

1. `.feature` file(s) are written and approved by the team
2. Decision log is written to `docs/decisions-log/<timestamp>-<feature-area>.md`
3. Both artifacts are committed to git
4. The skill explicitly states: "Requirements are captured. Implementation can proceed separately."

The skill does NOT write step definitions, implementation code, or invoke any other skill. Clean handoff — the next step is the team's choice.

## Scope of Invocation

- Can span multiple `.feature` files if the change is cross-cutting
- Typically maps to one feature area per session
- The AI analyzes existing scenarios in the relevant area before proposing changes

## Relationship to Other Artifacts

- **Step definitions:** Written separately during implementation. Not part of this skill.
- **Integration/unit tests:** Separate concern entirely. This skill produces requirements only.
- **Implementation planning:** Happens after this skill completes, via separate workflow.
