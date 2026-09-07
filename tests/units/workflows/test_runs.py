# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Run workflows: waiting, summarising, and the destructive gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pytfe.errors import RunNotConfirmable, WorkflowTimeout
from pytfe.models.configuration_version import ConfigurationVersion
from pytfe.models.run import Run
from pytfe.models.workspace import Workspace
from pytfe.workflows import apply_with_gate, plan_summary, wait_for_run

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "plan_json"


def plan_json(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def make_run(status: str, *, confirmable: bool | None = None) -> Run:
    payload: dict[str, Any] = {"id": "run-1", "status": status}
    if confirmable is not None:
        payload["actions"] = {
            "is-cancelable": True,
            "is-confirmable": confirmable,
            "is-discardable": True,
            "is-force-cancelable": False,
        }
    return Run.model_validate(payload)


# --------------------------------------------------------------------------
# wait_for_run
# --------------------------------------------------------------------------


def test_wait_for_run_stops_at_plan_done(client: Any, clock: Any) -> None:
    client.runs.read.side_effect = [
        make_run("planning"),
        make_run("planning"),
        make_run("planned"),
    ]
    run = wait_for_run(
        client,
        "run-1",
        until="plan_done",
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    assert run.status is not None and run.status.value == "planned"
    assert client.runs.read.call_count == 3


def test_wait_for_run_keeps_going_past_plan_when_terminal(
    client: Any, clock: Any
) -> None:
    client.runs.read.side_effect = [
        make_run("planned"),
        make_run("applying"),
        make_run("applied"),
    ]
    run = wait_for_run(
        client, "run-1", until="terminal", _sleep=clock.sleep, _clock=clock.time
    )
    assert run.status is not None and run.status.value == "applied"


def test_wait_for_run_times_out_with_last_status(client: Any, clock: Any) -> None:
    client.runs.read.return_value = make_run("planning")
    with pytest.raises(WorkflowTimeout) as excinfo:
        wait_for_run(client, "run-1", timeout=10, _sleep=clock.sleep, _clock=clock.time)
    last = excinfo.value.last
    assert isinstance(last, Run)
    assert last.status is not None and last.status.value == "planning"


def test_wait_for_run_does_not_hang_on_an_awaiting_decision_run(
    client: Any, clock: Any
) -> None:
    """A run paused for a policy override never becomes terminal on its own."""
    client.runs.read.return_value = make_run("policy_soft_failed")
    run = wait_for_run(
        client, "run-1", until="plan_done", _sleep=clock.sleep, _clock=clock.time
    )
    assert run.status is not None and run.status.value == "policy_soft_failed"


# --------------------------------------------------------------------------
# plan_summary
# --------------------------------------------------------------------------


def test_plan_summary_counts_from_plan_json(client: Any) -> None:
    client.plans.read_json_output_for_run.return_value = plan_json("simple")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.return_value = make_run("planned")

    summary = plan_summary(client, "run-1")
    assert (summary.add, summary.change, summary.destroy) == (2, 1, 0)
    assert summary.source == "plan_json"
    assert not summary.is_destructive
    assert summary.has_changes
    assert summary.output_changes == ["bucket_arn"]
    assert str(summary) == "+2 ~1 -0 (no destroys)"


def test_plan_summary_detects_replace_in_either_order(client: Any) -> None:
    """A replace is delete+create, and the API emits both orderings."""
    client.plans.read_json_output_for_run.return_value = plan_json("replace")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.return_value = make_run("planned")

    summary = plan_summary(client, "run-1")
    assert summary.replace == 2
    assert summary.add == 1
    assert summary.is_destructive
    assert summary.drift == 1
    assert sorted(summary.replace_addresses) == [
        "aws_instance.api",
        "aws_instance.web",
    ]


def test_plan_summary_reports_destroys(client: Any) -> None:
    client.plans.read_json_output_for_run.return_value = plan_json("destroy")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.return_value = make_run("planned")

    summary = plan_summary(client, "run-1")
    assert summary.destroy == 2
    assert summary.is_destructive
    assert "DESTRUCTIVE" in str(summary)


def test_plan_summary_ignores_noops(client: Any) -> None:
    client.plans.read_json_output_for_run.return_value = plan_json("no_changes")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.return_value = make_run("planned")

    summary = plan_summary(client, "run-1")
    assert not summary.has_changes


def test_plan_summary_falls_back_to_plan_attributes(client: Any) -> None:
    """Plan JSON is unavailable for speculative and archived plans."""
    from pytfe.models.plan import Plan

    client.plans.read_json_output_for_run.return_value = None
    client.plans.read_for_run.return_value = Plan.model_validate(
        {
            "id": "plan-1",
            "resource-additions": 4,
            "resource-changes": 2,
            "resource-destructions": 1,
        }
    )
    client.policy_checks.list.return_value = iter([])
    client.runs.read.return_value = make_run("planned")

    summary = plan_summary(client, "run-1")
    assert summary.source == "plan_attributes"
    assert (summary.add, summary.change, summary.destroy) == (4, 2, 1)
    assert summary.is_destructive


def test_plan_summary_requires_an_identifier(client: Any) -> None:
    with pytest.raises(ValueError, match="run_id or plan_id"):
        plan_summary(client)


# --------------------------------------------------------------------------
# apply_with_gate - the safety-critical path
# --------------------------------------------------------------------------


def _planned(client: Any, fixture: str = "simple") -> None:
    client.runs.read.return_value = make_run("planned", confirmable=True)
    client.plans.read_json_output_for_run.return_value = plan_json(fixture)
    client.policy_checks.list.return_value = iter([])


def test_apply_stops_without_confirmation_and_makes_no_apply_call(
    client: Any,
) -> None:
    _planned(client)
    result = apply_with_gate(client, "run-1")
    assert result.phase == "awaiting_confirmation"
    assert result.applied is False
    client.runs.apply.assert_not_called()


def test_apply_refuses_a_destructive_plan_even_when_confirmed(client: Any) -> None:
    """confirmed=True is not enough; allow_destroy must be explicit."""
    _planned(client, "destroy")
    result = apply_with_gate(client, "run-1", confirmed=True)
    assert result.phase == "refused_destructive"
    assert result.ok is False
    client.runs.apply.assert_not_called()


def test_apply_refuses_a_replace_plan(client: Any) -> None:
    _planned(client, "replace")
    result = apply_with_gate(client, "run-1", confirmed=True)
    assert result.phase == "refused_destructive"
    client.runs.apply.assert_not_called()


def test_apply_proceeds_when_confirmed(client: Any, clock: Any) -> None:
    _planned(client)
    client.runs.read.side_effect = [
        make_run("planned", confirmable=True),  # the confirmable check
        make_run("planned", confirmable=True),  # cost-estimate lookup
        make_run("applied"),  # first poll after apply
    ]
    result = apply_with_gate(
        client, "run-1", confirmed=True, _sleep=clock.sleep, _clock=clock.time
    )
    client.runs.apply.assert_called_once()
    assert result.phase == "applied"
    assert result.applied is True


def test_apply_honours_a_rejecting_confirm_callback(client: Any) -> None:
    _planned(client)
    result = apply_with_gate(client, "run-1", confirm=lambda plan: False)
    assert result.phase == "rejected"
    client.runs.apply.assert_not_called()


def test_confirm_callback_receives_the_plan_summary(client: Any, clock: Any) -> None:
    client.plans.read_json_output_for_run.return_value = plan_json("destroy")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.side_effect = [
        make_run("planned", confirmable=True),
        make_run("planned", confirmable=True),
        make_run("applied"),
    ]
    seen: list[Any] = []

    def confirm(plan: Any) -> bool:
        seen.append(plan)
        return True

    apply_with_gate(
        client,
        "run-1",
        confirm=confirm,
        allow_destroy=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    assert seen and seen[0].destroy == 2


def test_apply_rejects_an_unconfirmable_run(client: Any) -> None:
    client.runs.read.return_value = make_run("planning", confirmable=False)
    with pytest.raises(RunNotConfirmable):
        apply_with_gate(client, "run-1", confirmed=True)
    client.runs.apply.assert_not_called()


def test_destructive_plan_applies_with_explicit_allow_destroy(
    client: Any, clock: Any
) -> None:
    client.plans.read_json_output_for_run.return_value = plan_json("destroy")
    client.policy_checks.list.return_value = iter([])
    client.runs.read.side_effect = [
        make_run("planned", confirmable=True),
        make_run("planned", confirmable=True),
        make_run("applied"),
    ]
    result = apply_with_gate(
        client,
        "run-1",
        confirmed=True,
        allow_destroy=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    client.runs.apply.assert_called_once()
    assert result.phase == "applied"


def test_summary_is_json_serializable_and_small(client: Any) -> None:
    _planned(client)
    result = apply_with_gate(client, "run-1")
    summary = result.summary()
    json.dumps(summary)  # must not raise
    assert len(summary) <= 20
    assert summary["phase"] == "awaiting_confirmation"


# --------------------------------------------------------------------------
# Organization resolution for run URLs
#
# Found by a live run against HCP Terraform, which produced
# https://app.terraform.io/app//workspaces/... - an empty org segment - whenever
# the caller addressed the workspace by id rather than by organization+name.
# --------------------------------------------------------------------------


def workspace_with_org_relationship() -> Any:
    """A workspace as the resource parser actually produces it.

    `relationships` is a PrivateAttr attached by attach_jsonapi during parsing,
    not a model field, so passing it to model_validate silently does nothing -
    which is what made the first version of this test pass a bad fixture.
    """
    from pytfe._jsonapi import attach_jsonapi
    from pytfe.models.workspace import Workspace

    return attach_jsonapi(
        Workspace.model_validate({"id": "ws-1", "name": "web"}),
        {
            "id": "ws-1",
            "type": "workspaces",
            "relationships": {
                # Organizations are identified by name, so data.id IS the name.
                "organization": {"data": {"id": "acme", "type": "organizations"}}
            },
        },
    )


def test_organization_read_from_the_relationship(client: Any) -> None:
    from pytfe.workflows._resolve import organization_of

    assert organization_of(client, workspace_with_org_relationship()) == "acme"


def test_related_returns_raw_dicts_not_a_model(client: Any) -> None:
    """Why the first implementation failed: the workspace parser has no entry
    for organizations, so related() yields a list of dicts and reading .name
    off it silently produced None."""
    ws = workspace_with_org_relationship()
    related = ws.related("organization")
    assert isinstance(related, list)
    assert getattr(related[0], "name", None) is None


def test_run_url_has_no_empty_segment(client: Any) -> None:
    from pytfe.workflows._resolve import organization_of, run_web_url

    org = organization_of(client, workspace_with_org_relationship())
    url = run_web_url(client, org, "web", "run-1")
    assert url == "https://tfe.example.com/app/acme/workspaces/web/runs/run-1"
    assert "//workspaces" not in url


def test_caller_supplied_organization_wins(client: Any) -> None:
    from pytfe.workflows._resolve import organization_of

    ws = workspace_with_org_relationship()
    assert organization_of(client, ws, "explicit") == "explicit"


def test_missing_relationship_degrades_to_empty(client: Any) -> None:
    from pytfe.models.workspace import Workspace
    from pytfe.workflows._resolve import organization_of

    assert (
        organization_of(client, Workspace.model_validate({"id": "ws-1", "name": "w"}))
        == ""
    )


# --------------------------------------------------------------------------
# planned_and_finished is ambiguous
#
# Found live: a speculative plan creating two resources reported
# phase="no_changes", because HCP ends every speculative run in
# planned_and_finished regardless of what it proposed.
# --------------------------------------------------------------------------


def test_speculative_plan_with_changes_reports_planned(client: Any, clock: Any) -> None:
    from pytfe.workflows import speculative_plan

    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.configuration_versions.create.return_value = (
        ConfigurationVersion.model_validate(
            {"id": "cv-1", "upload-url": "https://archivist/x"}
        )
    )
    client.configuration_versions.read.return_value = (
        ConfigurationVersion.model_validate({"id": "cv-1", "status": "uploaded"})
    )
    client.runs.create.return_value = make_run("pending")
    client.runs.read.return_value = make_run("planned_and_finished")
    client.plans.read_json_output_for_run.return_value = plan_json("simple")
    client.policy_checks.list.return_value = iter([])

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path

        Path(tmp, "main.tf").write_text("resource {}")
        result = speculative_plan(client, tmp, workspace_id="ws-1")

    assert result.plan is not None and result.plan.has_changes
    assert result.phase == "planned", (
        "a speculative plan with changes is not 'no_changes'"
    )


def test_planned_and_finished_with_no_changes_still_reports_no_changes(
    client: Any,
) -> None:
    from pytfe.workflows import queue_run

    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.runs.create.return_value = make_run("pending")
    client.runs.read.return_value = make_run("planned_and_finished")
    client.plans.read_json_output_for_run.return_value = plan_json("no_changes")
    client.policy_checks.list.return_value = iter([])

    result = queue_run(client, workspace_id="ws-1", plan_only=True)
    assert result.phase == "no_changes"
