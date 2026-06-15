# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the four confirmed admin API mismatches:
1. User action endpoint paths (underscores not hyphens).
2. ToolVersionArchitecture / archs field in version models.
3. Admin run parser — workspace relationship only (organization via compound include).
4. Admin workspace — vcs_repo_identifier from attribute, no execution_mode.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from pytfe.models.admin_run import AdminRun
from pytfe.models.admin_version import (
    OpaVersion,
    OpaVersionCreateOptions,
    SentinelVersion,
    SentinelVersionCreateOptions,
    TerraformVersion,
    TerraformVersionCreateOptions,
    TerraformVersionUpdateOptions,
    ToolVersionArchitecture,
)
from pytfe.models.admin_workspace import AdminWorkspace
from pytfe.resources.admin._runs import _AdminRuns, _parse_admin_run
from pytfe.resources.admin._users import _AdminUsers
from pytfe.resources.admin._workspaces import _parse_admin_workspace


def _transport(responses: list[Any]) -> MagicMock:
    t = MagicMock()
    mocks = []
    for body in responses:
        r = MagicMock()
        r.json.return_value = body
        mocks.append(r)
    t.request.side_effect = mocks
    return t


# ---------------------------------------------------------------------------
# Finding 1: user action endpoint paths use underscores
# ---------------------------------------------------------------------------


class TestUserActionPaths:
    def _make_user_resp(self, user_id: str = "user-abc") -> dict:
        return {
            "data": {
                "id": user_id,
                "type": "users",
                "attributes": {
                    "username": "tester",
                    "email": "tester@example.com",
                    "is-admin": False,
                    "is-suspended": False,
                    "two-factor-enabled": False,
                    "two-factor-verified": False,
                },
            }
        }

    def test_grant_admin_uses_underscore_path(self):
        t = _transport([self._make_user_resp()])
        svc = _AdminUsers(t)
        svc.grant_admin("user-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/users/user-abc/actions/grant_admin"
        )

    def test_revoke_admin_uses_underscore_path(self):
        t = _transport([self._make_user_resp()])
        svc = _AdminUsers(t)
        svc.revoke_admin("user-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/users/user-abc/actions/revoke_admin"
        )

    def test_disable_two_factor_uses_underscore_path(self):
        t = _transport([self._make_user_resp()])
        svc = _AdminUsers(t)
        svc.disable_two_factor("user-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/users/user-abc/actions/disable_two_factor"
        )

    def test_suspend_still_hyphenated(self):
        t = _transport([self._make_user_resp()])
        svc = _AdminUsers(t)
        svc.suspend("user-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/users/user-abc/actions/suspend"
        )

    def test_unsuspend_still_hyphenated(self):
        t = _transport([self._make_user_resp()])
        svc = _AdminUsers(t)
        svc.unsuspend("user-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/users/user-abc/actions/unsuspend"
        )


# ---------------------------------------------------------------------------
# Finding 2: ToolVersionArchitecture / archs field
# ---------------------------------------------------------------------------


class TestToolVersionArchitecture:
    def test_architecture_model_fields(self):
        arch = ToolVersionArchitecture(
            url="https://example.com/tf.zip", sha="abc123", os="linux", arch="amd64"
        )
        assert arch.url == "https://example.com/tf.zip"
        assert arch.sha == "abc123"
        assert arch.os == "linux"
        assert arch.arch == "amd64"

    def test_terraform_version_has_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="linux", arch="amd64")
        v = TerraformVersion(id="tv-1", version="1.9.0", archs=[arch])
        assert v.archs is not None
        assert len(v.archs) == 1
        assert v.archs[0].arch == "amd64"

    def test_terraform_version_archs_optional(self):
        v = TerraformVersion(id="tv-1", version="1.9.0", url="u", sha="s")
        assert v.archs is None

    def test_create_options_include_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="darwin", arch="arm64")
        opts = TerraformVersionCreateOptions(
            version="1.9.0", url="u", sha="s", archs=[arch]
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert "archs" in dumped
        assert dumped["archs"][0]["arch"] == "arm64"

    def test_update_options_include_archs(self):
        arch = ToolVersionArchitecture(url="u2", sha="s2", os="windows", arch="amd64")
        opts = TerraformVersionUpdateOptions(archs=[arch])
        dumped = opts.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert "archs" in dumped

    def test_opa_version_has_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="linux", arch="amd64")
        v = OpaVersion(id="ov-1", version="0.60.0", archs=[arch])
        assert v.archs is not None

    def test_opa_create_options_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="linux", arch="amd64")
        opts = OpaVersionCreateOptions(version="0.60.0", url="u", sha="s", archs=[arch])
        dumped = opts.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert "archs" in dumped

    def test_sentinel_version_has_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="linux", arch="amd64")
        v = SentinelVersion(id="sv-1", version="0.26.0", archs=[arch])
        assert v.archs is not None

    def test_sentinel_create_options_archs(self):
        arch = ToolVersionArchitecture(url="u", sha="s", os="linux", arch="amd64")
        opts = SentinelVersionCreateOptions(
            version="0.26.0", url="u", sha="s", archs=[arch]
        )
        dumped = opts.model_dump(by_alias=True, exclude_none=True, mode="json")
        assert "archs" in dumped

    def test_version_parsed_from_api_with_archs(self):
        raw = {
            "id": "tv-1",
            "type": "terraform-versions",
            "attributes": {
                "version": "1.9.0",
                "url": "https://example.com/tf.zip",
                "sha": "deadbeef",
                "official": True,
                "enabled": True,
                "beta": False,
                "deprecated": False,
                "usage": 5,
                "archs": [
                    {"url": "u1", "sha": "s1", "os": "linux", "arch": "amd64"},
                    {"url": "u2", "sha": "s2", "os": "darwin", "arch": "arm64"},
                ],
            },
        }
        attrs = raw["attributes"]
        v = TerraformVersion.model_validate({"id": raw["id"], **attrs})
        assert v.archs is not None
        assert len(v.archs) == 2
        assert v.archs[1].os == "darwin"


