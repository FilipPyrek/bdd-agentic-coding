"""Base behave environment hooks: server startup/teardown and state reset."""
from __future__ import annotations

from users.main import app
from users.store import _store

from shared.client import make_client


def before_scenario(context, scenario):
    _store.clear()
    context.client = make_client(app)
