# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidNoCodeModuleIDError,
    InvalidOrgError,
    InvalidVersionError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceUpgradeIDError,
    RequiredAgentPoolIDError,
    RequiredNameError,
    RequiredProjectError,
    RequiredRegistryModuleIDError,
)
from ..models.no_code_module import (
    NoCodeModule,
    NoCodeModuleCreateOptions,
    NoCodeModuleReadOptions,
    NoCodeModuleUpdateOptions,
    NoCodeVariableOption,
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceUpgradeOptions,
    NoCodeWorkspaceVariable,
    RegistryModuleVariable,
    WorkspaceUpgrade,
)
from ..models.organization import Organization
from ..models.registry_module import RegistryModule
from ..models.workspace import ExecutionMode, Workspace
from ..utils import valid_string, valid_string_id
from ._base import _Service

_NO_CODE_MODULE_TYPE = "no-code-modules"
_REGISTRY_MODULE_TYPE = "registry-module"
_VARIABLE_OPTIONS_TYPE = "variable-options"
_WORKSPACE_TYPE = "workspaces"
_VARS_TYPE = "vars"


def _variable_option_payload(opt: NoCodeVariableOption) -> dict[str, Any]:
    """Serialize a NoCodeVariableOption to its JSON:API relationship-data shape.

    The API accepts both new entries (no ``id``) and updates to existing
    entries (``id`` set). Only the wire-aliased keys are emitted.
    """
    attrs: dict[str, Any] = {}
    if opt.variable_name is not None:
        attrs["variable-name"] = opt.variable_name
    if opt.variable_type is not None:
        attrs["variable-type"] = opt.variable_type
    if opt.options:
        attrs["options"] = list(opt.options)
    entry: dict[str, Any] = {"type": _VARIABLE_OPTIONS_TYPE, "attributes": attrs}
    if opt.id:
        entry["id"] = opt.id
    return entry


def _inline_var_payload(var: NoCodeWorkspaceVariable) -> dict[str, Any]:
    attrs: dict[str, Any] = {"key": var.key}
    if var.value is not None:
        attrs["value"] = var.value
    if var.description is not None:
        attrs["description"] = var.description
    if var.category is not None:
        attrs["category"] = var.category.value
    if var.hcl is not None:
        attrs["hcl"] = var.hcl
    if var.sensitive is not None:
        attrs["sensitive"] = var.sensitive
    return {"type": _VARS_TYPE, "attributes": attrs}


def _variable_option_from(data: dict[str, Any]) -> NoCodeVariableOption:
    attrs = data.get("attributes") or {}
    return NoCodeVariableOption.model_validate(
        {
            "id": data.get("id"),
            "variable-name": attrs.get("variable-name"),
            "variable-type": attrs.get("variable-type"),
            "options": attrs.get("options") or [],
        }
    )


def _no_code_module_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> NoCodeModule:
    attrs = data.get("attributes") or {}
    relationships = data.get("relationships") or {}

    module = NoCodeModule.model_validate(
        {
            "id": data.get("id"),
            "enabled": attrs.get("enabled"),
            "version-pin": attrs.get("version-pin"),
        }
    )

    org_data = (relationships.get("organization") or {}).get("data")
    if org_data and org_data.get("id"):
        module.organization = Organization.model_construct(id=org_data["id"])

    rm_data = (relationships.get("registry-module") or {}).get("data")
    if rm_data and rm_data.get("id"):
        module.registry_module = RegistryModule.model_construct(id=rm_data["id"])

    vo_rel = (relationships.get("variable-options") or {}).get("data") or []
    if vo_rel and included:
        index = {(item.get("type"), item.get("id")): item for item in included}
        resolved: list[NoCodeVariableOption] = []
        for ref in vo_rel:
            key = (ref.get("type"), ref.get("id"))
            full = index.get(key)
            if full is not None:
                resolved.append(_variable_option_from(full))
            else:
                resolved.append(
                    NoCodeVariableOption.model_validate({"id": ref.get("id")})
                )
        module.variable_options = resolved
    elif vo_rel:
        module.variable_options = [
            NoCodeVariableOption.model_validate({"id": ref.get("id")})
            for ref in vo_rel
            if ref.get("id")
        ]

    return module


def _workspace_upgrade_from(data: dict[str, Any]) -> WorkspaceUpgrade:
    attrs = data.get("attributes") or {}
    relationships = data.get("relationships") or {}

    upgrade = WorkspaceUpgrade.model_validate(
        {
            "id": data.get("id"),
            "status": attrs.get("status"),
            "plan-url": attrs.get("plan-url"),
            "message": attrs.get("message"),
        }
    )

    ws_data = (relationships.get("workspace") or {}).get("data")
    if ws_data and ws_data.get("id"):
        upgrade.workspace = Workspace.model_construct(id=ws_data["id"])

    return upgrade


