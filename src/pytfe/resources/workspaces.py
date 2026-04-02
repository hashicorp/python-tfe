# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

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
from ..models.common import (
    EffectiveTagBinding,
    Tag,
    TagBinding,
)
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


def _em_safe(v: Any) -> ExecutionMode | None:
    # Only accept strings; map to enum if known, else None
    if not isinstance(v, str):
        return None
    result = ExecutionMode._value2member_map_.get(v)
    return result if isinstance(result, ExecutionMode) else None


def _ws_from(d: dict[str, Any]) -> Workspace:
    attr: dict[str, Any] = d.get("attributes", {}) or {}
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

    # Map outputs
    outputs = []
    if relationships.get("outputs", {}).get("data"):
        for output_data in relationships["outputs"].get("data", []):
            output_attrs = output_data.get("attributes", {})
            output_attrs["id"] = output_data.get("id", "")
            outputs.append(WorkspaceOutputs.model_validate(output_attrs))

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
    attr["execution_mode"] = em
    attr["actions"] = actions
    attr["permissions"] = permissions
    attr["setting_overwrites"] = setting_overwrites
    attr["vcs-repo"] = vcs_repo

    # Add parsed relations
    if relationships.get("organization", {}).get("data"):
        attr["organization"] = Organization.model_validate(
            {"id": relationships["organization"]["data"].get("id")}
        )
    if relationships.get("project", {}).get("data"):
        attr["project"] = Project.model_validate(
            {"id": relationships["project"]["data"].get("id")}
        )
    if relationships.get("ssh-key", {}).get("data"):
        attr["ssh_key"] = relationships["ssh-key"]["data"].get("id")
    attr["outputs"] = outputs
    attr["locked_by"] = locked_by
    attr["data_retention_policy_choice"] = data_retention_policy_choice

    return Workspace.model_validate(attr)


class Workspaces(_Service):
    def list(
        self,
        organization: str,
        options: WorkspaceListOptions | None = None,
    ) -> Iterator[Workspace]:
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
        """Read workspace by organization and name."""
        return self.read_with_options(workspace, organization=organization)

    def read_with_options(
        self,
        workspace: str,
        options: WorkspaceReadOptions | None = None,
        *,
        organization: str,
    ) -> Workspace:
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
        ws = _ws_from(r.json()["data"])
        ws.data_retention_policy = (
            ws.data_retention_policy_choice.convert_to_legacy_struct()
            if ws.data_retention_policy_choice
            else None
        )
        return ws

    def read_by_id(self, workspace_id: str) -> Workspace:
        """Read workspace by workspace ID."""
        return self.read_by_id_with_options(workspace_id)

    def read_by_id_with_options(
        self, workspace_id: str, options: WorkspaceReadOptions | None = None
    ) -> Workspace:
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}
        if options is not None:
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", f"/api/v2/workspaces/{workspace_id}", params=params)
        ws = _ws_from(r.json()["data"])
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
        """Create a new workspace in the given organization."""
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
        """Update workspace by organization and name."""
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
        """Update workspace by workspace ID."""
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
        """Delete workspace by organization and workspace name."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(workspace):
            raise InvalidWorkspaceValueError()

        self.t.request(
            "DELETE", f"/api/v2/organizations/{organization}/workspaces/{workspace}"
        )
        return None

    def delete_by_id(self, workspace_id: str) -> None:
        """Delete workspace by workspace ID."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        self.t.request("DELETE", f"/api/v2/workspaces/{workspace_id}")
        return None

    def safe_delete(self, workspace: str, *, organization: str) -> None:
        """Safely delete workspace by organization and name."""
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
        """Safely delete workspace by workspace ID."""
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
        """Remove VCS connection from workspace by organization and name."""
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
        """Remove VCS connection from workspace by workspace ID."""
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
        """Lock a workspace by workspace ID."""
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
        """Unlock a workspace by workspace ID."""
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
        """Force unlock a workspace by workspace ID."""
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
        """Assign an SSH key to a workspace by workspace ID."""
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
        """Unassign the SSH key from a workspace by workspace ID."""
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
        """List remote state consumers of a workspace by workspace ID."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        path = f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers"
        for item in self._list(path, params=params):
            yield _ws_from(item)

    def add_remote_state_consumers(
        self, workspace_id: str, options: WorkspaceAddRemoteStateConsumersOptions
    ) -> None:
        """Add remote state consumers to a workspace by workspace ID."""
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
        """Remove remote state consumers from a workspace by workspace ID."""
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
        """Update remote state consumers of a workspace by workspace ID."""
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
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        path = f"/api/v2/workspaces/{workspace_id}/relationships/tags"
        for item in self._list(path, params=params):
            attr = item.get("attributes", {}) or {}
            yield Tag(id=item.get("id"), name=attr.get("name", ""))

    def add_tags(self, workspace_id: str, options: WorkspaceAddTagsOptions) -> None:
        """AddTags adds a list of tags to a workspace."""
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
        """RemoveTags removes a list of tags from a workspace."""
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
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        path = f"/api/v2/workspaces/{workspace_id}/tag-bindings"
        for item in self._list(path):
            attr = item.get("attributes", {}) or {}
            yield TagBinding(
                id=item.get("id"),
                key=attr.get("key", ""),
                value=attr.get("value", ""),
            )

    def list_effective_tag_bindings(
        self, workspace_id: str
    ) -> Iterator[EffectiveTagBinding]:
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        path = f"/api/v2/workspaces/{workspace_id}/effective-tag-bindings"
        for item in self._list(path):
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
        """AddTagBindings adds or modifies the value of existing tag binding keys for a workspace."""
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
        """DeleteAllTagBindings removes all tag bindings associated with a workspace."""
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
        """Read a workspace's data retention policy (deprecated: use read_data_retention_policy_choice instead)."""
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
        """Read a workspace's data retention policy choice (polymorphic)."""
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
        """Set a workspace's data retention policy (deprecated: use set_data_retention_policy_delete_older instead)."""
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
        """Set a workspace's data retention policy to delete data older than a certain number of days."""
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
        """Set a workspace's data retention policy to explicitly not delete data."""
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
        """Delete a workspace's data retention policy."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        self.t.request("DELETE", self._data_retention_policy_link(workspace_id))
        return None

    def readme(self, workspace_id: str) -> str | None:
        """Get the README content of a workspace by its ID."""
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
