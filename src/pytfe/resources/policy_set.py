from __future__ import annotations

from ..errors import (
    InvalidNameError,
    InvalidOrgError,
    InvalidPoliciesError,
    InvalidPolicySetIDError,
    RequiredNameError,
    RequiredPoliciesError,
    WorkspaceMinimumLimitError,
    WorkspaceRequiredError,
)
from ..models.policy_set import (
    PolicySet,
    PolicySetAddPoliciesOptions,
    PolicySetAddProjectsOptions,
    PolicySetAddWorkspaceExclusionsOptions,
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetList,
    PolicySetListOptions,
    PolicySetReadOptions,
    PolicySetRemovePoliciesOptions,
    PolicySetRemoveProjectsOptions,
    PolicySetRemoveWorkspaceExclusionsOptions,
    PolicySetRemoveWorkspacesOptions,
    PolicySetUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


class PolicySets(_Service):
    """
    PolicySets describes all the policy set related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets
    """

    def list(
        self, organization: str, options: PolicySetListOptions | None = None
    ) -> PolicySetList:
        """List all the policy sets of the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/policy-sets",
            params=params,
        )
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            attrs["organization"] = d.get("relationships", {}).get("organization", {})
            attrs["workspace_exclusions"] = (
                d.get("relationships", {})
                .get("workspace-exclusions", {})
                .get("data", [])
            )
            attrs["workspaces"] = (
                d.get("relationships", {}).get("workspaces", {}).get("data", [])
            )
            attrs["projects"] = (
                d.get("relationships", {}).get("projects", {}).get("data", [])
            )
            attrs["policies"] = (
                d.get("relationships", {}).get("policies", {}).get("data", [])
            )
            items.append(PolicySet.model_validate(attrs))
        return PolicySetList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

    def create(self, organization: str, options: PolicySetCreateOptions) -> PolicySet:
        """Create a new policy set in the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string(options.name):
            raise RequiredNameError()
        if not valid_string_id(options.name):
            raise InvalidNameError()

        # Separate attributes from relationships
        options_dict = options.model_dump(by_alias=True, exclude_none=True)

        # Relationship fields that go under relationships
        relationship_fields = [
            "workspaces",
            "projects",
            "workspace-exclusions",
            "policies",
        ]
        relationships = {}
        attributes = {}

        for key, value in options_dict.items():
            if key in relationship_fields:
                # Convert the relationship data to the proper JSON:API format
                if value:  # Only add if not None/empty
                    relationships[key] = {
                        "data": [
                            {"id": item.id, "type": self._get_relationship_type(key)}
                            for item in value
                        ]
                    }
            else:
                attributes[key] = value

        if not attributes:
            raise ValueError("No attributes provided to create a policy set")

        payload = {
            "data": {
                "attributes": attributes,
                "type": "policy-sets",
            }
        }

        # Only add relationships if they exist
        if relationships:
            payload["data"]["relationships"] = relationships

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/policy-sets",
            json_body=payload,
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        # Handle relationships in response
        relationships_data = data.get("relationships", {})
        attrs["organization"] = relationships_data.get("organization", {})
        attrs["workspace_exclusions"] = relationships_data.get(
            "workspace-exclusions", {}
        ).get("data", [])
        attrs["workspaces"] = relationships_data.get("workspaces", {}).get("data", [])
        attrs["projects"] = relationships_data.get("projects", {}).get("data", [])
        attrs["policies"] = relationships_data.get("policies", {}).get("data", [])

        return PolicySet.model_validate(attrs)

    def read(self, policy_set_id: str) -> PolicySet:
        """Read a policy set by its ID."""
        return self.read_with_options(policy_set_id, None)

    def read_with_options(
        self, policy_set_id: str, options: PolicySetReadOptions | None = None
    ) -> PolicySet:
        """Read a policy set by its ID with additional options."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )

        r = self.t.request(
            "GET",
            f"/api/v2/policy-sets/{policy_set_id}",
            params=params,
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        # Handle relationships in response
        relationships_data = data.get("relationships", {})
        attrs["organization"] = relationships_data.get("organization", {})
        attrs["workspace_exclusions"] = relationships_data.get(
            "workspace-exclusions", {}
        ).get("data", [])
        attrs["workspaces"] = relationships_data.get("workspaces", {}).get("data", [])
        attrs["projects"] = relationships_data.get("projects", {}).get("data", [])
        attrs["policies"] = relationships_data.get("policies", {}).get("data", [])

        return PolicySet.model_validate(attrs)

    def update(self, policy_set_id: str, options: PolicySetUpdateOptions) -> PolicySet:
        """Update an existing policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        if not attrs:
            raise ValueError("No attributes provided to update the policy set")

        payload = {
            "data": {
                "attributes": attrs,
                "type": "policy-sets",
                "id": policy_set_id,
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/policy-sets/{policy_set_id}",
            json_body=payload,
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        # Handle relationships in response
        relationships_data = data.get("relationships", {})
        attrs["organization"] = relationships_data.get("organization", {})
        attrs["workspace_exclusions"] = relationships_data.get(
            "workspace-exclusions", {}
        ).get("data", [])
        attrs["workspaces"] = relationships_data.get("workspaces", {}).get("data", [])
        attrs["projects"] = relationships_data.get("projects", {}).get("data", [])
        attrs["policies"] = relationships_data.get("policies", {}).get("data", [])

        return PolicySet.model_validate(attrs)

    def add_policies(
        self, policy_set_id: str, options: PolicySetAddPoliciesOptions
    ) -> None:
        """Add policies to a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.policies:
            raise RequiredPoliciesError()

        if len(options.policies) == 0:
            raise InvalidPoliciesError()

        payload = {
            "data": [
                {"id": policy.id, "type": "policies"} for policy in options.policies
            ]
        }

        self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/policies",
            json_body=payload,
        )
        return None

    def remove_policies(
        self, policy_set_id: str, options: PolicySetRemovePoliciesOptions
    ) -> None:
        """Remove policies from a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.policies:
            raise RequiredPoliciesError()

        if len(options.policies) == 0:
            raise InvalidPoliciesError()

        payload = {
            "data": [
                {"id": policy.id, "type": "policies"} for policy in options.policies
            ]
        }

        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/policies",
            json_body=payload,
        )
        return None

    def add_workspaces(
        self, policy_set_id: str, options: PolicySetAddWorkspacesOptions
    ) -> None:
        """Add workspaces to a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.workspaces:
            raise WorkspaceRequiredError()

        if len(options.workspaces) == 0:
            raise WorkspaceMinimumLimitError()

        payload = {
            "data": [
                {"id": workspace.id, "type": "workspaces"}
                for workspace in options.workspaces
            ]
        }

        self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/workspaces",
            json_body=payload,
        )
        return None

    def remove_workspaces(
        self, policy_set_id: str, options: PolicySetRemoveWorkspacesOptions
    ) -> None:
        """Remove workspaces from a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.workspaces:
            raise WorkspaceRequiredError()

        if len(options.workspaces) == 0:
            raise WorkspaceMinimumLimitError()

        payload = {
            "data": [
                {"id": workspace.id, "type": "workspaces"}
                for workspace in options.workspaces
            ]
        }

        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/workspaces",
            json_body=payload,
        )
        return None

    def add_workspace_exclusions(
        self, policy_set_id: str, options: PolicySetAddWorkspaceExclusionsOptions
    ) -> None:
        """Add workspace exclusions to a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.workspace_exclusions:
            raise WorkspaceRequiredError()

        if len(options.workspace_exclusions) == 0:
            raise WorkspaceMinimumLimitError()

        payload = {
            "data": [
                {"id": workspace.id, "type": "workspaces"}
                for workspace in options.workspace_exclusions
            ]
        }

        self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/workspace-exclusions",
            json_body=payload,
        )
        return None

    def remove_workspace_exclusions(
        self, policy_set_id: str, options: PolicySetRemoveWorkspaceExclusionsOptions
    ) -> None:
        """Remove workspace exclusions from a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.workspace_exclusions:
            raise WorkspaceRequiredError()

        if len(options.workspace_exclusions) == 0:
            raise WorkspaceMinimumLimitError()

        payload = {
            "data": [
                {"id": workspace.id, "type": "workspaces"}
                for workspace in options.workspace_exclusions
            ]
        }

        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/workspace-exclusions",
            json_body=payload,
        )
        return None

    def add_projects(
        self, policy_set_id: str, options: PolicySetAddProjectsOptions
    ) -> None:
        """Add projects to a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.projects:
            raise ValueError("project is required")

        if len(options.projects) == 0:
            raise ValueError("must provide at least one project")

        payload = {
            "data": [
                {"id": project.id, "type": "projects"} for project in options.projects
            ]
        }

        self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/projects",
            json_body=payload,
        )
        return None

    def remove_projects(
        self, policy_set_id: str, options: PolicySetRemoveProjectsOptions
    ) -> None:
        """Remove projects from a policy set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not options.projects:
            raise ValueError("project is required")

        if len(options.projects) == 0:
            raise ValueError("must provide at least one project")

        payload = {
            "data": [
                {"id": project.id, "type": "projects"} for project in options.projects
            ]
        }

        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/projects",
            json_body=payload,
        )
        return None

    def delete(self, policy_set_id: str) -> None:
        """Delete a policy set by its ID."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}",
        )
        return None

    def _get_relationship_type(self, field_name: str) -> str:
        """Get the JSON:API type for relationship fields."""
        type_mapping = {
            "workspaces": "workspaces",
            "projects": "projects",
            "workspace-exclusions": "workspaces",
            "policies": "policies",
        }
        return type_mapping.get(field_name, field_name)
