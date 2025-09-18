from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    ERR_INVALID_VARIABLE_ID,
    ERR_INVALID_WORKSPACE_ID,
    ERR_REQUIRED_CATEGORY,
    ERR_REQUIRED_KEY,
)
from ..types import (
    Variable,
    VariableCreateOptions,
    VariableListOptions,
    VariableUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


class Variables(_Service):
    def list(
        self, workspace_id: str, options: VariableListOptions | None = None
    ) -> Iterator[Variable]:
        """List all the variables associated with the given workspace (doesn't include variables inherited from varsets)."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        path = f"/api/v2/workspaces/{workspace_id}/vars"
        params: dict[str, Any] = {}
        if options:
            # Add any options if needed in the future
            pass

        for item in self._list(path, params=params):
            attr = item.get("attributes", {}) or {}
            var_id = item.get("id", "")
            variable_data = dict(attr)
            variable_data["id"] = var_id
            yield Variable(**variable_data)

    def list_all(
        self, workspace_id: str, options: VariableListOptions | None = None
    ) -> Iterator[Variable]:
        """ListAll the variables associated with the given workspace including variables inherited from varsets."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        path = f"/api/v2/workspaces/{workspace_id}/all-vars"
        params: dict[str, Any] = {}
        if options:
            # Add any options if needed in the future
            pass

        for item in self._list(path, params=params):
            attr = item.get("attributes", {}) or {}
            var_id = item.get("id", "")
            variable_data = dict(attr)
            variable_data["id"] = var_id
            yield Variable(**variable_data)

    def create(self, workspace_id: str, options: VariableCreateOptions) -> Variable:
        """Create is used to create a new variable."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        # Validate required fields
        if not valid_string(options.key):
            raise ValueError(ERR_REQUIRED_KEY)
        if options.category is None:
            raise ValueError(ERR_REQUIRED_CATEGORY)

        body = {
            "data": {
                "type": "vars",
                "attributes": options.model_dump(exclude_none=True),
            }
        }

        response = self.t.request(
            "POST", f"/api/v2/workspaces/{workspace_id}/vars", json_body=body
        )
        data = response.json()["data"]

        # Parse the response and create Variable object
        attr = data.get("attributes", {}) or {}
        variable_id = data.get("id", "")
        variable_data = dict(attr)
        variable_data["id"] = variable_id

        return Variable(**variable_data)

    def read(self, workspace_id: str, variable_id: str) -> Variable:
        """Read a variable by its ID."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)
        if not valid_string_id(variable_id):
            raise ValueError(ERR_INVALID_VARIABLE_ID)

        response = self.t.request(
            "GET", f"/api/v2/workspaces/{workspace_id}/vars/{variable_id}"
        )
        data = response.json()["data"]

        # Parse the response and create Variable object
        attr = data.get("attributes", {}) or {}
        var_id = data.get("id", "")
        variable_data = dict(attr)
        variable_data["id"] = var_id

        return Variable(**variable_data)

    def update(
        self, workspace_id: str, variable_id: str, options: VariableUpdateOptions
    ) -> Variable:
        """Update values of an existing variable."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)
        if not valid_string_id(variable_id):
            raise ValueError(ERR_INVALID_VARIABLE_ID)

        body = {
            "data": {
                "type": "vars",
                "attributes": options.model_dump(exclude_none=True),
            }
        }

        response = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/vars/{variable_id}",
            json_body=body,
        )
        data = response.json()["data"]

        # Parse the response and create Variable object
        attr = data.get("attributes", {}) or {}
        var_id = data.get("id", "")
        variable_data = dict(attr)
        variable_data["id"] = var_id

        return Variable(**variable_data)

    def delete(self, workspace_id: str, variable_id: str) -> None:
        """Delete a variable by its ID."""
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)
        if not valid_string_id(variable_id):
            raise ValueError(ERR_INVALID_VARIABLE_ID)

        self.t.request(
            "DELETE", f"/api/v2/workspaces/{workspace_id}/vars/{variable_id}"
        )
        return None
