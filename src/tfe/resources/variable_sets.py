"""Variable Set resource implementation for the Python TFE SDK."""

import builtins
from typing import Any

from tfe._http import HTTPTransport
from tfe.resources._base import _Service
from tfe.types import (
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
    ) -> list[VariableSet]:
        """List all variable sets within an organization.

        Args:
            organization: Organization name
            options: Optional parameters for filtering and pagination

        Returns:
            List of VariableSet objects

        Raises:
            ValueError: If organization name is invalid
            TFEError: If API request fails
        """
        if not organization or not isinstance(organization, str):
            raise ValueError("Organization name is required and must be a string")

        path = f"/api/v2/organizations/{organization}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()

        return self._parse_variable_sets_response(data)

    def list_for_workspace(
        self,
        workspace_id: str,
        options: VariableSetListOptions | None = None,
    ) -> builtins.list[VariableSet]:
        """List variable sets associated with a workspace.

        Args:
            workspace_id: Workspace ID
            options: Optional parameters for filtering and pagination

        Returns:
            List of VariableSet objects associated with the workspace

        Raises:
            ValueError: If workspace_id is invalid
            TFEError: If API request fails
        """
        if not workspace_id or not isinstance(workspace_id, str):
            raise ValueError("Workspace ID is required and must be a string")

        path = f"/api/v2/workspaces/{workspace_id}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()

        return self._parse_variable_sets_response(data)

    def list_for_project(
        self,
        project_id: str,
        options: VariableSetListOptions | None = None,
    ) -> builtins.list[VariableSet]:
        """List variable sets associated with a project.

        Args:
            project_id: Project ID
            options: Optional parameters for filtering and pagination

        Returns:
            List of VariableSet objects associated with the project

        Raises:
            ValueError: If project_id is invalid
            TFEError: If API request fails
        """
        if not project_id or not isinstance(project_id, str):
            raise ValueError("Project ID is required and must be a string")

        path = f"/api/v2/projects/{project_id}/varsets"
        params: dict[str, str] = {}

        if options:
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.query:
                params["q"] = options.query
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()

        return self._parse_variable_sets_response(data)

    def create(
        self,
        organization: str,
        options: VariableSetCreateOptions,
    ) -> VariableSet:
        """Create a new variable set.

        Args:
            organization: Organization name
            options: Variable set creation options

        Returns:
            Created VariableSet object

        Raises:
            ValueError: If organization name or options are invalid
            TFEError: If API request fails
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
        """Read a variable set by its ID.

        Args:
            variable_set_id: Variable set ID
            options: Optional parameters for including related resources

        Returns:
            VariableSet object

        Raises:
            ValueError: If variable_set_id is invalid
            TFEError: If API request fails
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}"
        params: dict[str, str] = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()

        return self._parse_variable_set(data["data"])

    def update(
        self,
        variable_set_id: str,
        options: VariableSetUpdateOptions,
    ) -> VariableSet:
        """Update an existing variable set.

        Args:
            variable_set_id: Variable set ID
            options: Variable set update options

        Returns:
            Updated VariableSet object

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Delete a variable set by its ID.

        Args:
            variable_set_id: Variable set ID

        Raises:
            ValueError: If variable_set_id is invalid
            TFEError: If API request fails
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
        """Apply variable set to workspaces.

        Note: This method will return an error if the variable set has global = true.

        Args:
            variable_set_id: Variable set ID
            options: Options specifying workspaces to apply to

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Remove variable set from workspaces.

        Note: This method will return an error if the variable set has global = true.

        Args:
            variable_set_id: Variable set ID
            options: Options specifying workspaces to remove from

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Apply variable set to projects.

        This method will return an error if the variable set has global = true.

        Args:
            variable_set_id: Variable set ID
            options: Options specifying projects to apply to

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Remove variable set from projects.

        This method will return an error if the variable set has global = true.

        Args:
            variable_set_id: Variable set ID
            options: Options specifying projects to remove from

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Update variable set to be applied to only the workspaces in the supplied list.

        Args:
            variable_set_id: Variable set ID
            options: Options specifying workspaces to apply to

        Returns:
            Updated VariableSet object

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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

    def _parse_variable_set(self, data: dict[str, Any]) -> VariableSet:
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

        # Build workspaces list - simplified to just contain minimal data
        workspaces = []
        if "workspaces" in relationships:
            ws_data = relationships["workspaces"].get("data", [])
            if isinstance(ws_data, list):
                for ws in ws_data:
                    if "id" in ws:
                        workspaces.append(
                            {
                                "id": ws["id"],
                                "name": f"workspace-{ws['id']}",  # Placeholder name
                                "organization": "placeholder-org",  # Placeholder organization
                            }
                        )
        parsed_data["workspaces"] = workspaces

        # Build projects list - simplified to just contain minimal data
        projects = []
        if "projects" in relationships:
            proj_data = relationships["projects"].get("data", [])
            if isinstance(proj_data, list):
                for proj in proj_data:
                    if "id" in proj:
                        projects.append(
                            {
                                "id": proj["id"],
                                "name": f"project-{proj['id']}",  # Placeholder name
                                "organization": "placeholder-org",  # Placeholder organization
                            }
                        )
        parsed_data["projects"] = projects

        # Build variables list - simplified to just contain minimal data
        variables = []
        if "vars" in relationships:
            vars_data = relationships["vars"].get("data", [])
            if isinstance(vars_data, list):
                for var in vars_data:
                    if "id" in var:
                        variables.append(
                            {
                                "id": var["id"],
                                "key": f"var-{var['id']}",  # Placeholder key
                                "category": "terraform",  # Default category
                                "variable_set": {
                                    "id": data.get("id"),
                                    "name": attrs.get("name", ""),
                                    "global": attrs.get("global", False),
                                },
                            }
                        )
        parsed_data["vars"] = variables

        # Handle parent relationship
        parent = None
        if "parent" in relationships:
            parent_data = relationships["parent"].get("data")
            if parent_data:
                if parent_data.get("type") == "projects":
                    parent = {
                        "project": {
                            "id": parent_data["id"],
                            "name": f"project-{parent_data['id']}",
                            "organization": "placeholder-org",
                        }
                    }
                elif parent_data.get("type") == "organizations":
                    parent = {"organization": {"id": parent_data["id"]}}
        parsed_data["parent"] = parent

        # Use Pydantic model validation to handle aliases properly
        return VariableSet.model_validate(parsed_data)


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
    ) -> list[VariableSetVariable]:
        """List all variables in a variable set.

        Args:
            variable_set_id: Variable set ID
            options: Optional parameters for pagination

        Returns:
            List of VariableSetVariable objects

        Raises:
            ValueError: If variable_set_id is invalid
            TFEError: If API request fails
        """
        if not variable_set_id or not isinstance(variable_set_id, str):
            raise ValueError("Variable set ID is required and must be a string")

        path = f"/api/v2/varsets/{variable_set_id}/relationships/vars"
        params: dict[str, str] = {}

        if options:
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)

        response = self.t.request("GET", path, params=params)
        data = response.json()

        variables = []
        for item in data.get("data", []):
            variables.append(self._parse_variable_set_variable(item))

        return variables

    def create(
        self,
        variable_set_id: str,
        options: VariableSetVariableCreateOptions,
    ) -> VariableSetVariable:
        """Create a new variable within a variable set.

        Args:
            variable_set_id: Variable set ID
            options: Variable creation options

        Returns:
            Created VariableSetVariable object

        Raises:
            ValueError: If variable_set_id or options are invalid
            TFEError: If API request fails
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
        """Read a variable by its ID.

        Args:
            variable_set_id: Variable set ID
            variable_id: Variable ID

        Returns:
            VariableSetVariable object

        Raises:
            ValueError: If variable_set_id or variable_id are invalid
            TFEError: If API request fails
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
        """Update an existing variable.

        Args:
            variable_set_id: Variable set ID
            variable_id: Variable ID
            options: Variable update options

        Returns:
            Updated VariableSetVariable object

        Raises:
            ValueError: If variable_set_id, variable_id or options are invalid
            TFEError: If API request fails
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
        """Delete a variable by its ID.

        Args:
            variable_set_id: Variable set ID
            variable_id: Variable ID

        Raises:
            ValueError: If variable_set_id or variable_id are invalid
            TFEError: If API request fails
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
        return VariableSetVariable.model_validate(parsed_data)
