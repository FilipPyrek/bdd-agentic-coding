bdd:
	uv run --package users --directory services/users behave || true
	uv run --package orders --directory services/orders behave || true
	uv run --package inventory --directory services/inventory behave || true
	uv run --package e2e --directory e2e behave || true

bdd-e2e:
	uv run --package e2e --directory e2e behave || true

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

setup:
	uv sync --all-packages
