# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Stack workflows: the per-deployment matrix, the approval gate, diagnosis."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pytfe.errors import TFEError, WorkflowError
from pytfe.models.stack import Stack
from pytfe.models.stack_configuration import (
    StackConfiguration,
    StackConfigurationSource,
)
from pytfe.models.stack_deployment_group import StackDeploymentGroup
from pytfe.models.stack_deployment_run import DeploymentRunStatus, StackDeploymentRun
from pytfe.models.stack_deployment_step import (
    StackDeploymentStep,
    StackDiagnostic,
)
from pytfe.workflows import (
    StackPhase,
    approve_stack_plans,
    configuration_is_prepared,
    diagnose_stack_configuration,
    run_is_awaiting_approval,
    run_phase,
    speculative_stack_plan,
    stack_fetch_and_run,
    stack_run_from_directory,
    stack_status,
    step_phase,
    teardown_stack,
    wait_for_stack_configuration,
)

# --------------------------------------------------------------------------
# classification
# --------------------------------------------------------------------------


def test_every_status_partitions_exactly_once() -> None:
    """The guarantee that a new upstream status fails CI, not a waiter."""
    import pytfe.workflows.stack_phases as ss
    from pytfe.models.stack_configuration import StackConfigurationStatus
    from pytfe.models.stack_deployment_group import DeploymentGroupStatus
    from pytfe.models.stack_deployment_step import DeploymentStepStatus

    cases = [
        (StackConfigurationStatus, [ss.CONFIG_TERMINAL, ss.CONFIG_IN_PROGRESS]),
        (DeploymentGroupStatus, [ss.GROUP_TERMINAL, ss.GROUP_IN_PROGRESS]),
        (
            DeploymentRunStatus,
            [ss.RUN_TERMINAL, ss.RUN_AWAITING_APPROVAL, ss.RUN_IN_PROGRESS],
        ),
        (
            DeploymentStepStatus,
            [ss.STEP_TERMINAL, ss.STEP_AWAITING_APPROVAL, ss.STEP_IN_PROGRESS],
        ),
    ]
    for enum, buckets in cases:
        for member in enum:
            hits = [b for b in buckets if member in b]
            assert len(hits) == 1, (
                f"{enum.__name__}.{member.value} in {len(hits)} buckets"
            )
        assert sum(len(b) for b in buckets) == len(list(enum))


def test_operator_gates_are_recognised() -> None:
    """The states that never resolve without a human."""
    assert run_is_awaiting_approval("pre-deploying-pending-operator")
    assert run_is_awaiting_approval("deploying-pending-operator")
    assert step_phase("pending-operator") is StackPhase.AWAITING_APPROVAL
    assert run_phase("deploying") is StackPhase.IN_PROGRESS


def test_blocked_step_is_in_progress_not_terminal() -> None:
    """A blocked step waits on a predecessor; treating it as finished would
    report a half-run deployment as done."""
    assert step_phase("blocked") is StackPhase.IN_PROGRESS


def test_unknown_status_keeps_polling() -> None:
    assert run_phase("some-future-status") is StackPhase.IN_PROGRESS
    assert not configuration_is_prepared("converging")  # documented, not real


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------


def make_stack(**kw: Any) -> Stack:
    payload: dict[str, Any] = {
        "id": "st-1",
        "name": "platform",
        "vcs-repo": {"identifier": "acme/stacks", "branch": "main"},
    }
    payload.update(kw)
    return Stack.model_validate(payload)


def make_config(status: str = "completed", seq: int = 3) -> StackConfiguration:
    return StackConfiguration.model_validate(
        {"id": "sc-1", "status": status, "sequence-number": seq}
    )


def make_group(gid: str = "sdg-1") -> StackDeploymentGroup:
    return StackDeploymentGroup.model_validate(
        {"id": gid, "name": "group-a", "status": "deploying"}
    )


def make_run(
    deployment: str, status: str, rid: str | None = None
) -> StackDeploymentRun:
    return StackDeploymentRun.model_validate(
        {"id": rid or f"sdr-{deployment}", "deployment": deployment, "status": status}
    )


def make_step(sid: str, operation: str, status: str) -> StackDeploymentStep:
    return StackDeploymentStep.model_validate(
        {"id": sid, "operation-type": operation, "status": status}
    )


