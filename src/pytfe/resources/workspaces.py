# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from pytfe.models.ssh_key import SSHKey

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceValueError,
    MissingTagBindingIdentifierError,
    MissingTagIdentifierError,
    RequiredSSHKeyIDError,
    WorkspaceLockedStateVersionStillPending,
    WorkspaceMinimumLimitError,
    WorkspaceRequiredError,
)
from ..models.agent import AgentPool
from ..models.assessment_result import AssessmentResult
from ..models.common import (
    EffectiveTagBinding,
    Tag,
    TagBinding,
)
from ..models.configuration_version import ConfigurationVersion
from ..models.data_retention_policy import (
    DataRetentionPolicy,
    DataRetentionPolicyChoice,
    DataRetentionPolicyDeleteOlder,
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDelete,
    DataRetentionPolicySetOptions,
)
from ..models.organization import Organization
from ..models.project import Project
from ..models.run import Run
from ..models.state_version import StateVersion
from ..models.variable import Variable
from ..models.workspace import (
    ExecutionMode,
    LockedByChoice,
    VCSRepo,
    Workspace,
    WorkspaceActions,
    WorkspaceAddRemoteStateConsumersOptions,
    WorkspaceAddTagBindingsOptions,
    WorkspaceAddTagsOptions,
    WorkspaceAssignSSHKeyOptions,
    WorkspaceCreateOptions,
    WorkspaceListOptions,
    WorkspaceListRemoteStateConsumersOptions,
    WorkspaceLockOptions,
    WorkspaceOutputs,
    WorkspacePermissions,
    WorkspaceReadOptions,
    WorkspaceRemoveRemoteStateConsumersOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceSettingOverwrites,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
    WorkspaceUpdateRemoteStateConsumersOptions,
)
from ..utils import (
    valid_string,
    valid_string_id,
)
from ._base import _Service

# Declarative relationship map: wire relation name -> model (attr derived as
# wire.replace("-", "_")), or an explicit (attr, model) tuple where they diverge.
# Only the genuinely polymorphic relations (locked-by, data-retention-policy-choice,
# whose target model depends on the reference ``type``) are handled as special
# cases in ``_ws_from`` and intentionally left out of this map.
_WORKSPACE_REL_MAP: RelationMap = {
    "organization": Organization,
    "project": Project,
    "ssh-key": SSHKey,
    "agent-pool": AgentPool,
    "current-run": Run,
    "latest-run": Run,
    "current-configuration-version": ConfigurationVersion,
    "current-state-version": StateVersion,
    "current-assessment-result": AssessmentResult,
    "remote-state-consumers": Workspace,
    "vars": ("variables", Variable),  # wire name diverges from attr
    # outputs is a JSON:API relation whose attributes live in the ``included``
    # array (matching go-tfe's `jsonapi:"relation,outputs"`); hydrate it via the
    # shared path so ?include=outputs populates name/value/type (python-tfe#134).
    "outputs": WorkspaceOutputs,
}


def _em_safe(v: Any) -> ExecutionMode | None:
    # Only accept strings; map to enum if known, else None
    if not isinstance(v, str):
        return None
    result = ExecutionMode._value2member_map_.get(v)
    return result if isinstance(result, ExecutionMode) else None


