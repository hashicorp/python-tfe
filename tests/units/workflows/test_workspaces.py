# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Workspace workflows: convergence, idempotence, dry-run, and field mapping."""

from __future__ import annotations

from typing import Any

import pytest

from pytfe.errors import NotFound, WorkspaceNotFound
from pytfe.models.variable import Variable
from pytfe.models.workspace import Workspace
from pytfe.workflows import (
    VariableSpec,
    WorkspaceSpec,
    ensure_variables,
    ensure_workspace,
    find_workspaces,
    workspace_status,
)


def make_workspace(**kw: Any) -> Workspace:
    payload: dict[str, Any] = {"id": "ws-1", "name": "web"}
    payload.update(kw)
    return Workspace.model_validate(payload)


def make_variable(**kw: Any) -> Variable:
    payload: dict[str, Any] = {
        "id": "var-1",
        "key": "region",
        "value": "eu-west-1",
        "category": "terraform",
        "sensitive": False,
        "hcl": False,
    }
    payload.update(kw)
    return Variable.model_validate(payload)


def _write_calls(client: Any) -> int:
    return (
        client.workspaces.create.call_count
        + client.workspaces.update_by_id.call_count
        + client.workspaces.add_tags.call_count
        + client.workspaces.remove_tags.call_count
        + client.variables.create.call_count
        + client.variables.update.call_count
        + client.variables.delete.call_count
    )


# --------------------------------------------------------------------------
# find_workspaces
# --------------------------------------------------------------------------


def test_find_workspaces_filters_locally_on_version(client: Any) -> None:
    client.workspaces.list.return_value = iter(
        [
            make_workspace(id="ws-1", name="a", **{"terraform-version": "1.9.5"}),
            make_workspace(id="ws-2", name="b", **{"terraform-version": "1.8.0"}),
        ]
    )
    found = find_workspaces(client, "acme", terraform_version="1.9.5")
    assert [w.name for w in found.items] == ["a"]


def test_find_workspaces_applies_a_glob(client: Any) -> None:
    client.workspaces.list.return_value = iter(
        [
            make_workspace(id="ws-1", name="prod-api"),
            make_workspace(id="ws-2", name="dev-api"),
        ]
    )
    found = find_workspaces(client, "acme", name_pattern="prod-*")
    assert [w.name for w in found.items] == ["prod-api"]


def test_find_workspaces_marks_truncation(client: Any) -> None:
    client.workspaces.list.return_value = iter(
        [make_workspace(id=f"ws-{i}", name=f"w{i}") for i in range(5)]
    )
    found = find_workspaces(client, "acme", limit=2)
    assert len(found.items) == 2
    assert found.truncated is True
    assert found.summary()["truncated"] is True


# --------------------------------------------------------------------------
# ensure_workspace
# --------------------------------------------------------------------------


def test_creates_when_absent(client: Any) -> None:
    client.workspaces.read.side_effect = NotFound("nope")
    client.workspaces.create.return_value = make_workspace()

    result = ensure_workspace(client, "acme", "web")
    assert result.action == "created"
    client.workspaces.create.assert_called_once()


def test_second_call_is_a_no_op(client: Any) -> None:
    """Idempotence: converging an already-correct workspace writes nothing."""
    client.workspaces.read.return_value = make_workspace(
        **{"terraform-version": "1.9.5", "auto-apply": False}
    )
    spec = WorkspaceSpec(terraform_version="1.9.5", auto_apply=False)

    result = ensure_workspace(client, "acme", "web", spec=spec)
    assert result.action == "unchanged"
    assert result.changed is False
    assert _write_calls(client) == 0


def test_updates_only_the_managed_fields(client: Any) -> None:
    client.workspaces.read.return_value = make_workspace(
        **{
            "terraform-version": "1.8.0",
            "auto-apply": True,
            "working-directory": "infra",
        }
    )
    client.workspaces.update_by_id.return_value = make_workspace()

    result = ensure_workspace(
        client, "acme", "web", spec=WorkspaceSpec(terraform_version="1.9.5")
    )
    assert result.action == "updated"
    assert [c.field for c in result.changes] == ["terraform_version"]

    options = client.workspaces.update_by_id.call_args.args[1]
    payload = options.model_dump(by_alias=True, exclude_none=True)
    # working_directory was never mentioned by the spec, so it must not be sent.
    assert "working-directory" not in payload
    assert payload["terraform-version"] == "1.9.5"