def stage(
    client: Any,
    runs: list[StackDeploymentRun],
    *,
    config_status: str = "completed",
    steps: dict[str, list[StackDeploymentStep]] | None = None,
) -> None:
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.read.return_value = make_config(config_status)
    client.stack_configurations.list.return_value = iter([make_config(config_status)])
    client.stack_configurations.create.return_value = make_config("pending")
    client.stack_deployment_groups.list.side_effect = lambda *a, **k: iter(
        [make_group()]
    )
    client.stack_deployment_runs.list.side_effect = lambda *a, **k: iter(list(runs))
    steps = steps or {}
    client.stack_deployment_steps.list.side_effect = lambda rid, *a, **k: iter(
        steps.get(rid, [])
    )
    client.stack_deployment_steps.list_diagnostics.side_effect = lambda *a, **k: iter(
        []
    )


# --------------------------------------------------------------------------
# stack_status - the matrix
# --------------------------------------------------------------------------


def test_status_builds_a_per_deployment_matrix(client: Any) -> None:
    """A stack has no single status; the result is a matrix keyed by deployment."""
    stage(
        client,
        [
            make_run("dev", "succeeded"),
            make_run("staging", "deploying"),
            make_run("production", "deploying-pending-operator"),
        ],
    )
    result = stack_status(client, "st-1")
    assert set(result.deployments) == {"dev", "staging", "production"}
    assert result.deployments["production"].awaiting_approval is True
    assert result.deployments["dev"].awaiting_approval is False


def test_status_health_is_awaiting_when_any_deployment_is_gated(client: Any) -> None:
    stage(
        client,
        [make_run("dev", "succeeded"), make_run("prod", "deploying-pending-operator")],
    )
    assert stack_status(client, "st-1").health == "awaiting_approval"


