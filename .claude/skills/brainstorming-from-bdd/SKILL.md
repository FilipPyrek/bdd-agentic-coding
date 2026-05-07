---
name: brainstorming-from-bdd
description: Loads a decision log from writing-bdd-scenarios and kicks off brainstorming for implementation.
disable-model-invocation: true
---

# Brainstorming Implementation

## Overview

Thin wrapper that loads a feature specification (decision log + referenced scenarios) and
invokes the brainstorming skill with that context pre-loaded. The user has already captured
WHAT to build via writing-bdd-scenarios — this skill starts the conversation about HOW.

## When to Use

When you have a completed feature specification (decision log + scenarios from writing-bdd-scenarios)
and want to brainstorm the implementation approach.

**When NOT to use:**

- Brainstorming without a decision log — use the brainstorming skill directly
- Modifying or adding BDD scenarios — use writing-bdd-scenarios
- You haven't finished the writing-bdd-scenarios process yet (no decision log exists)

## Process

### 1. Select Decision Log

Glob `docs/decisions-log/*.md`, sort by filename (timestamp prefix) descending, take the
3 most recent. Present them to the user via the question/picker tool. The user picks one
or types a custom path.

### 2. Load Context

- Read the selected decision log
- Parse the `## Affected Scenarios` section to extract referenced `.feature` file paths
- Read those feature files

### 3. Invoke Brainstorming

Invoke the `brainstorming` skill (from superpowers) with the following user message, including
the decision log and feature file paths as file references so the engine reads them automatically:

> I have a feature specification prepared, but now I would like to brainstorm implementation steps and make sure all the details are addressed. Make sure to focus on implementing everything so that when you execute the feature file, it passes successfully.
>
> Decision log: <path to decision log>
> Scenarios: <paths to .feature files>

The brainstorming skill will pick up from there with full context.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Invoking without a completed decision log | Finish writing-bdd-scenarios first — partial logs lead to incomplete brainstorming |
| Only passing the decision log, not the feature files | The brainstorming skill needs concrete scenarios to reason about implementation |
| Trying to implement during brainstorming | Brainstorming produces a plan, not code — implementation is a separate step |

## Exit Criteria

This skill's job is done once brainstorming is invoked with the loaded context. From that
point, the brainstorming skill owns the session.