def _ws_from(
    d: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> Workspace:
    attr: dict[str, Any] = dict(d.get("attributes") or {})
    relationships: dict[str, Any] = d.get("relationships", {}) or {}

    # Optional fields
    em: ExecutionMode | None = _em_safe(attr.get("execution-mode"))

    actions = None
    if attr.get("actions"):
        actions = WorkspaceActions.model_validate(attr["actions"])

    permissions = None
    if attr.get("permissions"):
        permissions = WorkspacePermissions.model_validate(attr["permissions"])

    setting_overwrites = None
    if attr.get("setting-overwrites"):
        setting_overwrites = WorkspaceSettingOverwrites.model_validate(
            attr["setting-overwrites"]
        )

    # Map VCS repo
    vcs_repo = None
    if attr.get("vcs-repo"):
        vcs_repo = VCSRepo.model_validate(attr["vcs-repo"])

    # Map locked_by choice
    locked_by = None
    if relationships.get("locked-by", {}).get("data"):
        lb_data = relationships["locked-by"]["data"]
        if lb_data:
            if lb_data.get("type") == "runs":
                locked_by = LockedByChoice.model_validate({"run": lb_data.get("id")})
            elif lb_data.get("type") == "users":
                locked_by = LockedByChoice.model_validate({"user": lb_data.get("id")})
            elif lb_data.get("type") == "teams":
                locked_by = LockedByChoice.model_validate({"team": lb_data.get("id")})

    data_retention_policy_choice: DataRetentionPolicyChoice | None = None
    if relationships.get("data-retention-policy-choice", {}).get("data"):
        drp_data = relationships["data-retention-policy-choice"]["data"]
        if drp_data:
            if drp_data.get("type") == "data-retention-policy-delete-olders":
                data_retention_policy_delete_older = (
                    DataRetentionPolicyDeleteOlder.model_validate(
                        {
                            "id": drp_data.get("id"),
                            "delete_older_than_n_days": drp_data.get(
                                "attributes", {}
                            ).get("delete-older-than-n-days", 0),
                        }
                    )
                )
                data_retention_policy_choice = DataRetentionPolicyChoice.model_validate(
                    {
                        "data_retention_policy_delete_older": data_retention_policy_delete_older
                    }
                )
            elif drp_data.get("type") == "data-retention-policy-dont-deletes":
                data_retention_policy_dont_delete = (
                    DataRetentionPolicyDontDelete.model_validate(
                        {"id": drp_data.get("id")}
                    )
                )
                data_retention_policy_choice = DataRetentionPolicyChoice.model_validate(
                    {
                        "data_retention_policy_dont_delete": data_retention_policy_dont_delete
                    }
                )
            elif drp_data.get("type") == "data-retention-policies":
                # Legacy data retention policy
                data_retention_policy = DataRetentionPolicy.model_validate(
                    {
                        "id": drp_data.get("id"),
                        "delete_older_than_n_days": drp_data.get("attributes", {}).get(
                            "delete-older-than-n-days", 0
                        ),
                    }
                )
                data_retention_policy_choice = DataRetentionPolicyChoice.model_validate(
                    {"data_retention_policy": data_retention_policy}
                )

    attr["id"] = d.get("id")
    # Overwrite the raw wire string with the coerced enum (unknown values -> None).
    attr["execution-mode"] = em
    attr["actions"] = actions
    attr["permissions"] = permissions
    # Use alias keys consistently so the pre-built objects overwrite the raw wire
    # dicts rather than leaving a duplicate that extra="allow" would leak.
    attr["setting-overwrites"] = setting_overwrites
    attr["vcs-repo"] = vcs_repo

    # Generic relations: declarative map + optional ``included`` hydration.
    attr.update(
        parse_relationships(relationships, _WORKSPACE_REL_MAP, included=included)
    )

    # Special-case (polymorphic) relations that don't fit the generic map.
    attr["locked_by"] = locked_by
    attr["data_retention_policy_choice"] = data_retention_policy_choice

    # Keep the raw relationships + included so related resources we don't model
    # are never lost (reachable via ws.relationships / ws.included / ws.related).
    return attach_jsonapi(Workspace.model_validate(attr), d, included)


class Workspaces(_Service):
    def list(
        self,
        organization: str,
        options: WorkspaceListOptions | None = None,
    ) -> Iterator[Workspace]:
        """List workspaces in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional filters and includes, as a :class:`WorkspaceListOptions`.

        Returns:
            A single-use ``Iterator[Workspace]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceListOptions
            >>> for workspace in client.workspaces.list(
            ...     "my-org", WorkspaceListOptions(search="prod")
            ... ):
            ...     print(workspace.id, workspace.name)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params = (
            options.model_dump(
                by_alias=True, exclude_none=True, exclude={"tag_bindings"}
            )
            if options
            else {}
        )

        if options is not None:
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])

            if options.tag_bindings:
                for i, binding in enumerate(options.tag_bindings):
                    if binding.key and binding.value:
                        params[f"filter[tagged][{i}][key]"] = binding.key
                        params[f"filter[tagged][{i}][value]"] = binding.value
                    elif binding.key:
                        params[f"filter[tagged][{i}][key]"] = binding.key

        path = f"/api/v2/organizations/{organization}/workspaces"
        for item in self._list(path, params=params):
            yield _ws_from(item)

    def read(self, workspace: str, *, organization: str) -> Workspace:
        """Read a workspace by organization and name.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`Workspace`.

        Raises:
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.read(
            ...     "example-workspace", organization="my-org"
            ... )
            >>> print(workspace.id)
        """
        return self.read_with_options(workspace, organization=organization)

    def read_with_options(
        self,
        workspace: str,
        options: WorkspaceReadOptions | None = None,
        *,
        organization: str,
    ) -> Workspace:
        """Read a workspace by organization and name with include options.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            options: Optional related resources, as a :class:`WorkspaceReadOptions`.
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`Workspace`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceIncludeOpt, WorkspaceReadOptions
            >>> workspace = client.workspaces.read_with_options(
            ...     "example-workspace",
            ...     WorkspaceReadOptions(include=[WorkspaceIncludeOpt.PROJECT]),
            ...     organization="my-org",
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        params: dict[str, Any] = {}
        if options is not None:
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/workspaces/{workspace}",
            params=params,
        )
        payload = r.json()
        ws = _ws_from(payload["data"], payload.get("included"))
        ws.data_retention_policy = (
            ws.data_retention_policy_choice.convert_to_legacy_struct()
            if ws.data_retention_policy_choice
            else None
        )
        return ws

    def read_by_id(self, workspace_id: str) -> Workspace:
        """Read a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.read_by_id("ws-abc123def456")
            >>> print(workspace.name)
        """
        return self.read_by_id_with_options(workspace_id)

    def read_by_id_with_options(
        self, workspace_id: str, options: WorkspaceReadOptions | None = None
    ) -> Workspace:
        """Read a workspace by workspace ID with include options.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: Optional related resources, as a :class:`WorkspaceReadOptions`.

        Returns:
            The :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceIncludeOpt, WorkspaceReadOptions
            >>> workspace = client.workspaces.read_by_id_with_options(
            ...     "ws-abc123def456",
            ...     WorkspaceReadOptions(include=[WorkspaceIncludeOpt.OUTPUTS]),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}
        if options is not None:
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", f"/api/v2/workspaces/{workspace_id}", params=params)
        payload = r.json()
        ws = _ws_from(payload["data"], payload.get("included"))
        if ws.data_retention_policy_choice is not None:
            ws.data_retention_policy = (
                ws.data_retention_policy_choice.convert_to_legacy_struct()
            )
        return ws

    def create(
        self,
        organization: str,
        options: WorkspaceCreateOptions,
    ) -> Workspace:
        """Create a workspace in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The workspace settings, as a :class:`WorkspaceCreateOptions`.

        Returns:
            The created :class:`Workspace`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceCreateOptions
            >>> workspace = client.workspaces.create(
            ...     "my-org", WorkspaceCreateOptions(name="example-workspace")
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        body = self._build_workspace_payload(options)
        r = self.t.request(
            "POST", f"/api/v2/organizations/{organization}/workspaces", json_body=body
        )
        return _ws_from(r.json()["data"])

    def update(
        self, workspace: str, options: WorkspaceUpdateOptions, *, organization: str
    ) -> Workspace:
        """Update a workspace by organization and name.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            options: The workspace changes, as a :class:`WorkspaceUpdateOptions`.
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceUpdateOptions
            >>> workspace = client.workspaces.update(
            ...     "example-workspace",
            ...     WorkspaceUpdateOptions(description="Managed by pytfe."),
            ...     organization="my-org",
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        body = self._build_workspace_payload(options)
        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/workspaces/{workspace}",
            json_body=body,
        )
        return _ws_from(r.json()["data"])

    def update_by_id(
        self, workspace_id: str, options: WorkspaceUpdateOptions
    ) -> Workspace:
        """Update a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The workspace changes, as a :class:`WorkspaceUpdateOptions`.

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceUpdateOptions
            >>> workspace = client.workspaces.update_by_id(
            ...     "ws-abc123def456", WorkspaceUpdateOptions(auto_apply=True)
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = self._build_workspace_payload(options)
        r = self.t.request(
            "PATCH", f"/api/v2/workspaces/{workspace_id}", json_body=body
        )
        return _ws_from(r.json()["data"])

    def _build_workspace_payload(
        self, options: WorkspaceCreateOptions | WorkspaceUpdateOptions
    ) -> dict[str, Any]:
        """Build the workspace payload from options following API specification.

        Args:
            options: Either WorkspaceCreateOptions or WorkspaceUpdateOptions
        """
        attrs = (
            (
                options.model_dump(
                    by_alias=True,
                    exclude_none=True,
                    exclude={
                        "vcs_repo",
                        "setting_overwrites",
                        "project",
                        "tag_bindings",
                    },
                )
            )
            if options
            else {}
        )

        # VCS repository configuration
        if hasattr(options, "vcs_repo"):
            vcs_data = (
                (options.vcs_repo.model_dump(by_alias=True, exclude_none=True))
                if options.vcs_repo
                else {}
            )
            attrs["vcs-repo"] = vcs_data

        # Setting overwrites
        if hasattr(options, "setting_overwrites"):
            setting_overwrites = (
                (
                    options.setting_overwrites.model_dump(
                        by_alias=True, exclude_none=True
                    )
                )
                if options.setting_overwrites
                else {}
            )
            attrs["setting-overwrites"] = setting_overwrites

        body = {"data": {"type": "workspaces", "attributes": attrs}}

        # Add relationships
        relationships: dict[str, Any] = {}

        if hasattr(options, "project") and options.project and options.project.id:
            relationships["project"] = {
                "data": {"type": "projects", "id": options.project.id}
            }

        if hasattr(options, "tag_bindings") and options.tag_bindings:
            relationships["tag-bindings"] = {"data": []}
            for binding in options.tag_bindings:
                if binding.key and binding.value:
                    tag_binding_data = {
                        "type": "tag-bindings",
                        "attributes": {
                            "key": binding.key,
                            "value": binding.value,
                        },
                    }
                    relationships["tag-bindings"]["data"].append(tag_binding_data)

        if relationships:
            body["data"]["relationships"] = relationships

        return body

    def delete(self, workspace: str, *, organization: str) -> None:
        """Delete a workspace by organization and name.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            None.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.delete("example-workspace", organization="my-org")
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        self.t.request(
            "DELETE", f"/api/v2/organizations/{organization}/workspaces/{workspace}"
        )
        return None

    def delete_by_id(self, workspace_id: str) -> None:
        """Delete a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.delete_by_id("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        self.t.request("DELETE", f"/api/v2/workspaces/{workspace_id}")
        return None

    def safe_delete(self, workspace: str, *, organization: str) -> None:
        """Safely delete a workspace by organization and name.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            None.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.safe_delete(
            ...     "example-workspace", organization="my-org"
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/workspaces/{workspace}/actions/safe-delete",
        )
        return None

    def safe_delete_by_id(self, workspace_id: str) -> None:
        """Safely delete a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.safe_delete_by_id("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        self.t.request("POST", f"/api/v2/workspaces/{workspace_id}/actions/safe-delete")
        return None

    def remove_vcs_connection(
        self,
        workspace: str,
        *,
        organization: str | None = None,
    ) -> Workspace:
        """Remove the VCS connection from a workspace by name.

        Args:
            workspace: The workspace name (e.g. ``"example-workspace"``).
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            InvalidWorkspaceValueError: If ``workspace`` is not a valid workspace name.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.remove_vcs_connection(
            ...     "example-workspace", organization="my-org"
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        body = {
            "data": {
                "type": "workspaces",
                "attributes": {"vcs-repo": None},
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/workspaces/{workspace}",
            json_body=body,
        )
        return _ws_from(r.json()["data"])

    def remove_vcs_connection_by_id(self, workspace_id: str) -> Workspace:
        """Remove the VCS connection from a workspace by ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.remove_vcs_connection_by_id(
            ...     "ws-abc123def456"
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "workspaces",
                "attributes": {"vcs-repo": None},
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}",
            json_body=body,
        )
        return _ws_from(r.json()["data"])

    def lock(self, workspace_id: str, options: WorkspaceLockOptions) -> Workspace:
        """Lock a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The lock reason, as a :class:`WorkspaceLockOptions`.

        Returns:
            The locked :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceLockOptions
            >>> workspace = client.workspaces.lock(
            ...     "ws-abc123def456", WorkspaceLockOptions(reason="Maintenance")
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {"reason": options.reason}

        r = self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/actions/lock",
            json_body=body,
        )
        return _ws_from(r.json()["data"])

    def unlock(self, workspace_id: str) -> Workspace:
        """Unlock a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The unlocked :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            WorkspaceLockedStateVersionStillPending: If the latest state version is
                pending.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.unlock("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        try:
            r = self.t.request(
                "POST",
                f"/api/v2/workspaces/{workspace_id}/actions/unlock",
            )
            return _ws_from(r.json()["data"])
        except Exception as e:
            if "latest state version is still pending" in str(e):
                raise WorkspaceLockedStateVersionStillPending(str(e)) from e
            raise

    def force_unlock(self, workspace_id: str) -> Workspace:
        """Force unlock a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The unlocked :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.force_unlock("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        r = self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/actions/force-unlock",
        )
        return _ws_from(r.json()["data"])

    def assign_ssh_key(
        self, workspace_id: str, options: WorkspaceAssignSSHKeyOptions
    ) -> Workspace:
        """Assign an SSH key to a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The SSH key ID, as a :class:`WorkspaceAssignSSHKeyOptions`.

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            RequiredSSHKeyIDError: If ``options.ssh_key_id`` is empty.
            InvalidSSHKeyIDError: If ``options.ssh_key_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import WorkspaceAssignSSHKeyOptions
            >>> workspace = client.workspaces.assign_ssh_key(
            ...     "ws-abc123def456",
            ...     WorkspaceAssignSSHKeyOptions(ssh_key_id="sshkey-123"),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        if not valid_string(options.ssh_key_id):
            raise RequiredSSHKeyIDError()

        if not valid_string_id(options.ssh_key_id):
            raise InvalidSSHKeyIDError()

        body = {
            "data": {
                "type": "workspaces",
                "attributes": {"id": options.ssh_key_id},
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/relationships/ssh-key",
            json_body=body,
        )
        return _ws_from(r.json()["data"])

    def unassign_ssh_key(self, workspace_id: str) -> Workspace:
        """Unassign the SSH key from a workspace by workspace ID.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The updated :class:`Workspace`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> workspace = client.workspaces.unassign_ssh_key("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "workspaces",
                "attributes": {"id": None},
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/relationships/ssh-key",
            json_body=body,
        )

        return _ws_from(r.json()["data"])

    def list_remote_state_consumers(
        self,
        workspace_id: str,
        options: WorkspaceListRemoteStateConsumersOptions | None = None,
    ) -> Iterator[Workspace]:
        """List remote-state consumers for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: Optional pagination, as a
                :class:`WorkspaceListRemoteStateConsumersOptions`.

        Returns:
            A single-use ``Iterator[Workspace]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for consumer in client.workspaces.list_remote_state_consumers(
            ...     "ws-abc123def456"
            ... ):
            ...     print(consumer.id)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        path = f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers"
        for item in self._list(path, params=params):
            yield _ws_from(item)

    def add_remote_state_consumers(
        self, workspace_id: str, options: WorkspaceAddRemoteStateConsumersOptions
    ) -> None:
        """Add remote-state consumers to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The consumer workspaces, as a
                :class:`WorkspaceAddRemoteStateConsumersOptions`.

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            WorkspaceRequiredError: If ``options.workspaces`` is ``None``.
            WorkspaceMinimumLimitError: If ``options.workspaces`` is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import (
            ...     Workspace,
            ...     WorkspaceAddRemoteStateConsumersOptions,
            ... )
            >>> client.workspaces.add_remote_state_consumers(
            ...     "ws-abc123def456",
            ...     WorkspaceAddRemoteStateConsumersOptions(
            ...         workspaces=[Workspace(id="ws-456")]
            ...     ),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if options.workspaces is None:
            raise WorkspaceRequiredError()
        if len(options.workspaces) == 0:
            raise WorkspaceMinimumLimitError()

        body = {
            "data": [{"type": "workspaces", "id": ws.id} for ws in options.workspaces]
        }
        self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers",
            json_body=body,
        )
        return None

    def remove_remote_state_consumers(
        self, workspace_id: str, options: WorkspaceRemoveRemoteStateConsumersOptions
    ) -> None:
        """Remove remote-state consumers from a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The consumer workspaces, as a
                :class:`WorkspaceRemoveRemoteStateConsumersOptions`.

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            WorkspaceRequiredError: If ``options.workspaces`` is ``None``.
            WorkspaceMinimumLimitError: If ``options.workspaces`` is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import (
            ...     Workspace,
            ...     WorkspaceRemoveRemoteStateConsumersOptions,
            ... )
            >>> client.workspaces.remove_remote_state_consumers(
            ...     "ws-abc123def456",
            ...     WorkspaceRemoveRemoteStateConsumersOptions(
            ...         workspaces=[Workspace(id="ws-456")]
            ...     ),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if options.workspaces is None:
            raise WorkspaceRequiredError()
        if len(options.workspaces) == 0:
            raise WorkspaceMinimumLimitError()
        body = {
            "data": [{"type": "workspaces", "id": ws.id} for ws in options.workspaces]
        }
        self.t.request(
            "DELETE",
            f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers",
            json_body=body,
        )
        return None

    def update_remote_state_consumers(
        self, workspace_id: str, options: WorkspaceUpdateRemoteStateConsumersOptions
    ) -> None:
        """Replace remote-state consumers for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The complete consumer set, as a
                :class:`WorkspaceUpdateRemoteStateConsumersOptions`.

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            WorkspaceRequiredError: If ``options.workspaces`` is ``None``.
            WorkspaceMinimumLimitError: If ``options.workspaces`` is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import (
            ...     Workspace,
            ...     WorkspaceUpdateRemoteStateConsumersOptions,
            ... )
            >>> client.workspaces.update_remote_state_consumers(
            ...     "ws-abc123def456",
            ...     WorkspaceUpdateRemoteStateConsumersOptions(
            ...         workspaces=[Workspace(id="ws-456")]
            ...     ),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if options.workspaces is None:
            raise WorkspaceRequiredError()
        if len(options.workspaces) == 0:
            raise WorkspaceMinimumLimitError()
        body = {
            "data": [{"type": "workspaces", "id": ws.id} for ws in options.workspaces]
        }
        self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers",
            json_body=body,
        )
        return None

    def list_tags(
        self, workspace_id: str, options: WorkspaceTagListOptions | None = None
    ) -> Iterator[Tag]:
        """List tags attached to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: Optional pagination and name filtering, as a
                :class:`WorkspaceTagListOptions`.

        Returns:
            A single-use ``Iterator[Tag]``. Wrap with ``list(...)`` to materialize the
            results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for tag in client.workspaces.list_tags("ws-abc123def456"):
            ...     print(tag.id, tag.name)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        path = f"/api/v2/workspaces/{workspace_id}/relationships/tags"
        for item in self._list(path, params=params):
            attr = item.get("attributes", {}) or {}
            yield Tag(id=item.get("id"), name=attr.get("name", ""))

    def add_tags(self, workspace_id: str, options: WorkspaceAddTagsOptions) -> None:
        """Add tags to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The tags to add, as a :class:`WorkspaceAddTagsOptions`.

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            MissingTagIdentifierError: If no tag has an ID or name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Tag, WorkspaceAddTagsOptions
            >>> client.workspaces.add_tags(
            ...     "ws-abc123def456", WorkspaceAddTagsOptions(tags=[Tag(name="prod")])
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if len(options.tags) == 0:
            raise MissingTagIdentifierError()
        for tag in options.tags:
            if tag.id == "" and tag.name == "":
                raise MissingTagIdentifierError()
        data: list[dict[str, Any]] = []
        for tag in options.tags:
            if tag.id:
                data.append({"type": "tags", "id": tag.id})
            else:
                data.append({"type": "tags", "attributes": {"name": tag.name}})
        body = {"data": data}
        self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/relationships/tags",
            json_body=body,
        )
        return None

    def remove_tags(
        self, workspace_id: str, options: WorkspaceRemoveTagsOptions
    ) -> None:
        """Remove tags from a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The tags to remove, as a :class:`WorkspaceRemoveTagsOptions`.

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            MissingTagIdentifierError: If no tag has an ID or name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Tag, WorkspaceRemoveTagsOptions
            >>> client.workspaces.remove_tags(
            ...     "ws-abc123def456",
            ...     WorkspaceRemoveTagsOptions(tags=[Tag(name="prod")]),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if len(options.tags) == 0:
            raise MissingTagIdentifierError()
        for tag in options.tags:
            if tag.id == "" and tag.name == "":
                raise MissingTagIdentifierError()
        data: list[dict[str, Any]] = []
        for tag in options.tags:
            if tag.id:
                data.append({"type": "tags", "id": tag.id})
            else:
                data.append({"type": "tags", "attributes": {"name": tag.name}})
        body = {"data": data}
        self.t.request(
            "DELETE",
            f"/api/v2/workspaces/{workspace_id}/relationships/tags",
            json_body=body,
        )
        return None

    def list_tag_bindings(self, workspace_id: str) -> Iterator[TagBinding]:
        """List tag bindings attached to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            A single-use ``Iterator[TagBinding]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> bindings = list(client.workspaces.list_tag_bindings("ws-abc123def456"))
            >>> print(bindings[0].key)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        # tag-bindings is not paginated.
        path = f"/api/v2/workspaces/{workspace_id}/tag-bindings"
        for item in self._list(path, paginated=False):
            attr = item.get("attributes", {}) or {}
            yield TagBinding(
                id=item.get("id"),
                key=attr.get("key", ""),
                value=attr.get("value", ""),
            )

    def list_effective_tag_bindings(
        self, workspace_id: str
    ) -> Iterator[EffectiveTagBinding]:
        """List effective tag bindings for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            A single-use ``Iterator[EffectiveTagBinding]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for binding in client.workspaces.list_effective_tag_bindings(
            ...     "ws-abc123def456"
            ... ):
            ...     print(binding.key, binding.value)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        # effective-tag-bindings is not paginated.
        path = f"/api/v2/workspaces/{workspace_id}/effective-tag-bindings"
        for item in self._list(path, paginated=False):
            attr = item.get("attributes", {}) or {}
            yield EffectiveTagBinding(
                id=item.get("id", ""),
                key=attr.get("key", ""),
                value=attr.get("value", ""),
                links=attr.get("links", {}),
            )

    def add_tag_bindings(
        self, workspace_id: str, options: WorkspaceAddTagBindingsOptions
    ) -> Iterator[TagBinding]:
        """Add or update tag bindings on a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The tag bindings, as a :class:`WorkspaceAddTagBindingsOptions`.

        Returns:
            A single-use ``Iterator[TagBinding]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            MissingTagBindingIdentifierError: If no tag bindings are provided.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import TagBinding, WorkspaceAddTagBindingsOptions
            >>> bindings = client.workspaces.add_tag_bindings(
            ...     "ws-abc123def456",
            ...     WorkspaceAddTagBindingsOptions(
            ...         tag_bindings=[TagBinding(key="env", value="prod")]
            ...     ),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if len(options.tag_bindings) == 0:
            raise MissingTagBindingIdentifierError()
        data: list[dict[str, Any]] = []
        for binding in options.tag_bindings:
            data.append(
                {
                    "type": "tag-bindings",
                    "attributes": {"key": binding.key, "value": binding.value},
                }
            )
        body = {"data": data}
        r = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/tag-bindings",
            json_body=body,
        )
        out: builtins.list[TagBinding] = []
        for item in r.json().get("data", []):
            attr = item.get("attributes", {}) or {}
            out.append(
                TagBinding(
                    id=item.get("id"),
                    key=attr.get("key", ""),
                    value=attr.get("value", ""),
                )
            )
        return iter(out)

    def delete_all_tag_bindings(self, workspace_id: str) -> None:
        """Delete all tag bindings from a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.delete_all_tag_bindings("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "workspaces",
                "id": workspace_id,
                "relationships": {"tag-bindings": {"data": []}},
            }
        }
        self.t.request("PATCH", f"/api/v2/workspaces/{workspace_id}", json_body=body)
        return None

    def read_data_retention_policy(
        self, workspace_id: str
    ) -> DataRetentionPolicy | None:
        """Read a workspace's deprecated data retention policy.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The :class:`DataRetentionPolicy`, or ``None`` if the relationship
            has no data.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            ValueError: If the deprecated policy endpoint should not be used.
            TFEError: If the API request fails.

        Example:
            >>> policy = client.workspaces.read_data_retention_policy("ws-abc123def456")
            >>> print(policy.delete_older_than_n_days if policy else "none")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        try:
            r = self.t.request("GET", self._data_retention_policy_link(workspace_id))
            d = r.json().get("data")
            if not d:
                return None

            return DataRetentionPolicy(
                id=d.get("id"),
                delete_older_than_n_days=d.get("attributes", {}).get(
                    "delete-older-than-n-days"
                ),
            )
        except Exception as e:
            # Handle the case where TFE >= 202401 and direct user towards the V2 function
            if "data-retention-policies" in str(e) and "does not match" in str(e):
                raise ValueError(
                    "error reading deprecated DataRetentionPolicy, use read_data_retention_policy_choice instead"
                ) from e
            raise

    def read_data_retention_policy_choice(
        self, workspace_id: str
    ) -> DataRetentionPolicyChoice | None:
        """Read a workspace's polymorphic data retention policy choice.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The :class:`DataRetentionPolicyChoice`, or ``None`` if the workspace has no
            policy choice or the relationship endpoint has no data.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> choice = client.workspaces.read_data_retention_policy_choice(
            ...     "ws-abc123def456"
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        # First, read the workspace to determine the type of data retention policy
        ws = self.read_by_id(workspace_id)

        # If there's no data retention policy choice or it's not populated, return it as-is
        if (
            ws.data_retention_policy_choice is None
            or not ws.data_retention_policy_choice.is_populated()
        ):
            return ws.data_retention_policy_choice

        # Get the specific data retention policy data from the relationships endpoint
        r = self.t.request("GET", self._data_retention_policy_link(workspace_id))
        drp_data = r.json().get("data")

        if not drp_data:
            return None

        data_retention_policy_choice = DataRetentionPolicyChoice()
        if (
            ws.data_retention_policy_choice.data_retention_policy_delete_older
            is not None
        ):
            data_retention_policy_choice.data_retention_policy_delete_older = (
                DataRetentionPolicyDeleteOlder(
                    id=drp_data.get("id"),
                    delete_older_than_n_days=drp_data.get("attributes", {}).get(
                        "delete-older-than-n-days"
                    ),
                )
            )
        elif (
            ws.data_retention_policy_choice.data_retention_policy_dont_delete
            is not None
        ):
            data_retention_policy_choice.data_retention_policy_dont_delete = (
                DataRetentionPolicyDontDelete(id=drp_data.get("id"))
            )
        elif ws.data_retention_policy_choice.data_retention_policy is not None:
            data_retention_policy_choice.data_retention_policy = DataRetentionPolicy(
                id=drp_data.get("id"),
                delete_older_than_n_days=drp_data.get("attributes", {}).get(
                    "delete-older-than-n-days"
                ),
            )

        return data_retention_policy_choice

    def set_data_retention_policy(
        self, workspace_id: str, options: DataRetentionPolicySetOptions
    ) -> DataRetentionPolicy:
        """Set a workspace's deprecated data retention policy.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The retention period, as a :class:`DataRetentionPolicySetOptions`.

        Returns:
            The :class:`DataRetentionPolicy`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import DataRetentionPolicySetOptions
            >>> policy = client.workspaces.set_data_retention_policy(
            ...     "ws-abc123def456",
            ...     DataRetentionPolicySetOptions(delete_older_than_n_days=30),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "data-retention-policies",
                "attributes": {
                    "delete-older-than-n-days": options.delete_older_than_n_days
                },
            }
        }

        r = self.t.request(
            "PATCH", self._data_retention_policy_link(workspace_id), json_body=body
        )
        d = r.json()["data"]

        return DataRetentionPolicy(
            id=d.get("id"),
            delete_older_than_n_days=d.get("attributes", {}).get(
                "delete-older-than-n-days"
            ),
        )

    def _data_retention_policy_link(self, workspace_id: str) -> str:
        """Helper method to generate the data retention policy relationships URL."""
        return f"/api/v2/workspaces/{workspace_id}/relationships/data-retention-policy"

    def set_data_retention_policy_delete_older(
        self, workspace_id: str, options: DataRetentionPolicyDeleteOlderSetOptions
    ) -> DataRetentionPolicyDeleteOlder:
        """Set a workspace's delete-older data retention policy.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).
            options: The retention period, as a
                :class:`DataRetentionPolicyDeleteOlderSetOptions`.

        Returns:
            The :class:`DataRetentionPolicyDeleteOlder`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import DataRetentionPolicyDeleteOlderSetOptions
            >>> policy = client.workspaces.set_data_retention_policy_delete_older(
            ...     "ws-abc123def456",
            ...     DataRetentionPolicyDeleteOlderSetOptions(
            ...         delete_older_than_n_days=30
            ...     ),
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "data-retention-policy-delete-olders",
                "attributes": {
                    "delete-older-than-n-days": options.delete_older_than_n_days
                },
            }
        }

        r = self.t.request(
            "POST", self._data_retention_policy_link(workspace_id), json_body=body
        )
        d = r.json()["data"]

        return DataRetentionPolicyDeleteOlder(
            id=d.get("id"),
            delete_older_than_n_days=d.get("attributes", {}).get(
                "delete-older-than-n-days"
            ),
        )

    def set_data_retention_policy_dont_delete(
        self, workspace_id: str
    ) -> DataRetentionPolicyDontDelete:
        """Set a workspace's data retention policy to never delete.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The :class:`DataRetentionPolicyDontDelete`.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> policy = client.workspaces.set_data_retention_policy_dont_delete(
            ...     "ws-abc123def456"
            ... )
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "data-retention-policy-dont-deletes",
                "attributes": {},
            }
        }

        r = self.t.request(
            "POST", self._data_retention_policy_link(workspace_id), json_body=body
        )
        d = r.json()["data"]

        return DataRetentionPolicyDontDelete(id=d.get("id"))

    def delete_data_retention_policy(self, workspace_id: str) -> None:
        """Delete a workspace's data retention policy.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            None.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.workspaces.delete_data_retention_policy("ws-abc123def456")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        self.t.request("DELETE", self._data_retention_policy_link(workspace_id))
        return None

    def readme(self, workspace_id: str) -> str | None:
        """Read the README content for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The README Markdown string, or ``None`` if the workspace has no README
            relationship or included README content.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> markdown = client.workspaces.readme("ws-abc123def456")
            >>> print(markdown or "No README")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        r = self.t.request(
            "GET", f"/api/v2/workspaces/{workspace_id}", params={"include": "readme"}
        )
        payload = r.json()

        # First check if workspace has a readme relationship
        data = payload.get("data", {})
        relationships = data.get("relationships", {})
        readme_rel = relationships.get("readme", {})
        readme_data = readme_rel.get("data")

        # If no readme relationship or it's null, return None
        if not readme_data:
            return None

        # Look for the readme in included section
        readme_id = readme_data.get("id")
        included = payload.get("included") or []

        for inc in included:
            if inc.get("type") == "workspace-readme" and inc.get("id") == readme_id:
                return (inc.get("attributes") or {}).get("raw-markdown")

        return None

    def current_assessment_result(self, workspace_id: str) -> AssessmentResult | None:
        """Read the current health-assessment result for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            The :class:`AssessmentResult`, or ``None`` if no assessment result exists.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> result = client.workspaces.current_assessment_result("ws-abc123def456")
            >>> print(result.status if result else "not assessed")
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        try:
            r = self.t.request(
                "GET",
                f"/api/v2/workspaces/{workspace_id}/current-assessment-result",
            )
        except Exception as exc:
            from ..errors import NotFound

            if isinstance(exc, NotFound):
                return None
            raise
        data = (r.json() or {}).get("data") or {}
        attributes = dict(data.get("attributes") or {})
        attributes["id"] = data.get("id", "")
        return AssessmentResult.model_validate(attributes)

    def list_applicable_varsets(self, workspace_id: str) -> Iterator[dict[str, Any]]:
        """List variable sets that apply to a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-abc123def456"``).

        Returns:
            A single-use ``Iterator[dict[str, Any]]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> varsets = client.workspaces.list_applicable_varsets(
            ...     "ws-abc123def456"
            ... )
            >>> for varset in varsets:
            ...     print(varset["id"], varset.get("name"))
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        path = f"/api/v2/workspaces/{workspace_id}/applicable-varsets"
        for item in self._list(path):
            attrs = dict(item.get("attributes") or {})
            attrs["id"] = item.get("id", "")
            yield attrs