def test_status_health_healthy_when_all_succeeded(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded"), make_run("prod", "succeeded")])
    assert stack_status(client, "st-1").health == "healthy"


def test_status_health_errored_when_a_deployment_failed(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded"), make_run("prod", "failed")])
    assert stack_status(client, "st-1").health == "errored"


def test_status_picks_the_latest_configuration_by_sequence(client: Any) -> None:
    """The list endpoint has no sort parameter, and the docs' newest-first claim
    is not backed by the API contract, so the workflow sorts locally."""
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.list.return_value = iter(
        [make_config(seq=1), make_config(seq=7), make_config(seq=3)]
    )
    client.stack_deployment_groups.list.side_effect = lambda *a, **k: iter([])
    result = stack_status(client, "st-1")
    assert result.sequence_number == 7


def test_status_never_deployed(client: Any) -> None:
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.list.return_value = iter([])
    assert stack_status(client, "st-1").health == "never_deployed"


def test_status_summary_is_serializable(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded")])
    summary = stack_status(client, "st-1").summary()
    json.dumps(summary)
    assert summary["deployments"] == {"dev": "succeeded"}


# --------------------------------------------------------------------------
# the approval gate
# --------------------------------------------------------------------------


def test_approval_is_gated(client: Any) -> None:
    stage(client, [make_run("prod", "deploying-pending-operator")])
    result = approve_stack_plans(client, configuration_id="sc-1")
    assert result.phase == "awaiting_confirmation"
    client.stack_deployment_groups.approve_all_plans.assert_not_called()


def test_approval_enumerates_before_asking(client: Any) -> None:
    stage(
        client,
        [
            make_run("dev", "deploying-pending-operator"),
            make_run("prod", "deploying-pending-operator"),
            make_run("staging", "succeeded"),
        ],
    )
    result = approve_stack_plans(client, configuration_id="sc-1")
    # Only the gated deployments are offered, and enumeration is timestamped
    # because approve_all_plans cannot promise it approves only these.
    assert {a.deployment for a in result.approvals} == {"dev", "prod"}
    assert result.enumerated_at is not None


def test_approval_confirms_by_re_reading(client: Any) -> None:
    """approve_all_plans returns None, so success is verified, not assumed."""
    stage(client, [make_run("prod", "deploying-pending-operator")])
    client.stack_deployment_runs.read.return_value = make_run("prod", "deploying")
    result = approve_stack_plans(client, configuration_id="sc-1", confirmed=True)
    client.stack_deployment_groups.approve_all_plans.assert_called_once_with("sdg-1")
    assert result.phase == "approved"
    assert result.approved == ["prod"]


def test_partial_approval_is_reported(client: Any) -> None:
    """An approver without permission on every plan clears only some."""
    stage(
        client,
        [
            make_run("dev", "deploying-pending-operator", "sdr-dev"),
            make_run("prod", "deploying-pending-operator", "sdr-prod"),
        ],
    )
    client.stack_deployment_runs.read.side_effect = lambda rid: (
        make_run("dev", "deploying", rid)
        if rid == "sdr-dev"
        else make_run("prod", "deploying-pending-operator", rid)
    )
    result = approve_stack_plans(client, configuration_id="sc-1", confirmed=True)
    assert result.phase == "partial"
    assert result.approved == ["dev"] and result.not_approved == ["prod"]
    assert any("lacks permission" in w for w in result.warnings)


def test_nothing_to_approve(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded")])
    result = approve_stack_plans(client, configuration_id="sc-1", confirmed=True)
    assert result.phase == "nothing_to_approve"
    client.stack_deployment_groups.approve_all_plans.assert_not_called()


def test_confirm_callback_receives_the_matrix(client: Any) -> None:
    stage(client, [make_run("prod", "deploying-pending-operator")])
    seen: list[Any] = []
    approve_stack_plans(
        client, configuration_id="sc-1", confirm=lambda m: seen.append(m) or False
    )
    assert seen and "prod" in seen[0]
    client.stack_deployment_groups.approve_all_plans.assert_not_called()


def test_approval_requires_an_identifier(client: Any) -> None:
    with pytest.raises(ValueError, match="configuration_id or deployment_group_id"):
        approve_stack_plans(client)


# --------------------------------------------------------------------------
# the loop
# --------------------------------------------------------------------------


def test_fetch_and_run_stops_at_the_gate(client: Any, clock: Any) -> None:
    stage(
        client,
        [make_run("dev", "succeeded"), make_run("prod", "deploying-pending-operator")],
    )
    result = stack_fetch_and_run(client, "st-1", _sleep=clock.sleep, _clock=clock.time)
    assert result.phase == "awaiting_approval"
    assert [d.deployment for d in result.awaiting] == ["prod"]
    client.stack_deployment_groups.approve_all_plans.assert_not_called()


def test_fetch_and_run_refuses_destroy_without_permission(client: Any) -> None:
    stage(client, [])
    result = stack_fetch_and_run(client, "st-1", destroy_all=True)
    assert result.phase == "refused_destructive"
    client.stack_configurations.create.assert_not_called()


def test_fetch_and_run_requires_vcs(client: Any) -> None:
    """There is no manual upload path, so a non-VCS stack cannot be run."""
    client.stacks.read.return_value = Stack.model_validate({"id": "st-1", "name": "s"})
    with pytest.raises(WorkflowError, match="no VCS repository"):
        stack_fetch_and_run(client, "st-1")


def test_prepare_failure_is_reported_not_raised(client: Any, clock: Any) -> None:
    stage(client, [], config_status="failed")
    result = stack_fetch_and_run(client, "st-1", _sleep=clock.sleep, _clock=clock.time)
    assert result.phase == "prepare_failed"
    assert result.ok is False
    assert any("diagnose_stack_configuration" in w for w in result.warnings)


def test_selected_deployments_reaches_the_wire(client: Any, clock: Any) -> None:
    stage(client, [make_run("dev", "succeeded")])
    stack_fetch_and_run(
        client, "st-1", deployments=["dev"], _sleep=clock.sleep, _clock=clock.time
    )
    options = client.stack_configurations.create.call_args.args[1]
    assert options.selected_deployments == ["dev"]


def test_speculative_never_approves(client: Any, clock: Any) -> None:
    stage(client, [make_run("prod", "deploying-pending-operator")])
    result = speculative_stack_plan(
        client, "st-1", _sleep=clock.sleep, _clock=clock.time
    )
    assert result.speculative is True
    assert result.phase == "planned"  # not awaiting_approval - it cannot be applied
    client.stack_deployment_groups.approve_all_plans.assert_not_called()
    options = client.stack_configurations.create.call_args.args[1]
    assert options.speculative_enabled is True


# --------------------------------------------------------------------------
# diagnosis
# --------------------------------------------------------------------------


def test_diagnose_prepare_failure(client: Any) -> None:
    stage(client, [], config_status="failed")
    from pytfe.models.stack_deployment_step import StackDiagnostic

    client.stack_diagnostics.read.return_value = StackDiagnostic.model_validate(
        {"id": "sd-1", "severity": "error", "summary": "Unsupported argument"}
    )
    result = diagnose_stack_configuration(client, "sc-1")
    assert result.stage == "prepare"
    assert result.ok is False


def test_diagnose_finds_the_failed_deployment_step(client: Any) -> None:
    steps = {
        "sdr-prod": [
            make_step("sds-1", "plan", "completed"),
            make_step("sds-2", "apply", "failed"),
        ],
        "sdr-dev": [make_step("sds-3", "apply", "completed")],
    }
    stage(
        client,
        [
            make_run("prod", "failed", "sdr-prod"),
            make_run("dev", "succeeded", "sdr-dev"),
        ],
        steps=steps,
    )
    result = diagnose_stack_configuration(client, "sc-1")
    assert result.stage == "apply"
    assert result.failed_deployments == ["prod"]
    # Debug-log bytes are credential-bearing, so only the step id is surfaced.
    assert result.debug_log_step_ids == {"prod": "sds-2"}


def test_diagnose_separates_blocked_from_failed(client: Any) -> None:
    """A blocked step is a symptom of a failed predecessor, not the cause."""
    steps = {
        "sdr-a": [make_step("sds-1", "apply", "failed")],
        "sdr-b": [make_step("sds-2", "apply", "blocked")],
    }
    stage(
        client,
        [make_run("a", "failed", "sdr-a"), make_run("b", "pending", "sdr-b")],
        steps=steps,
    )
    result = diagnose_stack_configuration(client, "sc-1")
    assert result.failed_deployments == ["a"]
    assert result.blocked_deployments == ["b"]


def test_diagnose_healthy_configuration(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded", "sdr-dev")], steps={"sdr-dev": []})
    result = diagnose_stack_configuration(client, "sc-1")
    assert result.stage == "none"


# --------------------------------------------------------------------------
# teardown
# --------------------------------------------------------------------------


def test_teardown_is_gated(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded")])
    result = teardown_stack(client, "st-1")
    assert result.phase == "awaiting_approval"
    client.stacks.delete.assert_not_called()
    client.stacks.force_delete.assert_not_called()


def test_teardown_destroys_through_the_api_not_hcl(client: Any, clock: Any) -> None:
    """destroy_all is a configuration create option, so no HCL editing."""
    stage(client, [make_run("dev", "succeeded")])
    teardown_stack(client, "st-1", confirmed=True)
    options = client.stack_configurations.create.call_args.args[1]
    assert options.destroy_all is True
    client.stacks.delete.assert_called_once_with("st-1")


def test_teardown_force_uses_force_delete(client: Any) -> None:
    stage(client, [make_run("dev", "failed")])
    teardown_stack(client, "st-1", confirmed=True, destroy_first=False, force=True)
    client.stacks.force_delete.assert_called_once_with("st-1")
    client.stacks.delete.assert_not_called()


def test_teardown_refuses_when_destroy_did_not_complete(client: Any) -> None:
    stage(client, [make_run("dev", "failed")])
    result = teardown_stack(client, "st-1", confirmed=True)
    assert result.ok is False
    assert any("force=True" in w for w in result.warnings)
    client.stacks.delete.assert_not_called()


# --------------------------------------------------------------------------
# the poller
# --------------------------------------------------------------------------


def test_wait_stops_when_prepared(client: Any, clock: Any) -> None:
    client.stack_configurations.read.side_effect = [
        make_config("preparing"),
        make_config("completed"),
    ]
    cfg = wait_for_stack_configuration(
        client, "sc-1", until="prepared", _sleep=clock.sleep, _clock=clock.time
    )
    assert configuration_is_prepared(cfg.status)


def test_wait_stops_when_prepare_fails(client: Any, clock: Any) -> None:
    """A failed prepare is 'done' - the caller diagnoses it rather than hanging."""
    client.stack_configurations.read.return_value = make_config("failed")
    cfg = wait_for_stack_configuration(
        client, "sc-1", until="prepared", _sleep=clock.sleep, _clock=clock.time
    )
    assert not configuration_is_prepared(cfg.status)


def test_wait_plans_ready_stops_at_the_operator_gate(client: Any, clock: Any) -> None:
    """The gate never resolves on its own; treating it as in-progress would spin
    to timeout on work waiting for a human."""
    stage(client, [make_run("prod", "deploying-pending-operator")])
    wait_for_stack_configuration(
        client, "sc-1", until="plans_ready", _sleep=clock.sleep, _clock=clock.time
    )


def test_wait_completed_does_not_stop_at_the_gate(client: Any, clock: Any) -> None:
    from pytfe.errors import WorkflowTimeout

    stage(client, [make_run("prod", "deploying-pending-operator")])
    with pytest.raises(WorkflowTimeout):
        wait_for_stack_configuration(
            client,
            "sc-1",
            until="completed",
            timeout=30,
            _sleep=clock.sleep,
            _clock=clock.time,
        )


def test_steps_unavailable_does_not_break_the_matrix(client: Any) -> None:
    stage(client, [make_run("dev", "succeeded")])
    client.stack_deployment_steps.list.side_effect = TFEError("forbidden")
    result = stack_status(client, "st-1")
    assert "dev" in result.deployments


def test_prepare_failure_lists_the_configuration_diagnostics(client: Any) -> None:
    """Prepare diagnostics come from the configuration, not from any step.

    A configuration that fails to prepare has no deployment runs, so the
    step-level diagnostics the rest of this workflow reads do not exist yet.
    """
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.read.return_value = StackConfiguration.model_validate(
        {
            "id": "sc-1",
            "status": "failed",
            "preparing-event-stream-url": "https://archivist.terraform.io/v1/object/abc",
        }
    )
    client.stack_diagnostics.list_for_configuration.return_value = iter(
        [
            StackDiagnostic.model_validate(
                {
                    "id": "std-1",
                    "severity": "error",
                    "summary": "Diagnostics reported",
                    "detail": "HCP Terraform reported 2 errors.",
                    "diags": [
                        {
                            "severity": "error",
                            "summary": "Cannot read .terraform-version file",
                            "detail": "does not contain the version selection file.",
                            "range": {
                                "filename": ".terraform-version",
                                "start": {"line": 1, "column": 1},
                            },
                        },
                        {"severity": "error", "summary": "Error while loading source"},
                    ],
                }
            )
        ]
    )

    result = diagnose_stack_configuration(client, "sc-1")

    assert result.stage == "prepare"
    assert result.ok is False
    client.stack_diagnostics.list_for_configuration.assert_called_once_with("sc-1")
    assert result.prepare_log_url == "https://archivist.terraform.io/v1/object/abc"
    assert not any("not reachable" in w for w in result.warnings)

    # The rollup counts the errors; the nested entries name them.
    (diagnostic,) = result.diagnostics
    assert diagnostic.summary == "Diagnostics reported"
    assert [e.summary for e in diagnostic.errors] == [
        "Cannot read .terraform-version file",
        "Error while loading source",
    ]
    assert diagnostic.errors[0].filename == ".terraform-version"
    assert diagnostic.errors[0].line == 1
    # A diagnostic with no range still parses rather than being dropped.
    assert diagnostic.errors[1].filename is None

    # The commonest first-upload failure gets an actionable suggestion.
    assert result.suggestion is not None
    assert ".terraform-version" in result.suggestion
    assert json.dumps(result.summary())


def test_prepare_failure_without_diagnostics_hands_back_the_log(
    client: Any,
) -> None:
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.read.return_value = StackConfiguration.model_validate(
        {
            "id": "sc-1",
            "status": "failed",
            "preparing-event-stream-url": "https://archivist.terraform.io/v1/object/abc",
        }
    )
    client.stack_diagnostics.list_for_configuration.return_value = iter([])

    result = diagnose_stack_configuration(client, "sc-1")

    assert result.diagnostics == []
    assert any("prepare_log_url" in w for w in result.warnings)
    assert result.summary()["prepare_log_url"]


def test_prepare_diagnostics_failure_is_reported_not_raised(client: Any) -> None:
    client.stacks.read.return_value = make_stack()
    client.stack_configurations.read.return_value = StackConfiguration.model_validate(
        {"id": "sc-1", "status": "failed"}
    )
    client.stack_diagnostics.list_for_configuration.side_effect = TFEError("forbidden")

    result = diagnose_stack_configuration(client, "sc-1")

    assert result.stage == "prepare"
    assert any("could not list prepare diagnostics" in w for w in result.warnings)


# --------------------------------------------------------------------------
# stack_run_from_directory - the manual upload path
# --------------------------------------------------------------------------


def _stack_dir(tmp_path: Any) -> Any:
    directory = tmp_path / "stack"
    directory.mkdir()
    (directory / "components.tfcomponent.hcl").write_text('component "app" {}\n')
    (directory / "deployments.tfdeploy.hcl").write_text('deployment "dev" {}\n')
    return directory


def test_run_from_directory_uploads_then_stops_at_the_gate(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    stage(
        client,
        [make_run("dev", "succeeded"), make_run("prod", "deploying-pending-operator")],
    )
    result = stack_run_from_directory(
        client, "st-1", _stack_dir(tmp_path), _sleep=clock.sleep, _clock=clock.time
    )

    assert result.phase == "awaiting_approval"
    assert [d.deployment for d in result.awaiting] == ["prod"]
    client.stack_deployment_groups.approve_all_plans.assert_not_called()

    # MANUAL source, not FETCH: the source is the archive, not the repository.
    _, _, source = client.stack_configurations.create.call_args[0]
    assert source is StackConfigurationSource.MANUAL

    configuration_id, archive = client.stack_configurations.upload.call_args[0]
    assert configuration_id == "sc-1"
    assert archive.startswith(b"\x1f\x8b")  # gzip


def test_run_from_directory_needs_no_vcs(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    """The reason this workflow exists: a stack with no repository attached."""
    stage(client, [make_run("dev", "succeeded")])
    client.stacks.read.return_value = Stack.model_validate({"id": "st-1", "name": "s"})

    result = stack_run_from_directory(
        client, "st-1", _stack_dir(tmp_path), _sleep=clock.sleep, _clock=clock.time
    )

    assert result.phase == "completed"


def test_run_from_directory_refuses_destroy_without_permission(
    client: Any, tmp_path: Any
) -> None:
    result = stack_run_from_directory(
        client, "st-1", _stack_dir(tmp_path), destroy_all=True
    )
    assert result.phase == "refused_destructive"
    client.stack_configurations.create.assert_not_called()
    client.stack_configurations.upload.assert_not_called()


def test_run_from_directory_packages_before_creating_anything(
    client: Any, tmp_path: Any
) -> None:
    """A bad path must not leave a configuration stranded with no source."""
    with pytest.raises(ValueError, match="existing directory"):
        stack_run_from_directory(client, "st-1", tmp_path / "absent")
    client.stack_configurations.create.assert_not_called()


def test_run_from_directory_approves_when_confirmed(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    stage(client, [make_run("prod", "deploying-pending-operator")])
    # The gate clears only once approve_all_plans is called, so the wait for
    # "completed" is driven by the approval rather than settling on its own.
    current = [make_run("prod", "deploying-pending-operator")]
    client.stack_deployment_runs.list.side_effect = lambda *a, **k: iter(list(current))
    client.stack_deployment_runs.read.side_effect = lambda rid: current[0]

    def clear_gate(_group_id: str) -> None:
        current[0] = make_run("prod", "succeeded")

    client.stack_deployment_groups.approve_all_plans.side_effect = clear_gate

    result = stack_run_from_directory(
        client,
        "st-1",
        _stack_dir(tmp_path),
        confirmed=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )

    client.stack_deployment_groups.approve_all_plans.assert_called_once_with("sdg-1")
    assert result.deployments["prod"].approved is True


def test_run_from_directory_speculative_never_approves(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    stage(client, [make_run("prod", "deploying-pending-operator")])

    result = stack_run_from_directory(
        client,
        "st-1",
        _stack_dir(tmp_path),
        speculative=True,
        confirmed=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )

    assert result.phase == "planned"
    client.stack_deployment_groups.approve_all_plans.assert_not_called()
    options = client.stack_configurations.create.call_args[0][1]
    assert options.speculative_enabled is True


def test_speculative_completion_is_reported_as_planned(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    """A speculative configuration's runs finish without applying anything.

    Verified live: every deployment reaches `succeeded`, which would otherwise
    be read as a completed deployment.
    """
    stage(client, [make_run("dev", "succeeded"), make_run("staging", "succeeded")])

    result = stack_run_from_directory(
        client,
        "st-1",
        _stack_dir(tmp_path),
        speculative=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )

    assert result.phase == "planned"
    assert result.ok is True


def test_non_speculative_completion_stays_completed(
    client: Any, clock: Any, tmp_path: Any
) -> None:
    stage(client, [make_run("dev", "succeeded")])
    result = stack_run_from_directory(
        client, "st-1", _stack_dir(tmp_path), _sleep=clock.sleep, _clock=clock.time
    )
    assert result.phase == "completed"
