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
from ..types import (
    DataRetentionPolicy,
    DataRetentionPolicyChoice,
    DataRetentionPolicyDeleteOlder,
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDelete,
    DataRetentionPolicyDontDeleteSetOptions,
    DataRetentionPolicySetOptions,
    EffectiveTagBinding,
    ExecutionMode,
    LockedByChoice,
    Tag,
    TagBinding,
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
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceSettingOverwrites,
    WorkspaceSource,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
    WorkspaceUpdateRemoteStateConsumersOptions,
)
from ..utils import (
    valid_string,
    valid_string_id,
    validate_workspace_create_options,
    validate_workspace_update_options,
)
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def _em_safe(v: Any) -> ExecutionMode | None:
    # Only accept strings; map to enum if known, else None
    if not isinstance(v, str):
        return None
    return ExecutionMode._value2member_map_.get(v)  # type: ignore[return-value]


def _ws_from(d: dict[str, Any], org: str | None = None) -> Workspace:
    attr: dict[str, Any] = d.get("attributes", {}) or {}

    # Coerce to required string fields (empty string fallback keeps mypy happy)
    id_str: str = _safe_str(d.get("id"))
    name_str: str = _safe_str(attr.get("name"))
    org_str: str = _safe_str(org if org is not None else attr.get("organization"))

    # Optional fields
    em: ExecutionMode | None = _em_safe(attr.get("execution-mode"))

    proj_id: str | None = None
    proj = attr.get("project")
    if isinstance(proj, dict):
        proj_id = proj.get("id") if isinstance(proj.get("id"), str) else None

    # Enhanced field mapping
    tags_val = attr.get("tags", []) or []
    tags_list: builtins.list[Tag] = []
    if isinstance(tags_val, builtins.list):
        for tag_item in tags_val:
            if isinstance(tag_item, dict):
                tags_list.append(
                    Tag(id=tag_item.get("id"), name=tag_item.get("name", ""))
                )
            elif isinstance(tag_item, str):
                tags_list.append(Tag(name=tag_item))

    # Map additional attributes
    actions = None
    if attr.get("actions"):
        actions = WorkspaceActions(
            is_destroyable=attr["actions"].get("is-destroyable", False)
        )

    permissions = None
    if attr.get("permissions"):
        perm_attr = attr["permissions"]
        permissions = WorkspacePermissions(
            can_destroy=perm_attr.get("can-destroy", False),
            can_force_unlock=perm_attr.get("can-force-unlock", False),
            can_lock=perm_attr.get("can-lock", False),
            can_manage_run_tasks=perm_attr.get("can-manage-run-tasks", False),
            can_queue_apply=perm_attr.get("can-queue-apply", False),
            can_queue_destroy=perm_attr.get("can-queue-destroy", False),
            can_queue_run=perm_attr.get("can-queue-run", False),
            can_read_settings=perm_attr.get("can-read-settings", False),
            can_unlock=perm_attr.get("can-unlock", False),
            can_update=perm_attr.get("can-update", False),
            can_update_variable=perm_attr.get("can-update-variable", False),
            can_force_delete=perm_attr.get("can-force-delete"),
        )

    setting_overwrites = None
    if attr.get("setting-overwrites"):
        so_attr = attr["setting-overwrites"]
        setting_overwrites = WorkspaceSettingOverwrites(
            execution_mode=so_attr.get("execution-mode"),
            agent_pool=so_attr.get("agent-pool"),
        )

    # Map VCS repo
    vcs_repo = None
    if attr.get("vcs-repo"):
        vcs_attr = attr["vcs-repo"]
        vcs_repo = VCSRepo(
            branch=vcs_attr.get("branch"),
            identifier=vcs_attr.get("identifier"),
            ingress_submodules=vcs_attr.get("ingress-submodules"),
            oauth_token_id=vcs_attr.get("oauth-token-id"),
            gha_installation_id=vcs_attr.get("github-app-installation-id"),
        )

    # Map locked_by choice
    locked_by = None
    if d.get("relationships", {}).get("locked-by"):
        lb_data = d["relationships"]["locked-by"]["data"]
        if lb_data:
            locked_by = LockedByChoice(
                run=lb_data.get("run"),
                user=lb_data.get("user"),
                team=lb_data.get("team"),
            )

    # Map outputs
    outputs = []
    if d.get("relationships", {}).get("outputs"):
        for output_data in d["relationships"]["outputs"].get("data", []):
            outputs.append(
                WorkspaceOutputs(
                    id=output_data.get("id", ""),
                    name=output_data.get("attributes", {}).get("name", ""),
                    sensitive=output_data.get("attributes", {}).get("sensitive", False),
                    output_type=output_data.get("attributes", {}).get(
                        "output-type", ""
                    ),
                    value=output_data.get("attributes", {}).get("value"),
                )
            )

    data_retention_policy_choice: DataRetentionPolicyChoice | None = None
    if d.get("relationships", {}).get("data-retention-policy-choice"):
        drp_data = d["relationships"]["data-retention-policy-choice"]["data"]
        if drp_data:
            if drp_data.get("type") == "data-retention-policy-delete-olders":
                data_retention_policy_choice = DataRetentionPolicyChoice(
                    data_retention_policy_delete_older=DataRetentionPolicyDeleteOlder(
                        id=drp_data.get("id"),
                        delete_older_than_n_days=drp_data.get("attributes", {}).get(
                            "delete-older-than-n-days", 0
                        ),
                    )
                )
            elif drp_data.get("type") == "data-retention-policy-dont-deletes":
                data_retention_policy_choice = DataRetentionPolicyChoice(
                    data_retention_policy_dont_delete=DataRetentionPolicyDontDelete(
                        id=drp_data.get("id")
                    )
                )
            elif drp_data.get("type") == "data-retention-policies":
                # Legacy data retention policy
                data_retention_policy_choice = DataRetentionPolicyChoice(
                    data_retention_policy=DataRetentionPolicy(
                        id=drp_data.get("id"),
                        delete_older_than_n_days=drp_data.get("attributes", {}).get(
                            "delete-older-than-n-days", 0
                        ),
                    )
                )

    return Workspace(
        id=id_str,
        name=name_str,
        organization=org_str,
        execution_mode=em,
        project_id=proj_id,
        tags=tags_list,
        # Core attributes
        actions=actions,
        allow_destroy_plan=attr.get("allow-destroy-plan", False),
        assessments_enabled=attr.get("assessments-enabled", False),
        auto_apply=attr.get("auto-apply", False),
        auto_apply_run_trigger=attr.get("auto-apply-run-trigger", False),
        auto_destroy_at=attr.get("auto-destroy-at"),
        auto_destroy_activity_duration=attr.get("auto-destroy-activity-duration"),
        can_queue_destroy_plan=attr.get("can-queue-destroy-plan", False),
        created_at=attr.get("created-at"),
        description=attr.get("description") or "",
        environment=attr.get("environment", ""),
        file_triggers_enabled=attr.get("file-triggers-enabled", False),
        global_remote_state=attr.get("global-remote-state", False),
        inherits_project_auto_destroy=attr.get("inherits-project-auto-destroy", False),
        locked=attr.get("locked", False),
        migration_environment=attr.get("migration-environment", ""),
        no_code_upgrade_available=attr.get("no-code-upgrade-available", False),
        operations=attr.get("operations", False),
        permissions=permissions,
        queue_all_runs=attr.get("queue-all-runs", False),
        speculative_enabled=attr.get("speculative-enabled", False),
        source=WorkspaceSource(attr.get("source")) if attr.get("source") else None,
        source_name=attr.get("source-name") or "",
        source_url=attr.get("source-url") or "",
        structured_run_output_enabled=attr.get("structured-run-output-enabled", False),
        terraform_version=attr.get("terraform-version") or "",
        trigger_prefixes=attr.get("trigger-prefixes", []),
        trigger_patterns=attr.get("trigger-patterns", []),
        vcs_repo=vcs_repo,
        working_directory=attr.get("working-directory") or "",
        updated_at=attr.get("updated-at"),
        resource_count=attr.get("resource-count", 0),
        apply_duration_average=attr.get("apply-duration-average"),
        plan_duration_average=attr.get("plan-duration-average"),
        policy_check_failures=attr.get("policy-check-failures") or 0,
        run_failures=attr.get("run-failures") or 0,
        runs_count=attr.get("workspace-kpis-runs-count") or 0,
        tag_names=attr.get("tag-names", []),
        setting_overwrites=setting_overwrites,
        # Relations
        outputs=outputs,
        locked_by=locked_by,
        data_retention_policy_choice=data_retention_policy_choice
        if data_retention_policy_choice
        else None,
    )


