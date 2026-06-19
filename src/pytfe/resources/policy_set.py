# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
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
from ..models.organization import Organization
from ..models.policy import Policy
from ..models.policy_set import (
    PolicySet,
    PolicySetAddPoliciesOptions,
    PolicySetAddProjectExclusionsOptions,
    PolicySetAddProjectsOptions,
    PolicySetAddWorkspaceExclusionsOptions,
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetListOptions,
    PolicySetReadOptions,
    PolicySetRemovePoliciesOptions,
    PolicySetRemoveProjectExclusionsOptions,
    PolicySetRemoveProjectsOptions,
    PolicySetRemoveWorkspaceExclusionsOptions,
    PolicySetRemoveWorkspacesOptions,
    PolicySetUpdateOptions,
)
from ..models.policy_set_version import PolicySetVersion
from ..models.project import Project
from ..models.workspace import Workspace
from ..utils import valid_string, valid_string_id
from ._base import _Service

# Wire relation name -> model; the python attr is derived as wire.replace("-","_"),
# which matches every PolicySet relation field. Threading ``included`` makes
# ?include= hydrate these typed fields (workspaces, projects, policies, versions,
# exclusions) instead of leaving id-only stubs.
_POLICY_SET_REL_MAP: RelationMap = {
    "organization": Organization,
    "workspaces": Workspace,
    "projects": Project,
    "policies": Policy,
    "newest-version": PolicySetVersion,
    "current-version": PolicySetVersion,
    "workspace-exclusions": Workspace,
    "project-exclusions": Project,
}


def _policy_set_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> PolicySet:
    """Parse a PolicySet, hydrating typed relations from ``included``."""
    attrs = dict(data.get("attributes", {}) or {})
    attrs["id"] = data.get("id")
    attrs.update(
        parse_relationships(
            data.get("relationships"), _POLICY_SET_REL_MAP, included=included
        )
    )
    return attach_jsonapi(PolicySet.model_validate(attrs), data, included)