def test_dry_run_makes_no_writes(client: Any) -> None:
    client.workspaces.read.return_value = make_workspace(
        **{"terraform-version": "1.8.0"}
    )
    result = ensure_workspace(
        client,
        "acme",
        "web",
        spec=WorkspaceSpec(terraform_version="1.9.5"),
        dry_run=True,
    )
    assert result.action == "would_update"
    assert [c.field for c in result.changes] == ["terraform_version"]
    assert _write_calls(client) == 0


def test_dry_run_reports_a_creation(client: Any) -> None:
    client.workspaces.read.side_effect = NotFound("nope")
    result = ensure_workspace(client, "acme", "web", dry_run=True)
    assert result.action == "would_create"
    assert _write_calls(client) == 0


def test_project_id_reaches_the_wire(client: Any) -> None:
    """Regression: the options model has `project`, not `project_id`.

    Because WorkspaceCreateOptions defaults to extra='ignore', passing
    project_id= would be silently discarded and the workspace created with no
    project at all - no error raised.
    """
    client.workspaces.read.side_effect = NotFound("nope")
    client.workspaces.create.return_value = make_workspace()

    ensure_workspace(client, "acme", "web", spec=WorkspaceSpec(project_id="prj-1"))
    options = client.workspaces.create.call_args.args[1]
    # workspaces.create reads options.project.id and emits a JSON:API
    # relationship from it (resources/workspaces.py:560-563), so carrying the
    # id on a Project object is the contract that matters here.
    assert options.project is not None
    assert options.project.id == "prj-1"


def test_tags_go_through_add_tags_not_tag_bindings(client: Any) -> None:
    """Regression: workspaces.py drops any TagBinding with a falsy value."""
    client.workspaces.read.side_effect = NotFound("nope")
    client.workspaces.create.return_value = make_workspace()

    ensure_workspace(client, "acme", "web", spec=WorkspaceSpec(tags={"env:prod"}))
    client.workspaces.add_tags.assert_called_once()
    options = client.workspaces.add_tags.call_args.args[1]
    assert [t.name for t in options.tags] == ["env:prod"]


def test_tags_converge_with_set_semantics(client: Any) -> None:
    client.workspaces.read.return_value = make_workspace(
        **{"tag-names": ["keep", "drop"]}
    )
    ensure_workspace(client, "acme", "web", spec=WorkspaceSpec(tags={"keep", "add"}))
    added = client.workspaces.add_tags.call_args.args[1]
    removed = client.workspaces.remove_tags.call_args.args[1]
    assert [t.name for t in added.tags] == ["add"]
    assert [t.name for t in removed.tags] == ["drop"]


def test_agent_mode_requires_a_pool(client: Any) -> None:
    client.workspaces.read.side_effect = NotFound("nope")
    with pytest.raises(ValueError, match="agent_pool_id"):
        ensure_workspace(
            client, "acme", "web", spec=WorkspaceSpec(execution_mode="agent")
        )
    assert _write_calls(client) == 0


def test_vcs_repo_needs_exactly_one_credential(client: Any) -> None:
    from pytfe.workflows import VCSRepoSpec

    client.workspaces.read.side_effect = NotFound("nope")
    spec = WorkspaceSpec(
        vcs_repo=VCSRepoSpec(
            identifier="acme/infra",
            oauth_token_id="ot-1",
            github_app_installation_id="ghain-1",
        )
    )
    with pytest.raises(ValueError, match="exactly one"):
        ensure_workspace(client, "acme", "web", spec=spec)


def test_unknown_spec_field_is_rejected_loudly(client: Any) -> None:
    """The whole point of extra='forbid' on the spec models."""
    with pytest.raises(Exception, match="terraform_versionn|extra_forbidden"):
        WorkspaceSpec(terraform_versionn="1.9.5")  # type: ignore[call-arg]


# --------------------------------------------------------------------------
# workspace_status
# --------------------------------------------------------------------------


