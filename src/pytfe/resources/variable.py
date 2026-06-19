# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    ERR_INVALID_VARIABLE_ID,
    ERR_INVALID_WORKSPACE_ID,
    ERR_REQUIRED_CATEGORY,
    ERR_REQUIRED_KEY,
)
from ..models.variable import (
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
        """List workspace variables, excluding variables inherited from variable sets.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Reserved for future filters, as a :class:`VariableListOptions`.

        Returns:
            A single-use ``Iterator[Variable]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for variable in client.variables.list("ws-6fHMCom98SDXSQUv"):
            ...     print(variable.key, variable.category)
        """
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        # The /vars endpoint is not paginated: it returns every variable in a
        # single response and ignores page[number]/page[size]. Opt out of the
        # pagination loop so we issue exactly one request (python-tfe#181).
        path = f"/api/v2/workspaces/{workspace_id}/vars"
        params: dict[str, Any] = {}
        if options:
            # Add any options if needed in the future
            pass

        for item in self._list(path, params=params, paginated=False):
            attr = item.get("attributes", {}) or {}
            var_id = item.get("id", "")
            variable_data = dict(attr)
            variable_data["id"] = var_id
            yield Variable(**variable_data)

    def list_all(
        self, workspace_id: str, options: VariableListOptions | None = None
    ) -> Iterator[Variable]:
        """List all workspace variables, including inherited variable-set variables.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Reserved for future filters, as a :class:`VariableListOptions`.

        Returns:
            A single-use ``Iterator[Variable]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> inherited = list(client.variables.list_all("ws-6fHMCom98SDXSQUv"))
            >>> print(len(inherited))
        """
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)

        # Like /vars, the /all-vars endpoint is not paginated; request once.
        path = f"/api/v2/workspaces/{workspace_id}/all-vars"
        params: dict[str, Any] = {}
        if options:
            # Add any options if needed in the future
            pass

        for item in self._list(path, params=params, paginated=False):
            attr = item.get("attributes", {}) or {}
            var_id = item.get("id", "")
            variable_data = dict(attr)
            variable_data["id"] = var_id
            yield Variable(**variable_data)

    def create(self, workspace_id: str, options: VariableCreateOptions) -> Variable:
        """Create a new workspace variable.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: The variable attributes, as a :class:`VariableCreateOptions`.

        Returns:
            The created :class:`Variable`.

        Raises:
            ValueError: If ``workspace_id`` is invalid, ``key`` is missing, or
                ``category`` is missing.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CategoryType, VariableCreateOptions
            >>> variable = client.variables.create(
            ...     "ws-6fHMCom98SDXSQUv",
            ...     VariableCreateOptions(
            ...         key="TF_LOG", value="INFO", category=CategoryType.ENV
            ...     ),
            ... )
        """
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
        """Read a workspace variable by its ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            The :class:`Variable`.

        Raises:
            ValueError: If ``workspace_id`` or ``variable_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> variable = client.variables.read(
            ...     "ws-6fHMCom98SDXSQUv", "var-N4b1qYNSuNsPzHhM"
            ... )
            >>> print(variable.key)
        """
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
        """Update an existing workspace variable.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).
            options: The changed variable attributes, as a
                :class:`VariableUpdateOptions`.

        Returns:
            The updated :class:`Variable`.

        Raises:
            ValueError: If ``workspace_id`` or ``variable_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableUpdateOptions
            >>> variable = client.variables.update(
            ...     "ws-6fHMCom98SDXSQUv",
            ...     "var-N4b1qYNSuNsPzHhM",
            ...     VariableUpdateOptions(value="DEBUG"),
            ... )
        """
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
        """Delete a workspace variable by its ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``workspace_id`` or ``variable_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.variables.delete(
            ...     "ws-6fHMCom98SDXSQUv", "var-N4b1qYNSuNsPzHhM"
            ... )
        """
        if not valid_string_id(workspace_id):
            raise ValueError(ERR_INVALID_WORKSPACE_ID)
        if not valid_string_id(variable_id):
            raise ValueError(ERR_INVALID_VARIABLE_ID)

        self.t.request(
            "DELETE", f"/api/v2/workspaces/{workspace_id}/vars/{variable_id}"
        )
        return None
