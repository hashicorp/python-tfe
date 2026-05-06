from __future__ import annotations

from ..models.user import User, UserUpdateCurrentOptions
from ..utils import valid_string_id
from ._base import _Service


class Users(_Service):
    def read(self, user_id: str) -> User:
        if not valid_string_id(user_id):
            raise ValueError("invalid user id")

        r = self.t.request("GET", f"/api/v2/users/{user_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)

    def read_current(self) -> User:
        r = self.t.request("GET", "/api/v2/account/details")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)

    def update_current(self, options: UserUpdateCurrentOptions) -> User:
        body = {
            "data": {
                "type": "users",
                "attributes": options.model_dump(exclude_none=True),
            }
        }
        r = self.t.request("PATCH", "/api/v2/account/update", json_body=body)
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        user_data = dict(attr)
        user_data["id"] = d.get("id")
        return User(**user_data)