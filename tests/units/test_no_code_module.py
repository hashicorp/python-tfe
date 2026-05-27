# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the no-code provisioning resource."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest

from pytfe.errors import (
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
from pytfe.models.no_code_module import (
    NoCodeModuleCreateOptions,
    NoCodeModuleIncludeOpt,
    NoCodeModuleReadOptions,
    NoCodeModuleUpdateOptions,
    NoCodeVariableOption,
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceUpgradeOptions,
    NoCodeWorkspaceVariable,
)
from pytfe.models.variable import CategoryType
from pytfe.models.workspace import ExecutionMode
from pytfe.resources.no_code_module import NoCodeModules


def _resp(json_body: Any) -> Mock:
    r = Mock()
    r.json.return_value = json_body
    return r


def _no_code_module_body(
    *,
    nc_id: str = "nocode-abc123",
    enabled: bool = True,
    version_pin: str | None = "1.0.0",
    org_id: str = "my-org",
    registry_module_id: str = "mod-abc123",
    variable_option_refs: list[dict[str, str]] | None = None,
    included: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    relationships: dict[str, Any] = {
        "organization": {"data": {"type": "organizations", "id": org_id}},
        "registry-module": {
            "data": {"type": "registry-modules", "id": registry_module_id}
        },
    }
    if variable_option_refs is not None:
        relationships["variable-options"] = {"data": variable_option_refs}

    body: dict[str, Any] = {
        "data": {
            "id": nc_id,
            "type": "no-code-modules",
            "attributes": {"enabled": enabled, "version-pin": version_pin},
            "relationships": relationships,
        }
    }
    if included is not None:
        body["included"] = included
    return body


def _workspace_body(*, ws_id: str = "ws-abc123") -> dict[str, Any]:
    return {
        "data": {
            "id": ws_id,
            "type": "workspaces",
            "attributes": {
                "name": "no-code-ws",
                "execution-mode": "remote",
            },
            "relationships": {
                "project": {"data": {"type": "projects", "id": "prj-abc123"}},
            },
        }
    }


def _upgrade_body(
    *,
    upgrade_id: str = "wsu-abc123",
    status: str = "planned",
    ws_id: str = "ws-abc123",
) -> dict[str, Any]:
    return {
        "data": {
            "id": upgrade_id,
            "type": "workspace-upgrade",
            "attributes": {
                "status": status,
                "plan-url": "https://app.terraform.io/plan/abc",
            },
            "relationships": {
                "workspace": {"data": {"type": "workspaces", "id": ws_id}},
            },
        }
    }


class TestNoCodeModuleCreate:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_create_minimum_payload(self) -> None:
        self.transport.request.return_value = _resp(_no_code_module_body())

        result = self.service.create(
            "my-org",
            NoCodeModuleCreateOptions(registry_module_id="mod-abc123"),
        )

        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]

        assert method == "POST"
        assert path == "/api/v2/organizations/my-org/no-code-modules"
        assert body["data"]["type"] == "no-code-modules"
        assert body["data"]["attributes"] == {}
        assert body["data"]["relationships"]["registry-module"]["data"] == {
            "type": "registry-module",
            "id": "mod-abc123",
        }
        assert "variable-options" not in body["data"]["relationships"]
        assert result.id == "nocode-abc123"
        assert result.registry_module is not None
        assert result.registry_module.id == "mod-abc123"

    def test_create_with_enabled_and_version_pin(self) -> None:
        self.transport.request.return_value = _resp(_no_code_module_body())

        self.service.create(
            "my-org",
            NoCodeModuleCreateOptions(
                registry_module_id="mod-abc123",
                enabled=True,
                version_pin="2.4.0",
            ),
        )

        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {
            "enabled": True,
            "version-pin": "2.4.0",
        }

    def test_create_with_variable_options(self) -> None:
        self.transport.request.return_value = _resp(_no_code_module_body())

        self.service.create(
            "my-org",
            NoCodeModuleCreateOptions(
                registry_module_id="mod-abc123",
                variable_options=[
                    NoCodeVariableOption(
                        variable_name="region",
                        variable_type="string",
                        options=["us-east-1", "us-west-2"],
                    )
                ],
            ),
        )

        body = self.transport.request.call_args.kwargs["json_body"]
        var_opts = body["data"]["relationships"]["variable-options"]["data"]
        assert len(var_opts) == 1
        assert var_opts[0] == {
            "type": "variable-options",
            "attributes": {
                "variable-name": "region",
                "variable-type": "string",
                "options": ["us-east-1", "us-west-2"],
            },
        }
        # No id on a new option
        assert "id" not in var_opts[0]

    def test_create_invalid_org_raises(self) -> None:
        with pytest.raises(InvalidOrgError):
            self.service.create(
                "",
                NoCodeModuleCreateOptions(registry_module_id="mod-abc123"),
            )

    def test_create_missing_registry_module_id_raises(self) -> None:
        with pytest.raises(RequiredRegistryModuleIDError):
            self.service.create(
                "my-org",
                NoCodeModuleCreateOptions(registry_module_id=""),
            )


class TestNoCodeModuleRead:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_read_without_include(self) -> None:
        self.transport.request.return_value = _resp(_no_code_module_body())

        result = self.service.read("nocode-abc123")

        method, path = self.transport.request.call_args.args
        kwargs = self.transport.request.call_args.kwargs
        assert method == "GET"
        assert path == "/api/v2/no-code-modules/nocode-abc123"
        assert kwargs.get("params") is None
        assert result.id == "nocode-abc123"
        assert result.enabled is True

    def test_read_with_include_emits_query_param(self) -> None:
        self.transport.request.return_value = _resp(_no_code_module_body())

        self.service.read(
            "nocode-abc123",
            NoCodeModuleReadOptions(
                include=[NoCodeModuleIncludeOpt.VARIABLE_OPTIONS]
            ),
        )

        params = self.transport.request.call_args.kwargs["params"]
        assert params == {"include": "variable_options"}

    def test_read_resolves_included_variable_options(self) -> None:
        body = _no_code_module_body(
            variable_option_refs=[
                {"type": "variable-options", "id": "vo-1"},
                {"type": "variable-options", "id": "vo-2"},
            ],
            included=[
                {
                    "type": "variable-options",
                    "id": "vo-1",
                    "attributes": {
                        "variable-name": "region",
                        "variable-type": "string",
                        "options": ["us-east-1"],
                    },
                },
                # Only one of the two is in `included` — the other should
                # fall back to an id-only stub.
            ],
        )
        self.transport.request.return_value = _resp(body)

        result = self.service.read("nocode-abc123")

        assert len(result.variable_options) == 2
        first = result.variable_options[0]
        assert first.id == "vo-1"
        assert first.variable_name == "region"
        assert first.options == ["us-east-1"]
        second = result.variable_options[1]
        assert second.id == "vo-2"
        assert second.variable_name is None

    def test_read_invalid_id_raises(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            self.service.read("")


class TestNoCodeModuleUpdate:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_update_variable_options_with_and_without_ids(self) -> None:
        # Caller supplies registry_module_id explicitly, so no auto-read.
        self.transport.request.return_value = _resp(_no_code_module_body())

        self.service.update(
            "nocode-abc123",
            NoCodeModuleUpdateOptions(
                registry_module_id="mod-abc123",
                enabled=False,
                variable_options=[
                    NoCodeVariableOption(
                        id="vo-existing",
                        variable_name="region",
                        variable_type="string",
                        options=["us-east-1", "us-west-2"],
                    ),
                    NoCodeVariableOption(
                        variable_name="size",
                        variable_type="string",
                        options=["small", "medium", "large"],
                    ),
                ],
            ),
        )

        # One PATCH (no preceding GET because the caller provided
        # registry_module_id explicitly).
        assert self.transport.request.call_count == 1
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/no-code-modules/nocode-abc123"
        assert body["data"]["attributes"] == {"enabled": False}

        # API requires the registry-module relationship on every PATCH.
        assert body["data"]["relationships"]["registry-module"]["data"] == {
            "type": "registry-module",
            "id": "mod-abc123",
        }

        var_opts = body["data"]["relationships"]["variable-options"]["data"]
        assert len(var_opts) == 2
        assert var_opts[0]["id"] == "vo-existing"
        assert "id" not in var_opts[1]

    def test_update_without_registry_module_id_auto_reads(self) -> None:
        # When the caller omits registry_module_id, the resource fetches the
        # current module to satisfy the API's PATCH requirement.
        read_response = _resp(_no_code_module_body(registry_module_id="mod-xyz789"))
        patch_response = _resp(_no_code_module_body(registry_module_id="mod-xyz789"))
        self.transport.request.side_effect = [read_response, patch_response]

        self.service.update(
            "nocode-abc123",
            NoCodeModuleUpdateOptions(enabled=True),
        )

        # Two requests: first GET (auto-read), then PATCH.
        assert self.transport.request.call_count == 2
        first_method, first_path = self.transport.request.call_args_list[0].args
        second_method, second_path = self.transport.request.call_args_list[1].args
        assert first_method == "GET"
        assert first_path == "/api/v2/no-code-modules/nocode-abc123"
        assert second_method == "PATCH"
        assert second_path == "/api/v2/no-code-modules/nocode-abc123"

        # PATCH body picked up the existing registry-module relationship.
        body = self.transport.request.call_args_list[1].kwargs["json_body"]
        assert body["data"]["relationships"]["registry-module"]["data"] == {
            "type": "registry-module",
            "id": "mod-xyz789",
        }

    def test_update_invalid_id_raises(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            self.service.update(
                "",
                NoCodeModuleUpdateOptions(enabled=True),
            )


class TestNoCodeModuleDelete:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_delete_calls_delete_path(self) -> None:
        self.transport.request.return_value = _resp({})

        self.service.delete("nocode-abc123")

        method, path = self.transport.request.call_args.args
        assert method == "DELETE"
        assert path == "/api/v2/no-code-modules/nocode-abc123"

    def test_delete_invalid_id_raises(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            self.service.delete("")


class TestNoCodeModuleReadVariables:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_read_variables_yields_typed_records(self) -> None:
        page = {
            "data": [
                {
                    "id": "modvar-1",
                    "type": "module-variables",
                    "attributes": {
                        "name": "region",
                        "type": "string",
                        "description": "AWS region",
                        "default": "us-east-1",
                        "required": False,
                        "sensitive": False,
                        "options": ["us-east-1", "us-west-2"],
                    },
                }
            ],
            "meta": {"pagination": {"current-page": 1, "total-pages": 1}},
        }
        self.transport.request.return_value = _resp(page)

        result = list(self.service.read_variables("nocode-abc123", "1.0.0"))

        path = self.transport.request.call_args.args[1]
        assert (
            path
            == "/api/v2/no-code-modules/nocode-abc123/versions/1.0.0/module-variables"
        )
        assert len(result) == 1
        v = result[0]
        assert v.id == "modvar-1"
        assert v.name == "region"
        assert v.options == ["us-east-1", "us-west-2"]

    def test_read_variables_invalid_id(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            list(self.service.read_variables("", "1.0.0"))

    def test_read_variables_invalid_version(self) -> None:
        with pytest.raises(InvalidVersionError):
            list(self.service.read_variables("nocode-abc123", ""))


class TestNoCodeCreateWorkspace:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_minimum_payload(self) -> None:
        self.transport.request.return_value = _resp(_workspace_body())

        ws = self.service.create_workspace(
            "nocode-abc123",
            NoCodeWorkspaceCreateOptions(
                name="no-code-ws", project_id="prj-abc123"
            ),
        )

        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "POST"
        assert path == "/api/v2/no-code-modules/nocode-abc123/workspaces"
        assert body["data"]["type"] == "workspaces"
        assert body["data"]["attributes"] == {"name": "no-code-ws"}
        assert body["data"]["relationships"]["project"]["data"] == {
            "type": "projects",
            "id": "prj-abc123",
        }
        assert "vars" not in body["data"]["relationships"]
        assert ws.id == "ws-abc123"

    def test_payload_with_inline_vars(self) -> None:
        self.transport.request.return_value = _resp(_workspace_body())

        self.service.create_workspace(
            "nocode-abc123",
            NoCodeWorkspaceCreateOptions(
                name="no-code-ws",
                project_id="prj-abc123",
                description="from no-code module",
                terraform_version="1.7.0",
                vars=[
                    NoCodeWorkspaceVariable(
                        key="region",
                        value="us-east-1",
                        category=CategoryType.TERRAFORM,
                    ),
                    NoCodeWorkspaceVariable(
                        key="API_KEY",
                        value="redacted",
                        category=CategoryType.ENV,
                        sensitive=True,
                    ),
                ],
            ),
        )

        body = self.transport.request.call_args.kwargs["json_body"]
        attrs = body["data"]["attributes"]
        assert attrs["name"] == "no-code-ws"
        assert attrs["description"] == "from no-code module"
        assert attrs["terraform-version"] == "1.7.0"

        var_data = body["data"]["relationships"]["vars"]["data"]
        assert len(var_data) == 2
        assert var_data[0] == {
            "type": "vars",
            "attributes": {
                "key": "region",
                "value": "us-east-1",
                "category": "terraform",
            },
        }
        assert var_data[1]["attributes"]["sensitive"] is True
        assert var_data[1]["attributes"]["category"] == "env"

    def test_agent_execution_mode_requires_agent_pool_id(self) -> None:
        with pytest.raises(RequiredAgentPoolIDError):
            self.service.create_workspace(
                "nocode-abc123",
                NoCodeWorkspaceCreateOptions(
                    name="no-code-ws",
                    project_id="prj-abc123",
                    execution_mode=ExecutionMode.AGENT,
                ),
            )

    def test_agent_execution_mode_with_agent_pool_id_succeeds(self) -> None:
        self.transport.request.return_value = _resp(_workspace_body())

        self.service.create_workspace(
            "nocode-abc123",
            NoCodeWorkspaceCreateOptions(
                name="no-code-ws",
                project_id="prj-abc123",
                execution_mode=ExecutionMode.AGENT,
                agent_pool_id="apool-abc123",
            ),
        )

        attrs = self.transport.request.call_args.kwargs["json_body"]["data"][
            "attributes"
        ]
        assert attrs["execution-mode"] == "agent"
        assert attrs["agent-pool-id"] == "apool-abc123"

    def test_missing_name_raises(self) -> None:
        with pytest.raises(RequiredNameError):
            self.service.create_workspace(
                "nocode-abc123",
                NoCodeWorkspaceCreateOptions(name="", project_id="prj-abc123"),
            )

    def test_missing_project_id_raises(self) -> None:
        with pytest.raises(RequiredProjectError):
            self.service.create_workspace(
                "nocode-abc123",
                NoCodeWorkspaceCreateOptions(name="no-code-ws", project_id=""),
            )

    def test_invalid_module_id_raises(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            self.service.create_workspace(
                "",
                NoCodeWorkspaceCreateOptions(
                    name="no-code-ws", project_id="prj-abc123"
                ),
            )


class TestNoCodeUpgradeWorkspace:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_upgrade_without_vars(self) -> None:
        self.transport.request.return_value = _resp(_upgrade_body())

        result = self.service.upgrade_workspace("nocode-abc123", "ws-abc123")

        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "POST"
        assert (
            path
            == "/api/v2/no-code-modules/nocode-abc123/workspaces/ws-abc123/upgrade"
        )
        assert body == {"data": {"type": "workspaces", "attributes": {}}}
        assert result.id == "wsu-abc123"
        assert result.status == "planned"
        assert result.plan_url == "https://app.terraform.io/plan/abc"
        assert result.workspace is not None
        assert result.workspace.id == "ws-abc123"

    def test_upgrade_with_vars(self) -> None:
        self.transport.request.return_value = _resp(_upgrade_body())

        self.service.upgrade_workspace(
            "nocode-abc123",
            "ws-abc123",
            NoCodeWorkspaceUpgradeOptions(
                vars=[
                    NoCodeWorkspaceVariable(
                        key="region",
                        value="us-west-2",
                        category=CategoryType.TERRAFORM,
                    ),
                ]
            ),
        )

        body = self.transport.request.call_args.kwargs["json_body"]
        var_data = body["data"]["relationships"]["vars"]["data"]
        assert var_data[0]["attributes"]["value"] == "us-west-2"

    def test_invalid_module_id(self) -> None:
        with pytest.raises(InvalidNoCodeModuleIDError):
            self.service.upgrade_workspace("", "ws-abc123")

    def test_invalid_workspace_id(self) -> None:
        with pytest.raises(InvalidWorkspaceIDError):
            self.service.upgrade_workspace("nocode-abc123", "")


class TestNoCodeReadAndConfirmUpgrade:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = NoCodeModules(self.transport)

    def test_read_upgrade(self) -> None:
        self.transport.request.return_value = _resp(
            _upgrade_body(status="planned_and_finished")
        )

        result = self.service.read_workspace_upgrade(
            "nocode-abc123", "ws-abc123", "wsu-abc123"
        )

        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == (
            "/api/v2/no-code-modules/nocode-abc123/workspaces/"
            "ws-abc123/upgrade/wsu-abc123"
        )
        assert result.status == "planned_and_finished"

    def test_confirm_upgrade_returns_none_and_ignores_plain_text(self) -> None:
        # The API returns a plain-text body. The resource should not try to
        # parse it; status code alone signals success.
        r = Mock()
        r.json.side_effect = ValueError("not JSON")
        r.text = "Workspace update completed"
        self.transport.request.return_value = r

        result = self.service.confirm_workspace_upgrade(
            "nocode-abc123", "ws-abc123", "wsu-abc123"
        )

        method, path = self.transport.request.call_args.args
        assert method == "POST"
        assert path == (
            "/api/v2/no-code-modules/nocode-abc123/workspaces/"
            "ws-abc123/upgrade/wsu-abc123"
        )
        assert result is None

    def test_read_upgrade_invalid_upgrade_id(self) -> None:
        with pytest.raises(InvalidWorkspaceUpgradeIDError):
            self.service.read_workspace_upgrade(
                "nocode-abc123", "ws-abc123", ""
            )

    def test_confirm_upgrade_invalid_workspace_id(self) -> None:
        with pytest.raises(InvalidWorkspaceIDError):
            self.service.confirm_workspace_upgrade(
                "nocode-abc123", "", "wsu-abc123"
            )


class TestWorkspaceAgentPoolParserFix:
    """Regression test for the workspace parser bug fixed alongside this
    feature. Prior to the fix, the parser wrote ``attr["agent_pools"]``
    (plural) while the Workspace model declares ``agent_pool`` (singular),
    so the relationship was always silently dropped.
    """

    def test_agent_pool_relationship_populated_on_parsed_workspace(self) -> None:
        from pytfe.resources.workspaces import _ws_from

        data = {
            "id": "ws-agent",
            "type": "workspaces",
            "attributes": {"name": "agent-ws", "execution-mode": "agent"},
            "relationships": {
                "agent-pool": {
                    "data": {"type": "agent-pools", "id": "apool-abc123"},
                },
            },
        }

        ws = _ws_from(data)

        assert ws.agent_pool is not None
        assert ws.agent_pool.id == "apool-abc123"
