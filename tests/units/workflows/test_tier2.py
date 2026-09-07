# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Tier-2 workflows: state, fleet, governance, admin, registry."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pytfe.errors import NotFound, TFEError, UnsupportedInCloud
from pytfe.models.registry_provider_platform import RegistryProviderPlatform
from pytfe.models.registry_provider_version import RegistryProviderVersion
from pytfe.models.state_version import StateVersion
from pytfe.models.workspace import Workspace
from pytfe.workflows import (
    OIDC_VARIABLES,
    ProviderPlatformSpec,
    VariableSpec,
    WorkspaceSpec,
    bulk_update,
    bulk_variable_rotate,
    download_state,
    is_hcp_terraform,
    lock,
    migrate_state,
    org_inventory,
    publish_provider_version,
    push_state,
    rollback_state,
    setup_oidc_dynamic_credentials,
    state_inventory,
    teardown_workspace,
    tfe_health,
    token_audit,
    unlock,
)

STATE = {
    "version": 4,
    "serial": 7,
    "lineage": "abc-123",
    "terraform_version": "1.9.5",
    "resources": [
        {
            "mode": "managed",
            "type": "aws_s3_bucket",
            "name": "logs",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
        },
        {
            "mode": "managed",
            "type": "aws_iam_role",
            "name": "app",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
        },
    ],
}


def make_workspace(**kw: Any) -> Workspace:
    payload: dict[str, Any] = {"id": "ws-1", "name": "web"}
    payload.update(kw)
    return Workspace.model_validate(payload)


def make_state_version(**kw: Any) -> StateVersion:
    payload: dict[str, Any] = {
        "id": "sv-1",
        "serial": 7,
        "resources-processed": True,
        "terraform-version": "1.9.5",
    }
    payload.update(kw)
    return StateVersion.model_validate(payload)