class Workspaces(_Service):
    def list(
        self,
        organization: str,
        *,
        options: WorkspaceListOptions,
    ) -> Iterator[Workspace]:
        # Validate parameters
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params: dict[str, Any] = {}

        # Use structured options
        if options.search:
            params["search[name]"] = options.search
        if options.tags:
            params["search[tags]"] = options.tags
        if options.exclude_tags:
            params["search[exclude-tags]"] = options.exclude_tags
        if options.wildcard_name:
            params["search[wildcard-name]"] = options.wildcard_name
        if options.project_id:
            params["filter[project][id]"] = options.project_id
        if options.current_run_status:
            params["filter[current-run][status]"] = options.current_run_status
        if options.include:
            params["include"] = ",".join([i.value for i in options.include])
        if options.sort:
            params["sort"] = options.sort
        if options.page_number:
            params["page[number]"] = options.page_number
        if options.page_size:
            params["page[size]"] = options.page_size

        # Handle tag binding filters
        if options.tag_bindings:
            for i, binding in enumerate(options.tag_bindings):
                if binding.key and binding.value:
                    params[f"search[tag-bindings][{i}][key]"] = binding.key
                    params[f"search[tag-bindings][{i}][value]"] = binding.value
                elif binding.key:
                    params[f"search[tag-bindings][{i}][key]"] = binding.key

        path = f"/api/v2/organizations/{organization}/workspaces"
        for item in self._list(path, params=params):
            yield _ws_from(item, organization)

    def read(self, organization: str, name: str) -> Workspace:
        """Read workspace by organization and name."""
        return self.read_with_options(
            name, organization=organization, options=WorkspaceReadOptions()
        )

    def read_with_options(
        self,
        name: str,
        organization: str,
        *,
        options: WorkspaceReadOptions,
    ) -> Workspace:
        # Validate parameters
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(name):
            raise InvalidWorkspaceValueError()

        params: dict[str, Any] = {}
        if options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/workspaces/{name}",
            params=params,
        )
        ws = _ws_from(r.json()["data"], organization)
        ws.data_retention_policy = (
            ws.data_retention_policy_choice.convert_to_legacy_struct()
            if ws.data_retention_policy_choice
            else None
        )
        return ws

    def read_by_id(self, id: str) -> Workspace:
        """Read workspace by workspace ID."""
        return self.read_by_id_with_options(id, options=WorkspaceReadOptions())

    def read_by_id_with_options(
        self, id: str, *, options: WorkspaceReadOptions
    ) -> Workspace:
        # Validate parameters
        if not valid_string_id(id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}
        if options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", f"/api/v2/workspaces/{id}", params=params)
        ws = _ws_from(r.json()["data"], None)
        if ws.data_retention_policy_choice is not None:
            ws.data_retention_policy = (
                ws.data_retention_policy_choice.convert_to_legacy_struct()
            )
        return ws

    def create(
        self,
        organization: str,
        *,
        options: WorkspaceCreateOptions,
    ) -> Workspace:
        """Create a new workspace in the given organization."""
        # Validate parameters
        if not valid_string_id(organization):
            raise InvalidOrgError()

        # Validate options before creating workspace
        validate_workspace_create_options(options)

        body = self._build_workspace_payload(options, is_create=True)
        r = self.t.request(
            "POST", f"/api/v2/organizations/{organization}/workspaces", json_body=body
        )
        return _ws_from(r.json()["data"], organization)

    # Convenience methods for org+name operations
    def update(
        self, organization: str, name: str, *, options: WorkspaceUpdateOptions
    ) -> Workspace:
        """Update workspace by organization and name."""
        # Validate parameters
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(name):
            raise InvalidWorkspaceValueError()

        # Validate options before updating workspace
        validate_workspace_update_options(options)

        body = self._build_workspace_payload(options, is_create=False)
        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/workspaces/{name}",
            json_body=body,
        )
        return _ws_from(r.json()["data"], organization)

    def update_by_id(self, id: str, *, options: WorkspaceUpdateOptions) -> Workspace:
        """Update workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(id):
            raise InvalidWorkspaceIDError()

        # Validate options before updating workspace
        validate_workspace_update_options(options)

        body = self._build_workspace_payload(options, is_create=False)
        r = self.t.request("PATCH", f"/api/v2/workspaces/{id}", json_body=body)
        return _ws_from(r.json()["data"], None)

    def _build_workspace_payload(
        self,
        options: WorkspaceCreateOptions | WorkspaceUpdateOptions,
        is_create: bool = False,
    ) -> dict[str, Any]:
        """Build the workspace payload from options following API specification.

        Args:
            options: Either WorkspaceCreateOptions or WorkspaceUpdateOptions
            is_create: True for create operations, False for update operations
        """
        body: dict[str, Any] = {"data": {"type": "workspaces", "attributes": {}}}

        # Add attributes from options
        attrs = body["data"]["attributes"]

        # Required field for both create and update: name
        attrs["name"] = options.name

        # Common optional attributes
        if options.agent_pool_id is not None:
            attrs["agent-pool-id"] = options.agent_pool_id
        if options.allow_destroy_plan is not None:
            attrs["allow-destroy-plan"] = options.allow_destroy_plan
        if options.assessments_enabled is not None:
            attrs["assessments-enabled"] = options.assessments_enabled
        if options.auto_apply is not None:
            attrs["auto-apply"] = options.auto_apply
        if options.auto_apply_run_trigger is not None:
            attrs["auto-apply-run-trigger"] = options.auto_apply_run_trigger
        if options.auto_destroy_at is not None:
            # Format datetime as ISO8601 string as expected by the API
            attrs["auto-destroy-at"] = options.auto_destroy_at.isoformat()
        if options.auto_destroy_activity_duration is not None:
            attrs["auto-destroy-activity-duration"] = (
                options.auto_destroy_activity_duration
            )
        if options.description is not None:
            attrs["description"] = options.description
        if options.execution_mode is not None:
            # Accepts either an enum (with .value) or a string; fallback to the value itself if neither
            attrs["execution-mode"] = getattr(
                options.execution_mode, "value", options.execution_mode
            )
        if options.file_triggers_enabled is not None:
            attrs["file-triggers-enabled"] = options.file_triggers_enabled
        if options.global_remote_state is not None:
            attrs["global-remote-state"] = options.global_remote_state
        if options.queue_all_runs is not None:
            attrs["queue-all-runs"] = options.queue_all_runs
        if options.speculative_enabled is not None:
            attrs["speculative-enabled"] = options.speculative_enabled
        if options.terraform_version is not None:
            attrs["terraform-version"] = options.terraform_version
        if options.trigger_patterns:
            attrs["trigger-patterns"] = options.trigger_patterns
        if options.trigger_prefixes:
            attrs["trigger-prefixes"] = options.trigger_prefixes
        if options.working_directory is not None:
            attrs["working-directory"] = options.working_directory
        if options.allow_destroy_plan is not None:
            attrs["allow-destroy-plan"] = options.allow_destroy_plan
        if options.assessments_enabled is not None:
            attrs["assessments-enabled"] = options.assessments_enabled

        # Create-specific attributes
        if (
            is_create
            and hasattr(options, "source_name")
            and options.source_name is not None
        ):
            attrs["source-name"] = options.source_name
        if (
            is_create
            and hasattr(options, "source_url")
            and options.source_url is not None
        ):
            attrs["source-url"] = options.source_url
        if (
            is_create
            and hasattr(options, "structured_run_output_enabled")
            and options.structured_run_output_enabled is not None
        ):
            attrs["structured-run-output-enabled"] = (
                options.structured_run_output_enabled
            )
        if (
            is_create
            and hasattr(options, "hyok_enabled")
            and options.hyok_enabled is not None
        ):
            attrs["hyok-enabled"] = options.hyok_enabled

        # VCS repository configuration
        if hasattr(options, "vcs_repo") and options.vcs_repo is not None:
            vcs_data: dict[str, Any] = {}
            if options.vcs_repo.oauth_token_id is not None:
                vcs_data["oauth-token-id"] = options.vcs_repo.oauth_token_id
            if options.vcs_repo.identifier is not None:
                vcs_data["identifier"] = options.vcs_repo.identifier
            if options.vcs_repo.branch is not None:
                vcs_data["branch"] = options.vcs_repo.branch
            if options.vcs_repo.ingress_submodules is not None:
                vcs_data["ingress-submodules"] = options.vcs_repo.ingress_submodules
            if options.vcs_repo.tags_regex is not None:
                vcs_data["tags-regex"] = options.vcs_repo.tags_regex
            if options.vcs_repo.gha_installation_id is not None:
                vcs_data["github-app-installation-id"] = (
                    options.vcs_repo.gha_installation_id
                )
            attrs["vcs-repo"] = vcs_data

        # Setting overwrites
        if (
            hasattr(options, "setting_overwrites")
            and options.setting_overwrites is not None
        ):
            setting_overwrites: dict[str, Any] = {}
            if options.setting_overwrites.execution_mode is not None:
                setting_overwrites["execution-mode"] = (
                    options.setting_overwrites.execution_mode
                )
            if options.setting_overwrites.agent_pool is not None:
                setting_overwrites["agent-pool"] = options.setting_overwrites.agent_pool
            attrs["setting-overwrites"] = setting_overwrites

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

    def delete(self, organization: str, name: str) -> None:
        """Delete workspace by organization and workspace name."""
        # Validate parameters (similar to Go implementation)
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(name):
            raise InvalidWorkspaceValueError()

        self.t.request(
            "DELETE", f"/api/v2/organizations/{organization}/workspaces/{name}"
        )

    def delete_by_id(self, id: str) -> None:
        """Delete workspace by workspace ID."""
        # Validate parameters (similar to Go implementation)
        if not valid_string_id(id):
            raise InvalidWorkspaceIDError()

        self.t.request("DELETE", f"/api/v2/workspaces/{id}")

    def safe_delete(self, organization: str, name: str) -> None:
        """Safely delete workspace by organization and name."""
        # Validate parameters (similar to Go implementation)
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(name):
            raise InvalidWorkspaceValueError()

        self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/workspaces/{name}/actions/safe-delete",
        )

    def safe_delete_by_id(self, id: str) -> None:
        """Safely delete workspace by workspace ID."""
        # Validate parameters (similar to Go implementation)
        if not valid_string_id(id):
            raise InvalidWorkspaceIDError()

        self.t.request("POST", f"/api/v2/workspaces/{id}/actions/safe-delete")

    def remove_vcs_connection(
        self,
        organization: str,
        name: str,
        *,
        options: WorkspaceRemoveVCSConnectionOptions,
    ) -> Workspace:
        """Remove VCS connection from workspace by organization and name."""
        # Validate parameters
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(name):
            raise InvalidWorkspaceValueError()

        body = {
            "data": {
                "type": "workspaces",
                "id": options.id,
                "attributes": {
                    "vcs-repo": None  # Setting to None removes the VCS connection
                },
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/workspaces/{name}",
            json_body=body,
        )
        return _ws_from(r.json()["data"], organization)

    def remove_vcs_connection_by_id(
        self, id: str, *, options: WorkspaceRemoveVCSConnectionOptions
    ) -> Workspace:
        """Remove VCS connection from workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "workspaces",
                "id": options.id,
                "attributes": {
                    "vcs-repo": None  # Setting to None removes the VCS connection
                },
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{id}",
            json_body=body,
        )
        return _ws_from(r.json()["data"], None)

    def lock(self, workspace_id: str, *, options: WorkspaceLockOptions) -> Workspace:
        """Lock a workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {"reason": options.reason}

        r = self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/actions/lock",
            json_body=body,
        )
        return _ws_from(r.json()["data"], None)

    def unlock(self, workspace_id: str) -> Workspace:
        """Unlock a workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        try:
            r = self.t.request(
                "POST",
                f"/api/v2/workspaces/{workspace_id}/actions/unlock",
            )
            return _ws_from(r.json()["data"], None)
        except Exception as e:
            if "latest state version is still pending" in str(e):
                raise WorkspaceLockedStateVersionStillPending(str(e)) from e
            raise

    def force_unlock(self, workspace_id: str) -> Workspace:
        """Force unlock a workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        r = self.t.request(
            "POST",
            f"/api/v2/workspaces/{workspace_id}/actions/force-unlock",
        )
        return _ws_from(r.json()["data"], None)

    def assign_ssh_key(
        self, workspace_id: str, *, options: WorkspaceAssignSSHKeyOptions
    ) -> Workspace:
        """Assign an SSH key to a workspace by workspace ID."""
        # Validate parameters
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
        return _ws_from(r.json()["data"], None)

    def unassign_ssh_key(self, workspace_id: str) -> Workspace:
        """Unassign the SSH key from a workspace by workspace ID."""
        # Validate parameters
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

        return _ws_from(r.json()["data"], None)

    def list_remote_state_consumers(
        self, workspace_id: str, options: WorkspaceListRemoteStateConsumersOptions
    ) -> Iterator[Workspace]:
        """List remote state consumers of a workspace by workspace ID."""
        # Validate parameters
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}

        # Use structured options
        if options.page_number:
            params["page[number]"] = options.page_number
        if options.page_size:
            params["page[size]"] = options.page_size

        path = f"/api/v2/workspaces/{workspace_id}/relationships/remote-state-consumers"
        for item in self._list(path, params=params):
            yield _ws_from(item, None)

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

    def list_tags(
        self, workspace_id: str, options: WorkspaceTagListOptions
    ) -> Iterator[Tag]:
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}
        if options.query is not None:
            params["name"] = options.query
        if options.page_number is not None:
            params["page[number]"] = options.page_number
        if options.page_size is not None:
            params["page[size]"] = options.page_size

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
        self, workspace_id: str, *, options: DataRetentionPolicySetOptions
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
        self, workspace_id: str, *, options: DataRetentionPolicyDeleteOlderSetOptions
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
        self, workspace_id: str, *, options: DataRetentionPolicyDontDeleteSetOptions
    ) -> DataRetentionPolicyDontDelete:
        """Set a workspace's data retention policy to explicitly not delete data."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        body = {
            "data": {
                "type": "data-retention-policy-dont-deletes",
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
