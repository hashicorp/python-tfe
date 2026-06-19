# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Variable Set resource implementation for the Python TFE SDK."""

import builtins
from collections.abc import Iterator
from typing import Any

from .._http import HTTPTransport
from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..models.project import Project
from ..models.variable_set import (
    VariableSet,
    VariableSetApplyToProjectsOptions,
    VariableSetApplyToWorkspacesOptions,
    VariableSetCreateOptions,
    VariableSetIncludeOpt,
    VariableSetListOptions,
    VariableSetReadOptions,
    VariableSetRemoveFromProjectsOptions,
    VariableSetRemoveFromWorkspacesOptions,
    VariableSetUpdateOptions,
    VariableSetUpdateWorkspacesOptions,
    VariableSetVariable,
    VariableSetVariableCreateOptions,
    VariableSetVariableListOptions,
    VariableSetVariableUpdateOptions,
)
from ..models.workspace import Workspace
from ._base import _Service

# Typed relations hydrated from ?include= (workspaces, projects, vars). The
# polymorphic ``parent`` relation is handled separately. See VariableSetIncludeOpt.
_VARIABLE_SET_REL_MAP: RelationMap = {
    "workspaces": Workspace,
    "projects": Project,
    "vars": VariableSetVariable,
}


class VariableSets(_Service):
    """
    Variable Sets resource for managing Terraform Cloud/Enterprise Variable Sets.

    Variable Sets provide a way to define and manage collections of variables
    that can be applied to multiple workspaces or projects, supporting both
    global and scoped variable management.

    API Documentation:
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets
    """

    def __init__(self, transport: HTTPTransport):
        """Initialize the Variable Sets resource.

        Args:
            transport: HTTP transport instance for API communication
        """
        super().__init__(transport)

    def list(
        self,
        organization: str,
        options: VariableSetListOptions | None = None,
    ) -> Iterator[VariableSet]:
        """List variable sets in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters and includes, as a
                :class:`VariableSetListOptions`.

        Returns:
            A single-use ``Iterator[VariableSet]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``organization`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetListOptions
            >>> for varset in client.variable_sets.list(
            ...     "my-org", VariableSetListOptions(query="shared")
            ... ):
            ...     print(varset.id, varset.name)
        """
        if not organization or not isinstance(organization, str):
            raise ValueError("Organization name is required and must be a string")

        path = f"/api/v2/organizations/{organization}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        for item in self._list(path, params=params):
            yield self._parse_variable_set(item)

    def list_for_workspace(
        self,
        workspace_id: str,
        options: VariableSetListOptions | None = None,
    ) -> Iterator[VariableSet]:
        """List variable sets associated with a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional filters and includes, as a
                :class:`VariableSetListOptions`.

        Returns:
            A single-use ``Iterator[VariableSet]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``workspace_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> for varset in client.variable_sets.list_for_workspace(
            ...     "ws-4j8p6jX1w33MiDC7"
            ... ):
            ...     print(varset.id, varset.name)
        """
        if not workspace_id or not isinstance(workspace_id, str):
            raise ValueError("Workspace ID is required and must be a string")

        path = f"/api/v2/workspaces/{workspace_id}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        for item in self._list(path, params=params):
            yield self._parse_variable_set(item)

    def list_for_project(
        self,
        project_id: str,
        options: VariableSetListOptions | None = None,
    ) -> Iterator[VariableSet]:
        """List variable sets associated with a project.

        Args:
            project_id: The project ID (e.g. ``"prj-xxxxxxxx"``).
            options: Optional filters and includes, as a
                :class:`VariableSetListOptions`.

        Returns:
            A single-use ``Iterator[VariableSet]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``project_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> for varset in client.variable_sets.list_for_project(
            ...     "prj-4j8p6jX1w33MiDC7"
            ... ):
            ...     print(varset.id, varset.name)
        """
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID is required and must be a string")

        path = f"/api/v2/projects/{project_id}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        for item in self._list(path, params=params):
            yield self._parse_variable_set(item)

    def create(
        self,
        organization: str,
        options: VariableSetCreateOptions,
    ) -> VariableSet:
        """Create a variable set in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The variable set configuration, as a
                :class:`VariableSetCreateOptions`.

        Returns:
            The :class:`VariableSet`.

        Raises:
            ValueError: If ``organization`` is not a string, ``options`` is not a
                :class:`VariableSetCreateOptions`, or ``options.name`` is blank.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetCreateOptions
            >>> varset = client.variable_sets.create(
            ...     "my-org",
            ...     VariableSetCreateOptions(name="shared", global_=False),
            ... )
        """
        if not organization or not isinstance(organization, str):
            raise ValueError("Organization name is required and must be a string")

        if not options or not isinstance(options, VariableSetCreateOptions):
            raise ValueError(
                "Options are required and must be VariableSetCreateOptions"
            )

        if not options.name:
            raise ValueError("Variable set name is required")

        path = f"/api/v2/organizations/{organization}/varsets"

        payload: dict[str, Any] = {
            "data": {
                "type": "varsets",
                "attributes": {
                    "name": options.name,
                    "global": options.global_,
                },
            }
        }

        attributes = payload["data"]["attributes"]
        if options.description is not None:
            attributes["description"] = options.description

        if options.priority is not None:
            attributes["priority"] = options.priority

        # Handle parent relationship
        if options.parent:
            relationships: dict[str, Any] = {}
            if options.parent.project and options.parent.project.id:
                relationships["parent"] = {
                    "data": {
                        "type": "projects",
                        "id": options.parent.project.id,
                    }
                }
            elif options.parent.organization and options.parent.organization.id:
                relationships["parent"] = {
                    "data": {
                        "type": "organizations",
                        "id": options.parent.organization.id,
                    }
                }
            if relationships:
                payload["data"]["relationships"] = relationships

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()

        return self._parse_variable_set(data["data"])

    def read(
        self,
        variable_set_id: str,
        options: VariableSetReadOptions | None = None,
    ) -> VariableSet:
        """Read a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: Optional includes, as a :class:`VariableSetReadOptions`.

        Returns:
            The :class:`VariableSet`.

        Raises:
            ValueError: If ``variable_set_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetReadOptions
            >>> varset = client.variable_sets.read(
            ...     "varset-4j8p6jX1w33MiDC7", VariableSetReadOptions()
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}"
        params: dict[str, str] = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()

        return self._parse_variable_set(data["data"], data.get("included"))

    def update(
        self,
        variable_set_id: str,
        options: VariableSetUpdateOptions,
    ) -> VariableSet:
        """Update a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The variable set updates, as a
                :class:`VariableSetUpdateOptions`.

        Returns:
            The :class:`VariableSet`.

        Raises:
            ValueError: If ``variable_set_id`` is not a string or ``options`` is not a
                :class:`VariableSetUpdateOptions`.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetUpdateOptions
            >>> varset = client.variable_sets.update(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetUpdateOptions(description="Shared AWS settings"),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetUpdateOptions):
            raise ValueError(
                "Options are required and must be VariableSetUpdateOptions"
            )

        path = f"/api/v2/varsets/{variable_set_id}"

        payload: dict[str, Any] = {
            "data": {
                "type": "varsets",
                "id": variable_set_id,
                "attributes": {},
            }
        }

        attributes = payload["data"]["attributes"]
        if options.name is not None:
            attributes["name"] = options.name

        if options.description is not None:
            attributes["description"] = options.description

        if options.global_ is not None:
            attributes["global"] = options.global_

        if options.priority is not None:
            attributes["priority"] = options.priority

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()

        return self._parse_variable_set(data["data"])

    def delete(self, variable_set_id: str) -> None:
        """Delete a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> client.variable_sets.delete("varset-4j8p6jX1w33MiDC7")
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}"
        self.t.request("DELETE", path)

    def apply_to_workspaces(
        self,
        variable_set_id: str,
        options: VariableSetApplyToWorkspacesOptions,
    ) -> None:
        """Apply a non-global variable set to workspaces.

        This endpoint returns an API error when the variable set has ``global=True``.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The workspace relationship payload, as a
                :class:`VariableSetApplyToWorkspacesOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` is not a string, ``options`` is not a
                :class:`VariableSetApplyToWorkspacesOptions`, no workspaces are
                supplied, or any supplied workspace has no ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetApplyToWorkspacesOptions, Workspace
            >>> client.variable_sets.apply_to_workspaces(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetApplyToWorkspacesOptions(
            ...         workspaces=[Workspace.model_construct(id="ws-4j8p6jX1w33MiDC7")]
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetApplyToWorkspacesOptions):
            raise ValueError(
                "Options are required and must be VariableSetApplyToWorkspacesOptions"
            )

        if not options.workspaces:
            raise ValueError("At least one workspace is required")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/workspaces"

        # Build workspace relationships payload
        workspace_data = []
        for workspace in options.workspaces:
            if not workspace.id:
                raise ValueError("All workspaces must have valid IDs")
            workspace_data.append(
                {
                    "type": "workspaces",
                    "id": workspace.id,
                }
            )

        payload = {"data": workspace_data}

        self.t.request("POST", path, json_body=payload)

    def remove_from_workspaces(
        self,
        variable_set_id: str,
        options: VariableSetRemoveFromWorkspacesOptions,
    ) -> None:
        """Remove a non-global variable set from workspaces.

        This endpoint returns an API error when the variable set has ``global=True``.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The workspace relationship payload, as a
                :class:`VariableSetRemoveFromWorkspacesOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` is not a string, ``options`` is not a
                :class:`VariableSetRemoveFromWorkspacesOptions`, no workspaces are
                supplied, or any supplied workspace has no ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetRemoveFromWorkspacesOptions, Workspace
            >>> client.variable_sets.remove_from_workspaces(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetRemoveFromWorkspacesOptions(
            ...         workspaces=[Workspace.model_construct(id="ws-4j8p6jX1w33MiDC7")]
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(
            options, VariableSetRemoveFromWorkspacesOptions
        ):
            raise ValueError(
                "Options are required and must be VariableSetRemoveFromWorkspacesOptions"
            )

        if not options.workspaces:
            raise ValueError("At least one workspace is required")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/workspaces"

        # Build workspace relationships payload
        workspace_data = []
        for workspace in options.workspaces:
            if not workspace.id:
                raise ValueError("All workspaces must have valid IDs")
            workspace_data.append(
                {
                    "type": "workspaces",
                    "id": workspace.id,
                }
            )

        payload = {"data": workspace_data}

        self.t.request("DELETE", path, json_body=payload)

    def apply_to_projects(
        self,
        variable_set_id: str,
        options: VariableSetApplyToProjectsOptions,
    ) -> None:
        """Apply a non-global variable set to projects.

        This endpoint returns an API error when the variable set has ``global=True``.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The project relationship payload, as a
                :class:`VariableSetApplyToProjectsOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` is not a string, ``options`` is not a
                :class:`VariableSetApplyToProjectsOptions`, no projects are supplied,
                or any supplied project has no ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, VariableSetApplyToProjectsOptions
            >>> client.variable_sets.apply_to_projects(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetApplyToProjectsOptions(
            ...         projects=[Project.model_construct(id="prj-4j8p6jX1w33MiDC7")]
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetApplyToProjectsOptions):
            raise ValueError(
                "Options are required and must be VariableSetApplyToProjectsOptions"
            )

        if not options.projects:
            raise ValueError("At least one project is required")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/projects"

        # Build project relationships payload
        project_data = []
        for project in options.projects:
            if not project.id:
                raise ValueError("All projects must have valid IDs")
            project_data.append(
                {
                    "type": "projects",
                    "id": project.id,
                }
            )

        payload = {"data": project_data}

        self.t.request("POST", path, json_body=payload)

    def remove_from_projects(
        self,
        variable_set_id: str,
        options: VariableSetRemoveFromProjectsOptions,
    ) -> None:
        """Remove a non-global variable set from projects.

        This endpoint returns an API error when the variable set has ``global=True``.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The project relationship payload, as a
                :class:`VariableSetRemoveFromProjectsOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` is not a string, ``options`` is not a
                :class:`VariableSetRemoveFromProjectsOptions`, no projects are
                supplied, or any supplied project has no ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, VariableSetRemoveFromProjectsOptions
            >>> client.variable_sets.remove_from_projects(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetRemoveFromProjectsOptions(
            ...         projects=[Project.model_construct(id="prj-4j8p6jX1w33MiDC7")]
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetRemoveFromProjectsOptions):
            raise ValueError(
                "Options are required and must be VariableSetRemoveFromProjectsOptions"
            )

        if not options.projects:
            raise ValueError("At least one project is required")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/projects"

        # Build project relationships payload
        project_data = []
        for project in options.projects:
            if not project.id:
                raise ValueError("All projects must have valid IDs")
            project_data.append(
                {
                    "type": "projects",
                    "id": project.id,
                }
            )

        payload = {"data": project_data}

        self.t.request("DELETE", path, json_body=payload)

    def update_workspaces(
        self,
        variable_set_id: str,
        options: VariableSetUpdateWorkspacesOptions,
    ) -> VariableSet:
        """Replace the workspaces applied to a variable set.

        This forces the variable set to ``global=False`` and includes workspaces in the
        response.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The complete workspace list, as a
                :class:`VariableSetUpdateWorkspacesOptions`.

        Returns:
            The :class:`VariableSet`.

        Raises:
            ValueError: If ``variable_set_id`` is not a string or ``options`` is not a
                :class:`VariableSetUpdateWorkspacesOptions`.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetUpdateWorkspacesOptions, Workspace
            >>> varset = client.variable_sets.update_workspaces(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetUpdateWorkspacesOptions(
            ...         workspaces=[Workspace.model_construct(id="ws-4j8p6jX1w33MiDC7")]
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetUpdateWorkspacesOptions):
            raise ValueError(
                "Options are required and must be VariableSetUpdateWorkspacesOptions"
            )

        # Force inclusion of workspaces as that is the primary data
        path = f"/api/v2/varsets/{variable_set_id}"
        params: dict[str, str] = {"include": VariableSetIncludeOpt.WORKSPACES.value}

        payload = {
            "data": {
                "type": "varsets",
                "id": variable_set_id,
                "attributes": {
                    "global": False,  # Force global to false when applying to workspaces
                },
                "relationships": {
                    "workspaces": {
                        "data": [
                            {"type": "workspaces", "id": ws.id}
                            for ws in options.workspaces
                            if ws.id
                        ]
                    }
                },
            }
        }

        response = self.t.request("PATCH", path, json_body=payload, params=params)
        data = response.json()

        return self._parse_variable_set(data["data"])

    def _parse_variable_sets_response(
        self, data: dict[str, Any]
    ) -> builtins.list[VariableSet]:
        """Parse API response containing multiple variable sets.

        Args:
            data: Raw API response data

        Returns:
            List of VariableSet objects
        """
        variable_sets = []
        for item in data.get("data", []):
            variable_sets.append(self._parse_variable_set(item))
        return variable_sets

    def _parse_variable_set(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> VariableSet:
        """Parse a single variable set from API response data.

        Args:
            data: Raw API response data for a single variable set

        Returns:
            VariableSet object
        """
        attrs = data.get("attributes", {})
        relationships = data.get("relationships", {})

        # Build the data dict for Pydantic model
        parsed_data = {
            "id": data.get("id"),
            "name": attrs.get("name", ""),
            "description": attrs.get("description"),
            "global": attrs.get(
                "global", False
            ),  # Use "global" not "global_" for API data
            "priority": attrs.get("priority"),
            "created_at": attrs.get("created-at"),
            "updated_at": attrs.get("updated-at"),
        }

        # workspaces/projects/vars are id-only stubs by default and are filled
        # from the JSON:API ``included`` array when requested via ?include=.
        parsed_data.update(
            parse_relationships(relationships, _VARIABLE_SET_REL_MAP, included=included)
        )

        # Handle parent relationship (polymorphic: project | organization).
        parent = None
        if "parent" in relationships:
            parent_data = relationships["parent"].get("data")
            if parent_data:
                if parent_data.get("type") == "projects":
                    parent = {
                        "project": {
                            "id": parent_data["id"],
                            "name": f"project-{parent_data['id']}",
                        }
                    }
                elif parent_data.get("type") == "organizations":
                    parent = {"organization": {"id": parent_data["id"]}}
        parsed_data["parent"] = parent

        # Use Pydantic model validation to handle aliases properly
        return attach_jsonapi(VariableSet.model_validate(parsed_data), data, included)


class VariableSetVariables(_Service):
    """
    Variable Set Variables resource for managing variables within Variable Sets.

    This resource handles CRUD operations for individual variables within
    Variable Sets, providing scoped variable management capabilities.

    API Documentation:
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets#variable-relationships
    """

    def __init__(self, transport: HTTPTransport):
        """Initialize the Variable Set Variables resource.

        Args:
            transport: HTTP transport instance for API communication
        """
        super().__init__(transport)

    def list(
        self,
        variable_set_id: str,
        options: VariableSetVariableListOptions | None = None,
    ) -> Iterator[VariableSetVariable]:
        """List variables in a variable set.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: Optional pagination options, as a
                :class:`VariableSetVariableListOptions`.

        Returns:
            A single-use ``Iterator[VariableSetVariable]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``variable_set_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> for variable in client.variable_set_variables.list(
            ...     "varset-4j8p6jX1w33MiDC7"
            ... ):
            ...     print(variable.id, variable.key)
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars"
        params: dict[str, str] = {}

        if options:
            if options.page_size:
                params["page[size]"] = str(options.page_size)

        for item in self._list(path, params=params):
            yield self._parse_variable_set_variable(item)

    def create(
        self,
        variable_set_id: str,
        options: VariableSetVariableCreateOptions,
    ) -> VariableSetVariable:
        """Create a variable in a variable set.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            options: The variable configuration, as a
                :class:`VariableSetVariableCreateOptions`.

        Returns:
            The :class:`VariableSetVariable`.

        Raises:
            ValueError: If ``variable_set_id`` is not a string, ``options`` is not a
                :class:`VariableSetVariableCreateOptions`, ``options.key`` is blank, or
                ``options.category`` is blank.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CategoryType, VariableSetVariableCreateOptions
            >>> variable = client.variable_set_variables.create(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     VariableSetVariableCreateOptions(
            ...         key="AWS_REGION", value="us-east-1", category=CategoryType.ENV,
            ...     ),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not options or not isinstance(options, VariableSetVariableCreateOptions):
            raise ValueError(
                "Options are required and must be VariableSetVariableCreateOptions"
            )

        if not options.key:
            raise ValueError("Variable key is required")

        if not options.category:
            raise ValueError("Variable category is required")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars"

        payload: dict[str, Any] = {
            "data": {
                "type": "vars",
                "attributes": {
                    "key": options.key,
                    "category": options.category.value,
                },
            }
        }

        attributes = payload["data"]["attributes"]
        if options.value is not None:
            attributes["value"] = options.value

        if options.description is not None:
            attributes["description"] = options.description

        if options.hcl is not None:
            attributes["hcl"] = options.hcl

        if options.sensitive is not None:
            attributes["sensitive"] = options.sensitive

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()

        return self._parse_variable_set_variable(data["data"])

    def read(
        self,
        variable_set_id: str,
        variable_id: str,
    ) -> VariableSetVariable:
        """Read a variable from a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            The :class:`VariableSetVariable`.

        Raises:
            ValueError: If ``variable_set_id`` or ``variable_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> variable = client.variable_set_variables.read(
            ...     "varset-4j8p6jX1w33MiDC7", "var-4j8p6jX1w33MiDC7"
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not variable_id or not isinstance(variable_id, str):
            raise ValueError("Variable ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars/{variable_id}"

        response = self.t.request("GET", path)
        data = response.json()

        return self._parse_variable_set_variable(data["data"])

    def update(
        self,
        variable_set_id: str,
        variable_id: str,
        options: VariableSetVariableUpdateOptions,
    ) -> VariableSetVariable:
        """Update a variable in a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).
            options: The variable updates, as a
                :class:`VariableSetVariableUpdateOptions`.

        Returns:
            The :class:`VariableSetVariable`.

        Raises:
            ValueError: If ``variable_set_id`` or ``variable_id`` is not a string, or if
                ``options`` is not a :class:`VariableSetVariableUpdateOptions`.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VariableSetVariableUpdateOptions
            >>> variable = client.variable_set_variables.update(
            ...     "varset-4j8p6jX1w33MiDC7",
            ...     "var-4j8p6jX1w33MiDC7",
            ...     VariableSetVariableUpdateOptions(value="us-west-2"),
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not variable_id or not isinstance(variable_id, str):
            raise ValueError("Variable ID is required and must be a string")

        if not options or not isinstance(options, VariableSetVariableUpdateOptions):
            raise ValueError(
                "Options are required and must be VariableSetVariableUpdateOptions"
            )

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars/{variable_id}"

        payload: dict[str, Any] = {
            "data": {
                "type": "vars",
                "id": variable_id,
                "attributes": {},
            }
        }

        attributes = payload["data"]["attributes"]
        if options.key is not None:
            attributes["key"] = options.key

        if options.value is not None:
            attributes["value"] = options.value

        if options.description is not None:
            attributes["description"] = options.description

        if options.hcl is not None:
            attributes["hcl"] = options.hcl

        if options.sensitive is not None:
            attributes["sensitive"] = options.sensitive

        response = self.t.request("PATCH", path, json_body=payload)
        data = response.json()

        return self._parse_variable_set_variable(data["data"])

    def delete(
        self,
        variable_set_id: str,
        variable_id: str,
    ) -> None:
        """Delete a variable from a variable set by ID.

        Args:
            variable_set_id: The variable set ID (e.g. ``"varset-xxxxxxxx"``).
            variable_id: The variable ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``variable_set_id`` or ``variable_id`` is not a string.
            TFEError: If the API request fails.

        Example:
            >>> client.variable_set_variables.delete(
            ...     "varset-4j8p6jX1w33MiDC7", "var-4j8p6jX1w33MiDC7"
            ... )
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        if not variable_id or not isinstance(variable_id, str):
            raise ValueError("Variable ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars/{variable_id}"

        self.t.request("DELETE", path)

    def _parse_variable_set_variable(self, data: dict[str, Any]) -> VariableSetVariable:
        """Parse a single variable set variable from API response data.

        Args:
            data: Raw API response data for a single variable

        Returns:
            VariableSetVariable object
        """
        attrs = data.get("attributes", {})
        relationships = data.get("relationships", {})

        # Build the data dict for Pydantic model
        parsed_data = {
            "id": data.get("id"),
            "key": attrs.get("key", ""),
            "value": attrs.get("value"),
            "description": attrs.get("description"),
            "category": attrs.get("category", "terraform"),
            "hcl": attrs.get("hcl", False),
            "sensitive": attrs.get("sensitive", False),
            "version_id": attrs.get("version-id"),
        }

        # Handle variable set relationship
        variable_set = None
        if "varset" in relationships:
            vs_data = relationships["varset"].get("data")
            if vs_data and "id" in vs_data:
                variable_set = {
                    "id": vs_data["id"],
                    "name": f"varset-{vs_data['id']}",  # Placeholder name
                    "global": False,  # Placeholder global
                }
        parsed_data["variable_set"] = variable_set

        # Use Pydantic model validation
        return attach_jsonapi(VariableSetVariable.model_validate(parsed_data), data)
