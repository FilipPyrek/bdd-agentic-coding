"""httpx-based test client helpers for BDD step definitions."""
from __future__ import annotations

from starlette.testclient import TestClient
from starlette.types import ASGIApp


def make_client(app: ASGIApp) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
