from __future__ import annotations


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict] = {}

    def add(self, user: dict) -> None:
        self._users[user["email"].lower()] = user

    def exists(self, email: str) -> bool:
        return email.lower() in self._users

    def get(self, email: str) -> dict | None:
        return self._users.get(email.lower())

    def get_by_id(self, user_id: str) -> dict | None:
        for user in self._users.values():
            if user["id"] == user_id:
                return user
        return None

    def clear(self) -> None:
        self._users.clear()


_store = UserStore()
