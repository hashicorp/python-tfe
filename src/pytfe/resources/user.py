from __future__ import annotations

from ..models.user import User
from ._base import _Service


class Users(_Service):
    def read(self, user_id: str) -> User:
        r = self.t.request("GET", f"/api/v2/users/{user_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)
