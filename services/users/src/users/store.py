from __future__ import annotations

from typing import Any

UserRecord = dict[str, Any]


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

    def add(self, user: UserRecord) -> None:
        self._users[user["email"].lower()] = user

    def exists(self, email: str) -> bool:
        return email.lower() in self._users

    def get(self, email: str) -> UserRecord | None:
        return self._users.get(email.lower())

    def get_by_id(self, user_id: str) -> UserRecord | None:
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def clear(self) -> None:
        self._users.clear()


_store = UserStore()