def stub_state(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace()
    client.state_versions.read_current.return_value = make_state_version()
    client.state_versions.download.return_value = json.dumps(STATE).encode()


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------


def test_download_state_parses_and_hides_body(client: Any) -> None:
    stub_state(client)
    result = download_state(client, "ws-1")
    assert result.serial == 7
    assert result.lineage == "abc-123"
    summary = result.summary()
    assert summary["resource_count"] == 2
    # The state body is large and may hold secrets; it must not be in summary().
    assert "state" not in summary
    json.dumps(summary)


def test_state_inventory_falls_back_to_state(client: Any) -> None:
    stub_state(client)
    client.workspace_resources.list.side_effect = TFEError("not available")
    inventory = state_inventory(client, "ws-1")
    assert inventory.by_type == {"aws_s3_bucket": 1, "aws_iam_role": 1}
    # The full provider source address is kept; it is unambiguous across
    # registries in a way that a bare "hashicorp/aws" is not.
    assert inventory.by_provider == {"registry.terraform.io/hashicorp/aws": 2}


def test_push_state_is_gated(client: Any) -> None:
    stub_state(client)
    result = push_state(client, "ws-1", STATE)
    assert result.action == "awaiting_confirmation"
    client.state_versions.upload.assert_not_called()
    client.workspaces.lock.assert_not_called()


def test_push_state_refuses_a_lineage_mismatch(client: Any) -> None:
    stub_state(client)
    foreign = dict(STATE, lineage="different-lineage")
    result = push_state(client, "ws-1", foreign, confirmed=True)
    assert result.action == "refused"
    assert result.ok is False
    assert "lineage mismatch" in result.warnings[0]
    client.state_versions.upload.assert_not_called()


def test_push_state_bumps_the_serial_floor(client: Any) -> None:
    stub_state(client)
    stale = dict(STATE, serial=3)
    client.state_versions.upload.return_value = make_state_version(id="sv-2", serial=8)
    result = push_state(client, "ws-1", stale, confirmed=True)
    # Incoming serial 3 is below the current 7, so it is raised to 8.
    assert result.serial_after == 8
    options = client.state_versions.upload.call_args.kwargs["options"]
    assert options.serial == 8
    assert options.md5


def test_push_state_always_unlocks(client: Any) -> None:
    stub_state(client)
    client.state_versions.upload.side_effect = TFEError("upload rejected")
    with pytest.raises(TFEError, match="upload rejected"):
        push_state(client, "ws-1", STATE, confirmed=True)
    client.workspaces.unlock.assert_called_once_with("ws-1")


def test_push_state_reports_a_stranded_lock(client: Any) -> None:
    """An unlock failure must not mask the upload error, but must be visible."""
    stub_state(client)
    client.state_versions.upload.side_effect = TFEError("upload rejected")
    client.workspaces.unlock.side_effect = TFEError("unlock failed")
    with pytest.raises(TFEError, match="upload rejected"):
        push_state(client, "ws-1", STATE, confirmed=True)


def test_rollback_uses_the_native_endpoint(client: Any) -> None:
    stub_state(client)
    client.state_versions.list.return_value = iter(
        [
            make_state_version(id="sv-3", serial=9),
            make_state_version(id="sv-2", serial=8),
        ]
    )
    client.state_versions.rollback.return_value = make_state_version(
        id="sv-4", serial=10
    )
    result = rollback_state(client, "ws-1", steps_back=1, confirmed=True)
    client.state_versions.rollback.assert_called_once_with("ws-1", "sv-2")
    assert result.action == "pushed"


def test_rollback_is_gated(client: Any) -> None:
    stub_state(client)
    client.state_versions.list.return_value = iter(
        [make_state_version(id="sv-3"), make_state_version(id="sv-2")]
    )
    result = rollback_state(client, "ws-1")
    assert result.action == "awaiting_confirmation"
    client.state_versions.rollback.assert_not_called()


def test_migrate_state_warns_when_target_has_state(client: Any) -> None:
    stub_state(client)
    client.state_versions.upload.return_value = make_state_version(id="sv-9", serial=8)
    result = migrate_state(client, "ws-source", "ws-target", confirmed=True)
    assert any("already has state" in w for w in result.warnings)


# --------------------------------------------------------------------------
# lock / unlock
# --------------------------------------------------------------------------


def test_lock_is_idempotent(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(locked=True)
    result = lock(client, "ws-1")
    assert result.action == "unchanged"
    client.workspaces.lock.assert_not_called()


def test_unlock_is_idempotent(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(locked=False)
    result = unlock(client, "ws-1")
    assert result.action == "unchanged"
    client.workspaces.unlock.assert_not_called()


def test_force_unlock_uses_the_force_endpoint(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(locked=True)
    unlock(client, "ws-1", force=True)
    client.workspaces.force_unlock.assert_called_once_with("ws-1")
    client.workspaces.unlock.assert_not_called()


# --------------------------------------------------------------------------
# teardown
# --------------------------------------------------------------------------


def test_teardown_is_gated(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(**{"resource-count": 5})
    result = teardown_workspace(client, "ws-1")
    assert result.action == "awaiting_confirmation"
    client.workspaces.delete_by_id.assert_not_called()
    client.workspaces.safe_delete_by_id.assert_not_called()


def test_teardown_refuses_while_resources_remain(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(**{"resource-count": 5})
    result = teardown_workspace(client, "ws-1", destroy_first=False, confirmed=True)
    assert result.action == "refused"
    assert result.ok is False
    client.workspaces.delete_by_id.assert_not_called()


def test_teardown_deletes_an_empty_workspace(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(**{"resource-count": 0})
    result = teardown_workspace(client, "ws-1", confirmed=True)
    assert result.action == "deleted"
    client.workspaces.safe_delete_by_id.assert_called_once_with("ws-1")


def test_teardown_force_uses_hard_delete(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(**{"resource-count": 3})
    result = teardown_workspace(
        client, "ws-1", destroy_first=False, force=True, confirmed=True
    )
    assert result.action == "deleted"
    client.workspaces.delete_by_id.assert_called_once_with("ws-1")


# --------------------------------------------------------------------------
# fleet
# --------------------------------------------------------------------------


def test_bulk_update_is_gated(client: Any) -> None:
    client.workspaces.list.return_value = iter(
        [make_workspace(id="ws-1", name="a"), make_workspace(id="ws-2", name="b")]
    )
    result = bulk_update(client, "acme", spec=WorkspaceSpec(auto_apply=False))
    assert result.skipped == 2
    assert result.succeeded == 0
    client.workspaces.update_by_id.assert_not_called()


def test_bulk_variable_rotate_is_gated(client: Any) -> None:
    client.workspaces.list.return_value = iter([make_workspace()])
    result = bulk_variable_rotate(
        client, "acme", variable=VariableSpec(key="K", value="v")
    )
    assert result.skipped == 1
    client.variables.create.assert_not_called()


def test_fleet_survives_one_failure(client: Any) -> None:
    client.workspaces.list.return_value = iter(
        [make_workspace(id="ws-1", name="a"), make_workspace(id="ws-2", name="b")]
    )
    calls: list[str] = []

    def read_by_id(workspace_id: str) -> Workspace:
        calls.append(workspace_id)
        if workspace_id == "ws-1":
            raise TFEError("boom", status=500)
        return make_workspace(id=workspace_id, name="b")

    client.workspaces.read_by_id.side_effect = read_by_id
    client.runs.list.return_value = iter([])
    client.state_versions.read_current.side_effect = NotFound("none")

    inventory = org_inventory(client, "acme", concurrency=2)
    # One workspace failed; the other still produced a row.
    assert len(inventory.rows) == 1
    assert any("boom" in w for w in inventory.warnings)


def test_org_inventory_renders_csv(client: Any) -> None:
    client.workspaces.list.return_value = iter([make_workspace()])
    client.workspaces.read_by_id.return_value = make_workspace()
    client.runs.list.return_value = iter([])
    client.state_versions.read_current.side_effect = NotFound("none")
    csv = org_inventory(client, "acme").to_csv()
    assert csv.splitlines()[0].startswith("id,name,health")
    assert "web" in csv


# --------------------------------------------------------------------------
# governance
# --------------------------------------------------------------------------


def test_oidc_writes_the_documented_variables(client: Any) -> None:
    client.variables.list.return_value = iter([])
    result = setup_oidc_dynamic_credentials(
        client, "ws-1", provider="aws", role="arn:aws:iam::1:role/tfc"
    )
    written = sorted(result.created)
    assert written == ["TFC_AWS_PROVIDER_AUTH", "TFC_AWS_RUN_ROLE_ARN"]
    for call in client.variables.create.call_args_list:
        assert call.args[1].category == "env"


def test_oidc_rejects_an_unknown_provider(client: Any) -> None:
    with pytest.raises(ValueError, match="unknown provider"):
        setup_oidc_dynamic_credentials(client, "ws-1", provider="oracle")  # type: ignore[arg-type]


def test_oidc_rejects_an_unknown_setting(client: Any) -> None:
    with pytest.raises(ValueError, match="unknown setting"):
        setup_oidc_dynamic_credentials(client, "ws-1", provider="aws", rolearn="typo")


def test_oidc_variable_table_covers_four_providers() -> None:
    assert set(OIDC_VARIABLES) == {"aws", "gcp", "azure", "vault"}
    for mapping in OIDC_VARIABLES.values():
        assert mapping["enable"].endswith("_PROVIDER_AUTH")


def test_token_audit_never_returns_values(client: Any) -> None:
    from pytfe.models.organization_token import OrganizationToken

    client.organization_tokens.read.return_value = OrganizationToken.model_validate(
        {
            "id": "at-1",
            "token": "SUPERSECRET",
            "description": "org",
            "created_at": "2026-01-01T00:00:00Z",
        }
    )
    client.team_tokens.list.return_value = iter([])
    client.agent_pools.list.return_value = iter([])

    audit = token_audit(client, "acme")
    rendered = repr(audit.tokens) + repr(audit.summary())
    assert "SUPERSECRET" not in rendered
    assert audit.tokens[0].id == "at-1"


def test_token_audit_reports_the_user_token_gap(client: Any) -> None:
    client.organization_tokens.read.side_effect = NotFound("none")
    client.team_tokens.list.return_value = iter([])
    client.agent_pools.list.return_value = iter([])
    audit = token_audit(client, "acme")
    assert any("user API tokens are not included" in w for w in audit.warnings)


# --------------------------------------------------------------------------
# admin
# --------------------------------------------------------------------------


def test_admin_workflows_refuse_hcp_terraform(client: Any) -> None:
    from pytfe import TFEConfig

    client.config = TFEConfig(address="https://app.terraform.io", token="t")
    assert is_hcp_terraform(client) is True
    with pytest.raises(UnsupportedInCloud):
        tfe_health(client)


def test_tfe_health_counts_the_queue(client: Any) -> None:
    from pytfe import TFEConfig
    from pytfe.models.admin_run import AdminRun

    client.config = TFEConfig(address="https://tfe.example.com", token="t")
    client.admin.organizations.list.return_value = iter([object(), object()])
    client.admin.users.list.return_value = iter([object()])
    client.admin.runs.list.return_value = iter(
        [
            AdminRun.model_validate({"id": "run-1", "status": "pending"}),
            AdminRun.model_validate({"id": "run-2", "status": "applied"}),
        ]
    )
    client.admin.terraform_versions.list.return_value = iter([object()])

    health = tfe_health(client)
    assert health.reachable is True
    assert health.organization_count == 2
    assert health.run_queue_depth == 1
    assert health.runs_by_status["applied"] == 1


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------


SHASUMS = b"deadbeef  terraform-provider-widget_1.0.0_linux_amd64.zip\n"


def make_provider_version(**kw: Any) -> RegistryProviderVersion:
    payload: dict[str, Any] = {
        "id": "rpv-1",
        "version": "1.0.0",
        "key-id": "KEY",
        "shasums-uploaded": True,
        "shasums-sig-uploaded": True,
        "links": {
            "shasums-upload": "https://archivist.terraform.io/v1/object/sha",
            "shasums-sig-upload": "https://archivist.terraform.io/v1/object/sig",
        },
    }
    payload.update(kw)
    return RegistryProviderVersion.model_validate(payload)


def make_platform(**kw: Any) -> RegistryProviderPlatform:
    payload: dict[str, Any] = {
        "id": "rpp-1",
        "os": "linux",
        "arch": "amd64",
        "filename": "terraform-provider-widget_1.0.0_linux_amd64.zip",
        "shasum": "deadbeef",
        "links": {
            "provider-binary-upload": "https://archivist.terraform.io/v1/object/bin"
        },
    }
    payload.update(kw)
    return RegistryProviderPlatform.model_validate(payload)


def stub_provider(client: Any) -> None:
    client.registry_provider_versions.list.return_value = iter([])
    client.registry_provider_versions.create.return_value = make_provider_version()
    client.registry_provider_versions.read.return_value = make_provider_version()
    client.registry_provider_platforms.create.return_value = make_platform()


def test_publish_provider_uploads_checksums_and_binaries(client: Any) -> None:
    """The full private-provider publish sequence."""
    stub_provider(client)
    result = publish_provider_version(
        client,
        "acme",
        "widget",
        "1.0.0",
        gpg_key_id="KEY",
        shasums=SHASUMS,
        shasums_sig=b"SIGNATURE",
        platforms=[
            ProviderPlatformSpec(
                os="linux",
                arch="amd64",
                filename="terraform-provider-widget_1.0.0_linux_amd64.zip",
                shasum="deadbeef",
                binary=b"PK\x03\x04",
            )
        ],
    )
    assert result.action == "published"
    assert result.ok is True
    client.registry_provider_versions.upload_shasums.assert_called_once()
    client.registry_provider_versions.upload_shasums_sig.assert_called_once()
    client.registry_provider_platforms.upload_binary.assert_called_once()
    # The platform binary must be uploaded for the platform that was created.
    platform, binary = client.registry_provider_platforms.upload_binary.call_args.args
    assert platform.os == "linux"
    assert binary == b"PK\x03\x04"


def test_publish_provider_creates_the_provider_when_absent(client: Any) -> None:
    stub_provider(client)
    client.registry_providers.read.side_effect = NotFound("nope")
    publish_provider_version(
        client,
        "acme",
        "widget",
        "1.0.0",
        gpg_key_id="KEY",
        shasums=SHASUMS,
        shasums_sig=b"SIG",
        platforms=[
            ProviderPlatformSpec(
                os="linux", arch="amd64", filename="p.zip", shasum="d", binary=b"x"
            )
        ],
    )
    client.registry_providers.create.assert_called_once()
    options = client.registry_providers.create.call_args.args[1]
    # The private registry requires namespace == organization.
    assert options.namespace == "acme"


def test_publish_provider_is_idempotent(client: Any) -> None:
    stub_provider(client)
    client.registry_provider_versions.list.return_value = iter(
        [make_provider_version()]
    )
    result = publish_provider_version(
        client,
        "acme",
        "widget",
        "1.0.0",
        gpg_key_id="KEY",
        shasums=SHASUMS,
        shasums_sig=b"SIG",
        platforms=[
            ProviderPlatformSpec(
                os="linux", arch="amd64", filename="p.zip", shasum="d", binary=b"x"
            )
        ],
    )
    assert result.action == "unchanged"
    client.registry_provider_versions.create.assert_not_called()
    client.registry_provider_versions.upload_shasums.assert_not_called()


def test_publish_provider_rejects_no_platforms(client: Any) -> None:
    """A version with no platform binaries is unusable, so refuse early."""
    with pytest.raises(ValueError, match="platforms must not be empty"):
        publish_provider_version(
            client,
            "acme",
            "widget",
            "1.0.0",
            gpg_key_id="KEY",
            shasums=SHASUMS,
            shasums_sig=b"SIG",
            platforms=[],
        )
    client.registry_provider_versions.create.assert_not_called()


def test_publish_provider_warns_when_upload_unconfirmed(client: Any) -> None:
    stub_provider(client)
    client.registry_provider_versions.read.return_value = make_provider_version(
        **{"shasums-uploaded": False}
    )
    result = publish_provider_version(
        client,
        "acme",
        "widget",
        "1.0.0",
        gpg_key_id="KEY",
        shasums=SHASUMS,
        shasums_sig=b"SIG",
        platforms=[
            ProviderPlatformSpec(
                os="linux", arch="amd64", filename="p.zip", shasum="d", binary=b"x"
            )
        ],
    )
    assert result.ok is False
    assert any("SHA256SUMS" in w for w in result.warnings)


def test_platform_spec_reads_from_disk(tmp_path: Any) -> None:
    binary = tmp_path / "p.zip"
    binary.write_bytes(b"ZIPDATA")
    spec = ProviderPlatformSpec(
        os="linux",
        arch="amd64",
        filename="p.zip",
        shasum="d",
        binary_path=str(binary),
    )
    assert spec.read_binary() == b"ZIPDATA"


def test_platform_spec_requires_a_source() -> None:
    spec = ProviderPlatformSpec(os="linux", arch="amd64", filename="p.zip", shasum="d")
    with pytest.raises(ValueError, match="neither binary nor binary_path"):
        spec.read_binary()


def test_platform_specs_from_a_release_dir(tmp_path: Any) -> None:
    """Pair a SHA256SUMS body with the zips actually present."""
    for name in (
        "terraform-provider-widget_1.0.0_linux_amd64.zip",
        "terraform-provider-widget_1.0.0_darwin_arm64.zip",
    ):
        (tmp_path / name).write_bytes(b"zip")
    shasums = (
        "aaa  terraform-provider-widget_1.0.0_linux_amd64.zip\n"
        "bbb  terraform-provider-widget_1.0.0_darwin_arm64.zip\n"
        "ccc  terraform-provider-widget_1.0.0_SHA256SUMS\n"
        "ddd  terraform-provider-widget_1.0.0_windows_386.zip\n"  # not on disk
    )
    specs = ProviderPlatformSpec.from_release_dir(str(tmp_path), shasums=shasums)
    assert {(s.os, s.arch) for s in specs} == {("linux", "amd64"), ("darwin", "arm64")}
    assert {s.shasum for s in specs} == {"aaa", "bbb"}


# --------------------------------------------------------------------------
# ensure_variable_set attachment idempotence
#
# Regression found by comparing against the Ansible collection, which reads the
# set's current attachments and attaches only on a miss
# (plugins/action/workspace_bootstrap.py:176-182). The first implementation here
# called apply_to_workspaces unconditionally, so a repeat call always reported
# action="updated" and issued a write.
# --------------------------------------------------------------------------


def make_variable_set(**kw: Any) -> Any:
    from pytfe.models.variable_set import VariableSet

    payload: dict[str, Any] = {"id": "varset-1", "name": "shared", "global": False}
    payload.update(kw)
    return VariableSet.model_validate(payload)


def test_variable_set_attachment_is_idempotent(client: Any) -> None:
    from pytfe.workflows import ensure_variable_set

    client.variable_sets.list.return_value = iter([make_variable_set()])
    client.variable_sets.read.return_value = make_variable_set(
        workspaces=[{"id": "ws-1", "name": "web"}]
    )
    result = ensure_variable_set(client, "acme", "shared", workspace_ids={"ws-1"})
    assert result.action == "unchanged"
    client.variable_sets.apply_to_workspaces.assert_not_called()


def test_variable_set_attaches_only_the_missing_workspaces(client: Any) -> None:
    from pytfe.workflows import ensure_variable_set

    client.variable_sets.list.return_value = iter([make_variable_set()])
    client.variable_sets.read.return_value = make_variable_set(
        workspaces=[{"id": "ws-1", "name": "web"}]
    )
    result = ensure_variable_set(
        client, "acme", "shared", workspace_ids={"ws-1", "ws-2"}
    )
    assert result.action == "updated"
    options = client.variable_sets.apply_to_workspaces.call_args.args[1]
    # Only the workspace that was not already attached.
    assert [w.id for w in options.workspaces] == ["ws-2"]
