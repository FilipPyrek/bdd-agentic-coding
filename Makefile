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
