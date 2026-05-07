from __future__ import annotations

import uuid


class TokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    def issue(self, user_id: str) -> str:
        token = str(uuid.uuid4())
        self._tokens[token] = user_id
        return token

    def get_user_id(self, token: str) -> str | None:
        return self._tokens.get(token)

    def clear(self) -> None:
        self._tokens.clear()


_token_store = TokenStore()
