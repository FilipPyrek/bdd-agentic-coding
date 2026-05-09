"""httpx-based test client helpers for BDD step definitions."""
from __future__ import annotations

from typing import Any

from starlette.testclient import TestClient


def make_client(app: Any) -> TestClient:
    return TestClient(app, raise_server_exceptions=True)