class NoCodeModules(_Service):
    """No-code provisioning: enable a registry module for self-service
    workspace creation, manage allowed variable values, and drive workspace
    create/upgrade flows.

    Upstream docs:
    https://developer.hashicorp.com/terraform/cloud-docs/api-docs/no-code-provisioning

    All write endpoints require a user or team token. Organization tokens are
    not supported by the API.
    """

    # ---- No-code module CRUD ----

    def create(
        self, organization: str, options: NoCodeModuleCreateOptions
    ) -> NoCodeModule:
        """Enable no-code provisioning on a registry module."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(options.registry_module_id):
            raise RequiredRegistryModuleIDError()

        body = self._build_module_payload(options)
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/no-code-modules",
            json_body=body,
        )
        return _no_code_module_from(r.json()["data"])

    def read(
        self,
        no_code_module_id: str,
        options: NoCodeModuleReadOptions | None = None,
    ) -> NoCodeModule:
        """Read a no-code module by ID, optionally including variable options."""
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()

        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(i.value for i in options.include)

        r = self.t.request(
            "GET",
            f"/api/v2/no-code-modules/{no_code_module_id}",
            params=params or None,
        )
        body = r.json()
        return _no_code_module_from(body["data"], body.get("included"))

    def update(
        self, no_code_module_id: str, options: NoCodeModuleUpdateOptions
    ) -> NoCodeModule:
        """Update no-code provisioning settings.

        The HCP API requires every PATCH on a no-code module to include the
        ``registry-module`` relationship in the request body — without it,
        the endpoint returns 404 even though the module exists. If the
        caller didn't supply ``registry_module_id`` in ``options``, we
        read the current module to pick up its existing relationship so
        callers don't have to remember this quirk.
        """
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()

        if not options.registry_module_id:
            current = self.read(no_code_module_id)
            if current.registry_module and current.registry_module.id:
                options = options.model_copy(
                    update={"registry_module_id": current.registry_module.id}
                )

        body = self._build_module_payload(options)
        r = self.t.request(
            "PATCH",
            f"/api/v2/no-code-modules/{no_code_module_id}",
            json_body=body,
        )
        return _no_code_module_from(r.json()["data"])

    def delete(self, no_code_module_id: str) -> None:
        """Disable no-code provisioning for a registry module."""
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()

        self.t.request("DELETE", f"/api/v2/no-code-modules/{no_code_module_id}")

    def read_variables(
        self, no_code_module_id: str, version: str
    ) -> Iterator[RegistryModuleVariable]:
        """Iterate the variables declared by a specific version of a no-code
        module. Useful for driving a form that lets users supply ``vars`` when
        creating a workspace.
        """
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()
        if not valid_string(version):
            raise InvalidVersionError()

        path = (
            f"/api/v2/no-code-modules/{no_code_module_id}"
            f"/versions/{version}/module-variables"
        )
        for item in self._list(path):
            attrs = item.get("attributes") or {}
            yield RegistryModuleVariable.model_validate(
                {
                    "id": item.get("id"),
                    "name": attrs.get("name"),
                    "type": attrs.get("type"),
                    "description": attrs.get("description"),
                    "default": attrs.get("default"),
                    "required": attrs.get("required"),
                    "sensitive": attrs.get("sensitive"),
                    "options": attrs.get("options") or [],
                }
            )

    # ---- Workspace lifecycle ----

    def create_workspace(
        self, no_code_module_id: str, options: NoCodeWorkspaceCreateOptions
    ) -> Workspace:
        """Create a workspace from a no-code module.

        The returned Workspace is populated by the workspaces parser, so
        relationships (project, agent_pool, vars) are available when the
        server includes them.
        """
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()
        if not valid_string(options.name):
            raise RequiredNameError()
        if not valid_string_id(options.project_id):
            raise RequiredProjectError()
        if options.execution_mode == ExecutionMode.AGENT and not valid_string_id(
            options.agent_pool_id
        ):
            raise RequiredAgentPoolIDError()

        body = self._build_workspace_payload(options)
        r = self.t.request(
            "POST",
            f"/api/v2/no-code-modules/{no_code_module_id}/workspaces",
            json_body=body,
        )
        # Reuse the workspace parser so all relationship handling stays in
        # one place. Imported lazily to avoid a circular import.
        from .workspaces import _ws_from

        return _ws_from(r.json()["data"])

    def upgrade_workspace(
        self,
        no_code_module_id: str,
        workspace_id: str,
        options: NoCodeWorkspaceUpgradeOptions | None = None,
    ) -> WorkspaceUpgrade:
        """Initiate a no-code workspace upgrade. Returns the upgrade record;
        poll with ``read_workspace_upgrade`` until ``status`` is
        ``planned_and_finished`` (or terminal), then call
        ``confirm_workspace_upgrade``.
        """
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        attrs: dict[str, Any] = {}
        body: dict[str, Any] = {"data": {"type": _WORKSPACE_TYPE, "attributes": attrs}}
        if options and options.vars:
            body["data"]["relationships"] = {
                "vars": {"data": [_inline_var_payload(v) for v in options.vars]}
            }

        r = self.t.request(
            "POST",
            (
                f"/api/v2/no-code-modules/{no_code_module_id}"
                f"/workspaces/{workspace_id}/upgrade"
            ),
            json_body=body,
        )
        return _workspace_upgrade_from(r.json()["data"])

    def read_workspace_upgrade(
        self,
        no_code_module_id: str,
        workspace_id: str,
        upgrade_id: str,
    ) -> WorkspaceUpgrade:
        """Read the current status of a no-code workspace upgrade."""
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(upgrade_id):
            raise InvalidWorkspaceUpgradeIDError()

        r = self.t.request(
            "GET",
            (
                f"/api/v2/no-code-modules/{no_code_module_id}"
                f"/workspaces/{workspace_id}/upgrade/{upgrade_id}"
            ),
        )
        return _workspace_upgrade_from(r.json()["data"])

    def confirm_workspace_upgrade(
        self,
        no_code_module_id: str,
        workspace_id: str,
        upgrade_id: str,
    ) -> None:
        """Confirm and apply a no-code workspace upgrade plan.

        The API returns a plain-text body (``"Workspace update completed"``)
        rather than a JSON:API envelope; we intentionally return ``None`` and
        rely on the HTTP status for success/failure semantics, matching the
        SDK's pattern for action endpoints.
        """
        if not valid_string_id(no_code_module_id):
            raise InvalidNoCodeModuleIDError()
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()
        if not valid_string_id(upgrade_id):
            raise InvalidWorkspaceUpgradeIDError()

        self.t.request(
            "POST",
            (
                f"/api/v2/no-code-modules/{no_code_module_id}"
                f"/workspaces/{workspace_id}/upgrade/{upgrade_id}"
            ),
        )

    # ---- Payload builders ----

    def _build_module_payload(
        self,
        options: NoCodeModuleCreateOptions | NoCodeModuleUpdateOptions,
    ) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if options.enabled is not None:
            attrs["enabled"] = options.enabled
        if options.version_pin is not None:
            attrs["version-pin"] = options.version_pin

        body: dict[str, Any] = {
            "data": {"type": _NO_CODE_MODULE_TYPE, "attributes": attrs}
        }

        relationships: dict[str, Any] = {}
        if options.registry_module_id:
            relationships["registry-module"] = {
                "data": {
                    "type": _REGISTRY_MODULE_TYPE,
                    "id": options.registry_module_id,
                }
            }

        var_opts = options.variable_options
        if var_opts:
            relationships["variable-options"] = {
                "data": [_variable_option_payload(v) for v in var_opts]
            }

        if relationships:
            body["data"]["relationships"] = relationships

        return body

    def _build_workspace_payload(
        self, options: NoCodeWorkspaceCreateOptions
    ) -> dict[str, Any]:
        attrs: dict[str, Any] = {"name": options.name}
        if options.description is not None:
            attrs["description"] = options.description
        if options.agent_pool_id is not None:
            attrs["agent-pool-id"] = options.agent_pool_id
        if options.auto_apply is not None:
            attrs["auto_apply"] = options.auto_apply
        if options.execution_mode is not None:
            attrs["execution-mode"] = options.execution_mode.value
        if options.source_name is not None:
            attrs["source-name"] = options.source_name
        if options.source_url is not None:
            attrs["source-url"] = options.source_url
        if options.terraform_version is not None:
            attrs["terraform-version"] = options.terraform_version

        body: dict[str, Any] = {"data": {"type": _WORKSPACE_TYPE, "attributes": attrs}}

        relationships: dict[str, Any] = {
            "project": {"data": {"type": "projects", "id": options.project_id}},
        }
        if options.vars:
            relationships["vars"] = {
                "data": [_inline_var_payload(v) for v in options.vars]
            }
        body["data"]["relationships"] = relationships
        return body