# ---------------------------------------------------------------------------
# Finding 3: admin run parser — workspace rel only, no top-level org rel
# ---------------------------------------------------------------------------


class TestAdminRunParser:
    def _make_run_data(self, run_id: str = "run-abc", ws_id: str = "ws-xyz") -> dict:
        return {
            "id": run_id,
            "type": "runs",
            "attributes": {
                "status": "pending",
                "has-changes": False,
                "plan-only": False,
            },
            "relationships": {
                "workspace": {"data": {"id": ws_id, "type": "workspaces"}},
                # no top-level 'organization' key in standard response
            },
        }

    def test_workspace_id_populated(self):
        data = self._make_run_data(ws_id="ws-xyz")
        run = _parse_admin_run(data)
        assert run.workspace_id == "ws-xyz"

    def test_organization_name_none_without_include(self):
        data = self._make_run_data()
        run = _parse_admin_run(data)
        assert run.organization_name is None

    def test_status_parsed(self):
        data = self._make_run_data()
        run = _parse_admin_run(data)
        from pytfe.models.run import RunStatus

        assert run.status == RunStatus.Run_Pending

    def test_model_has_no_workspace_name_field(self):
        assert not hasattr(AdminRun.model_fields.get("workspace_name", None), "default")

    def test_force_cancel_path(self):
        t = MagicMock()
        r = MagicMock()
        r.json.return_value = None
        t.request.return_value = r
        svc = _AdminRuns(t)
        svc.force_cancel("run-abc")
        t.request.assert_called_once_with(
            "POST", "/api/v2/admin/runs/run-abc/actions/force-cancel"
        )


# ---------------------------------------------------------------------------
# Finding 4: admin workspace — vcs_repo_identifier from attr, no execution_mode
# ---------------------------------------------------------------------------


class TestAdminWorkspaceParser:
    def _make_ws_data(
        self,
        ws_id: str = "ws-abc",
        org_id: str = "my-org",
        vcs_identifier: str | None = "github/my-repo",
        run_id: str | None = "run-123",
    ) -> dict:
        attrs: dict = {"name": "my-workspace", "locked": False}
        if vcs_identifier:
            attrs["vcs-repo"] = {"identifier": vcs_identifier}
        rels: dict = {
            "organization": {"data": {"id": org_id, "type": "organizations"}},
        }
        if run_id:
            rels["current-run"] = {"data": {"id": run_id, "type": "runs"}}
        return {
            "id": ws_id,
            "type": "workspaces",
            "attributes": attrs,
            "relationships": rels,
        }

    def test_organization_lifted_from_relationship(self):
        data = self._make_ws_data(org_id="prab-org")
        ws = _parse_admin_workspace(data)
        assert ws.organization_name == "prab-org"

    def test_current_run_id_lifted(self):
        data = self._make_ws_data(run_id="run-999")
        ws = _parse_admin_workspace(data)
        assert ws.current_run_id == "run-999"

    def test_vcs_repo_identifier_parsed(self):
        data = self._make_ws_data(vcs_identifier="hashicorp/terraform")
        ws = _parse_admin_workspace(data)
        assert ws.vcs_repo_identifier == "hashicorp/terraform"

    def test_vcs_repo_none_when_absent(self):
        data = self._make_ws_data(vcs_identifier=None)
        ws = _parse_admin_workspace(data)
        assert ws.vcs_repo_identifier is None

    def test_current_run_none_when_absent(self):
        data = self._make_ws_data(run_id=None)
        ws = _parse_admin_workspace(data)
        assert ws.current_run_id is None

    def test_no_execution_mode_field(self):
        assert "execution_mode" not in AdminWorkspace.model_fields

    def test_basic_fields(self):
        data = self._make_ws_data()
        ws = _parse_admin_workspace(data)
        assert ws.id == "ws-abc"
        assert ws.name == "my-workspace"
        assert ws.locked is False