def test_status_reports_locked(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace(locked=True)
    client.runs.list.return_value = iter([])
    client.state_versions.read_current.side_effect = NotFound("none")
    status = workspace_status(client, "ws-1")
    assert status.health == "locked"


def test_status_reports_never_run(client: Any) -> None:
    client.workspaces.read_by_id.return_value = make_workspace()
    client.runs.list.return_value = iter([])
    client.state_versions.read_current.side_effect = NotFound("none")
    status = workspace_status(client, "ws-1")
    assert status.health == "never_run"


def test_status_reports_errored(client: Any) -> None:
    from pytfe.models.run import Run

    client.workspaces.read_by_id.return_value = make_workspace()
    client.runs.list.return_value = iter(
        [Run.model_validate({"id": "run-1", "status": "errored"})]
    )
    client.state_versions.read_current.side_effect = NotFound("none")
    status = workspace_status(client, "ws-1")
    assert status.health == "errored"
    assert status.summary()["latest_run_status"] == "errored"


def test_resolution_failure_is_actionable(client: Any) -> None:
    client.workspaces.read_by_id.side_effect = NotFound("nope")
    with pytest.raises(WorkspaceNotFound) as excinfo:
        workspace_status(client, "ws-missing")
    assert excinfo.value.hint and "find_workspaces" in excinfo.value.hint


def test_resolution_needs_an_identifier(client: Any) -> None:
    with pytest.raises(WorkspaceNotFound, match="workspace_id"):
        workspace_status(client)


# --------------------------------------------------------------------------
# ensure_variables
# --------------------------------------------------------------------------


def test_creates_missing_variables(client: Any) -> None:
    client.variables.list.return_value = iter([])
    result = ensure_variables(
        client, "ws-1", [VariableSpec(key="region", value="eu-west-1")]
    )
    assert result.created == ["region"]
    client.variables.create.assert_called_once()


def test_variables_are_idempotent(client: Any) -> None:
    client.variables.list.return_value = iter([make_variable()])
    result = ensure_variables(
        client, "ws-1", [VariableSpec(key="region", value="eu-west-1")]
    )
    assert result.action == "unchanged"
    assert result.unchanged == ["region"]
    assert _write_calls(client) == 0


def test_variables_update_on_difference(client: Any) -> None:
    client.variables.list.return_value = iter([make_variable(value="us-east-1")])
    result = ensure_variables(
        client, "ws-1", [VariableSpec(key="region", value="eu-west-1")]
    )
    assert result.updated == ["region"]
    client.variables.update.assert_called_once()


def test_variables_dry_run_makes_no_writes(client: Any) -> None:
    client.variables.list.return_value = iter([make_variable(value="us-east-1")])
    result = ensure_variables(
        client,
        "ws-1",
        [VariableSpec(key="region", value="eu-west-1")],
        dry_run=True,
    )
    assert result.action == "would_update"
    assert _write_calls(client) == 0


def test_sensitive_values_never_appear_in_changes(client: Any) -> None:
    client.variables.list.return_value = iter([])
    result = ensure_variables(
        client,
        "ws-1",
        [
            VariableSpec(
                key="AWS_SECRET_ACCESS_KEY",
                value="hunter2",
                category="env",
                sensitive=True,
            )
        ],
    )
    rendered = repr(result.changes) + repr(result.summary())
    assert "hunter2" not in rendered
    assert "<sensitive>" in repr(result.changes)


def test_sensitive_skip_if_present(client: Any) -> None:
    client.variables.list.return_value = iter(
        [make_variable(key="TOKEN", sensitive=True, category="env")]
    )
    result = ensure_variables(
        client,
        "ws-1",
        [VariableSpec(key="TOKEN", value="new", category="env", sensitive=True)],
        sensitive_policy="skip_if_present",
    )
    assert result.unchanged == ["TOKEN"]
    assert _write_calls(client) == 0


def test_prune_requires_confirmation(client: Any) -> None:
    client.variables.list.return_value = iter([make_variable(key="stale", id="var-9")])
    result = ensure_variables(client, "ws-1", [], prune=True)
    assert result.action == "awaiting_confirmation"
    assert result.would_delete == ["stale"]
    client.variables.delete.assert_not_called()


def test_prune_deletes_when_confirmed(client: Any) -> None:
    client.variables.list.return_value = iter([make_variable(key="stale", id="var-9")])
    result = ensure_variables(client, "ws-1", [], prune=True, confirmed=True)
    assert result.deleted == ["stale"]
    client.variables.delete.assert_called_once_with("ws-1", "var-9")