class PolicySets(_Service):
    """
    PolicySets describes all the policy set related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets
    """

    def list(
        self, organization: str, options: PolicySetListOptions | None = None
    ) -> Iterator[PolicySet]:
        """List policy sets in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters, includes, and pagination, as a
                :class:`PolicySetListOptions`.

        Returns:
            A single-use ``Iterator[PolicySet]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for policy_set in client.policy_sets.list("my-org"):
            ...     print(policy_set.id, policy_set.name)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        # Build params from options but do not pass page[number] — let _list handle pagination.
        # mode="json" ensures enums (e.g. PolicySetIncludeOpt) serialize to
        # their string values rather than `'PolicySetIncludeOpt.FOO'` reprs.
        params = (
            options.model_dump(by_alias=True, exclude_none=True, mode="json")
            if options
            else {}
        )
        params.pop("page[number]", None)
        if isinstance(params.get("include"), list):
            params["include"] = ",".join(params["include"])

        path = f"/api/v2/organizations/{organization}/policy-sets"

        def _gen() -> Iterator[PolicySet]:
            for d in self._list(path, params=params):
                yield _policy_set_from(d)

        return _gen()

    def create(self, organization: str, options: PolicySetCreateOptions) -> PolicySet:
        """Create a policy set in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Policy set attributes and relationships, as a
                :class:`PolicySetCreateOptions`.

        Returns:
            The created :class:`PolicySet`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            RequiredNameError: If ``options.name`` is missing or empty.
            InvalidNameError: If ``options.name`` is not a valid policy set name.
            ValueError: If no attributes are provided for the policy set.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import PolicySetCreateOptions
            >>> policy_set = client.policy_sets.create(
            ...     "my-org",
            ...     PolicySetCreateOptions(name="baseline-policies"),
            ... )
        """
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
        return _policy_set_from(jd.get("data", {}), jd.get("included"))

    def read(self, policy_set_id: str) -> PolicySet:
        """Read a policy set by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).

        Returns:
            The :class:`PolicySet`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> policy_set = client.policy_sets.read("polset-123")
            >>> print(policy_set.name)
        """
        return self.read_with_options(policy_set_id)

    def read_with_options(
        self, policy_set_id: str, options: PolicySetReadOptions | None = None
    ) -> PolicySet:
        """Read a policy set by its ID with include options.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Optional include controls, as a :class:`PolicySetReadOptions`.

        Returns:
            The :class:`PolicySet`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import PolicySetReadOptions
            >>> policy_set = client.policy_sets.read_with_options(
            ...     "polset-123", PolicySetReadOptions()
            ... )
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        params: dict[str, Any] | None = None
        if options is not None:
            params = options.model_dump(by_alias=True, exclude_none=True, mode="json")
            if isinstance(params.get("include"), list):
                params["include"] = ",".join(params["include"])

        r = self.t.request(
            "GET",
            f"/api/v2/policy-sets/{policy_set_id}",
            params=params,
        )
        jd = r.json()
        return _policy_set_from(jd.get("data", {}), jd.get("included"))

    def update(self, policy_set_id: str, options: PolicySetUpdateOptions) -> PolicySet:
        """Update a policy set by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Policy set attributes to update, as a
                :class:`PolicySetUpdateOptions`.

        Returns:
            The updated :class:`PolicySet`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            ValueError: If no attributes are provided to update.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import PolicySetUpdateOptions
            >>> policy_set = client.policy_sets.update(
            ...     "polset-123", PolicySetUpdateOptions(description="Required checks")
            ... )
        """
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
        return _policy_set_from(jd.get("data", {}), jd.get("included"))

    def add_policies(
        self, policy_set_id: str, options: PolicySetAddPoliciesOptions
    ) -> None:
        """Add policies to a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetAddPoliciesOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            RequiredPoliciesError: If no policies are provided.
            InvalidPoliciesError: If the policy list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Policy, PolicySetAddPoliciesOptions
            >>> client.policy_sets.add_policies(
            ...     "polset-123", PolicySetAddPoliciesOptions(policies=[Policy(id="pol-123")])
            ... )
        """
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
        """Remove policies from a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetRemovePoliciesOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            RequiredPoliciesError: If no policies are provided.
            InvalidPoliciesError: If the policy list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Policy, PolicySetRemovePoliciesOptions
            >>> client.policy_sets.remove_policies(
            ...     "polset-123", PolicySetRemovePoliciesOptions(policies=[Policy(id="pol-123")])
            ... )
        """
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
        """Add workspaces to a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetAddWorkspacesOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            WorkspaceRequiredError: If no workspaces are provided.
            WorkspaceMinimumLimitError: If the workspace list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Workspace, PolicySetAddWorkspacesOptions
            >>> client.policy_sets.add_workspaces(
            ...     "polset-123", PolicySetAddWorkspacesOptions(workspaces=[Workspace(id="ws-123")])
            ... )
        """
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
        """Remove workspaces from a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetRemoveWorkspacesOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            WorkspaceRequiredError: If no workspaces are provided.
            WorkspaceMinimumLimitError: If the workspace list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Workspace, PolicySetRemoveWorkspacesOptions
            >>> client.policy_sets.remove_workspaces(
            ...     "polset-123", PolicySetRemoveWorkspacesOptions(workspaces=[Workspace(id="ws-123")])
            ... )
        """
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
        """Add workspace exclusions to a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetAddWorkspaceExclusionsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            WorkspaceRequiredError: If no workspaces are provided.
            WorkspaceMinimumLimitError: If the workspace list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Workspace, PolicySetAddWorkspaceExclusionsOptions
            >>> client.policy_sets.add_workspace_exclusions(
            ...     "polset-123", PolicySetAddWorkspaceExclusionsOptions(workspace_exclusions=[Workspace(id="ws-123")])
            ... )
        """
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
        """Remove workspace exclusions from a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetRemoveWorkspaceExclusionsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            WorkspaceRequiredError: If no workspaces are provided.
            WorkspaceMinimumLimitError: If the workspace list is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Workspace, PolicySetRemoveWorkspaceExclusionsOptions
            >>> client.policy_sets.remove_workspace_exclusions(
            ...     "polset-123", PolicySetRemoveWorkspaceExclusionsOptions(workspace_exclusions=[Workspace(id="ws-123")])
            ... )
        """
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

    def add_project_exclusions(
        self,
        policy_set_id: str,
        options: PolicySetAddProjectExclusionsOptions,
    ) -> None:
        """Add project exclusions to a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetAddProjectExclusionsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            ValueError: If no projects are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, PolicySetAddProjectExclusionsOptions
            >>> client.policy_sets.add_project_exclusions(
            ...     "polset-123", PolicySetAddProjectExclusionsOptions(project_exclusions=[Project(id="prj-123")])
            ... )
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        if not options.project_exclusions:
            raise ValueError("project_exclusions is required")
        payload = {
            "data": [
                {"id": project.id, "type": "projects"}
                for project in options.project_exclusions
            ]
        }
        self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/project-exclusions",
            json_body=payload,
        )
        return None

    def remove_project_exclusions(
        self,
        policy_set_id: str,
        options: PolicySetRemoveProjectExclusionsOptions,
    ) -> None:
        """Remove project exclusions from a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetRemoveProjectExclusionsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            ValueError: If no projects are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, PolicySetRemoveProjectExclusionsOptions
            >>> client.policy_sets.remove_project_exclusions(
            ...     "polset-123", PolicySetRemoveProjectExclusionsOptions(project_exclusions=[Project(id="prj-123")])
            ... )
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        if not options.project_exclusions:
            raise ValueError("project_exclusions is required")
        payload = {
            "data": [
                {"id": project.id, "type": "projects"}
                for project in options.project_exclusions
            ]
        }
        self.t.request(
            "DELETE",
            f"/api/v2/policy-sets/{policy_set_id}/relationships/project-exclusions",
            json_body=payload,
        )
        return None

    def add_projects(
        self, policy_set_id: str, options: PolicySetAddProjectsOptions
    ) -> None:
        """Add projects to a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetAddProjectsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            ValueError: If no projects are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, PolicySetAddProjectsOptions
            >>> client.policy_sets.add_projects(
            ...     "polset-123", PolicySetAddProjectsOptions(projects=[Project(id="prj-123")])
            ... )
        """
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
        """Remove projects from a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Relationship changes, as a :class:`PolicySetRemoveProjectsOptions`.

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            ValueError: If no projects are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, PolicySetRemoveProjectsOptions
            >>> client.policy_sets.remove_projects(
            ...     "polset-123", PolicySetRemoveProjectsOptions(projects=[Project(id="prj-123")])
            ... )
        """
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
        """Delete a policy set by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.policy_sets.delete("polset-123")
        """
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
