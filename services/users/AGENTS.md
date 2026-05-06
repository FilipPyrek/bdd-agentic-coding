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
