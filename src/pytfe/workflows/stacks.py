# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Deploy, inspect and tear down HCP Terraform Stacks.

Use these instead of driving ``client.stack_*`` by hand: one stack deployment
spans five API levels (configuration, deployment group, deployment run, step,
diagnostic) with no status filter below the stack, so hand-rolling the walk takes
roughly thirty requests and four separate status vocabularies.

Deploy a stack and stop for approval::

    from pytfe import TFEClient
    from pytfe.workflows import approve_stack_plans, stack_fetch_and_run

    with TFEClient() as tfe:
        result = stack_fetch_and_run(tfe, "st-abc")

        if result.phase == "awaiting_approval":
            for name, d in result.deployments.items():
                print(name, d.status, "GATED" if d.awaiting_approval else "")
            # ...after a human decides:
            approve_stack_plans(tfe, configuration_id=result.configuration_id,
                                confirmed=True)

Check what is waiting on you, across every deployment::

    status = stack_status(tfe, "st-abc")
    status.health                                    # 'awaiting_approval'
    [d.deployment for d in status.deployments.values() if d.awaiting_approval]

Results are a matrix, not a single status
-----------------------------------------
A stack has no one plan and no one status: a configuration fans out to N
deployments, each with its own run, plan and approval. So ``result.deployments``
is a dict keyed by deployment name (``"dev"``, ``"production"``), and both
:class:`~pytfe.workflows.models.StackRunResult` and
:class:`~pytfe.workflows.models.StackStatus` carry one. Branch on
``result.phase`` for the overall outcome, then read the matrix for detail.
``.awaiting`` and ``.failed`` are shortcuts over it.

What to expect when building on this
------------------------------------
* **Approval is per deployment, and the verb is approve, not apply.** Some
  deployments may be auto-approved by ``.tfdeploy.hcl`` orchestration rules and
  never appear at the gate.
* **Approving clears a whole deployment group.** A run that reaches the gate
  between the enumeration and the approval is approved too, so
  :func:`approve_stack_plans` reports ``enumerated_at`` and re-reads each run to
  say what actually cleared - including partial approval, when the approver
  lacks permission on every plan in the group.
* **The stack must be VCS-backed.** These workflows fetch the configuration from
  the connected repository; the SDK exposes no way to upload one from a local
  directory, so there is no ``stack_run_from_directory``.
* **You decide whether a plan is safe to approve.** Unlike a workspace run,
  nothing on the Stacks API reports how destructive a plan is. Pass a
  ``confirm`` callback to inspect the matrix and decide, or fetch the plan
  yourself with ``download_artifact`` using the ``plan_description_step_id`` on
  each deployment.
* **Waiting takes a stopping point.** ``until="plans_ready"`` returns when every
  deployment is gated or finished - the moment a human is needed - while
  ``until="completed"`` waits for the whole deployment to finish.

Function names mirror the ``terraform stacks`` CLI where one exists, so the same
vocabulary works in a playbook, a script and a prompt.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Literal

from ..client import TFEClient
from ..errors import TFEError, WorkflowError
from ..models.stack_configuration import (
    StackConfigurationCreateOptions,
    StackConfigurationSource,
)
from ._poll import wait_until
from .models import (
    StackApproval,
    StackApprovalResult,
    StackDeploymentState,
    StackDiagnosticRow,
    StackFailure,
    StackRunPhase,
    StackRunResult,
    StackStatus,
)
from .stack_phases import (
    CONFIG_FAILED,
    RUN_FAILED,
    STEP_FAILED,
    configuration_is_prepared,
    run_is_awaiting_approval,
    run_is_terminal,
    step_phase,
)

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "StackConfirm",
    "wait_for_stack_configuration",
    "stack_status",
    "stack_fetch_and_run",
    "speculative_stack_plan",
    "approve_stack_plans",
    "diagnose_stack_configuration",
    "teardown_stack",
]

#: Called with the per-deployment matrix; return True to approve.
StackConfirm = Callable[[dict[str, StackDeploymentState]], bool]

_SUGGESTIONS: tuple[tuple[str, str], ...] = (
    (
        "no such deployment",
        "A deployment named in selected_deployments is not declared in "
        ".tfdeploy.hcl. Run stack_status() to list the real deployment names.",
    ),
    (
        "component",
        "A component in .tfcomponent.hcl failed to resolve. Check its source and "
        "the inputs the deployment passes to it.",
    ),
    (
        "unsupported",
        "The configuration uses a feature this Stacks version does not support. "
        "Check the required_providers and language version in .tfcomponent.hcl.",
    ),
)


def _value(status: Any) -> str | None:
    """Wire value of a status enum, or the string it already is."""
    value = getattr(status, "value", status)
    return value if isinstance(value, str) else None


def _runs_for_configuration(
    client: TFEClient, configuration_id: str
) -> list[tuple[str, Any]]:
    """Every (group_id, run) under a configuration.

    There is no status filter at any level below the stack, so this is the only
    way to see the deployments - and it is why the matrix is built once and
    passed around rather than re-derived per workflow.
    """
    out: list[tuple[str, Any]] = []
    for group in client.stack_deployment_groups.list(configuration_id):
        group_id = group.id or ""
        for run in client.stack_deployment_runs.list(group_id):
            out.append((group_id, run))
    return out


def _matrix(
    client: TFEClient, configuration_id: str, *, with_steps: bool = True
) -> dict[str, StackDeploymentState]:
    """Build the per-deployment matrix for a configuration."""
    matrix: dict[str, StackDeploymentState] = {}
    for group_id, run in _runs_for_configuration(client, configuration_id):
        name = run.deployment or run.id or "?"
        status = _value(run.status)
        state = StackDeploymentState(
            deployment=name,
            run_id=run.id,
            group_id=group_id,
            status=status,
            phase=_value(getattr(run, "status", None)),
            awaiting_approval=run_is_awaiting_approval(run.status),
        )
        if with_steps and run.id:
            try:
                for step in client.stack_deployment_steps.list(run.id):
                    operation = (step.operation_type or "").lower()
                    if operation == "plan":
                        state.plan_steps += 1
                        state.plan_description_step_id = (
                            state.plan_description_step_id or step.id
                        )
                    elif operation == "apply":
                        state.apply_steps += 1
                    if step.status in STEP_FAILED and step.id:
                        state.failed_step_ids.append(step.id)
            except TFEError as exc:
                logger.debug("steps unavailable for run %s: %s", run.id, exc)
        matrix[name] = state
    return matrix


def wait_for_stack_configuration(
    client: TFEClient,
    configuration_id: str,
    *,
    until: Literal["prepared", "plans_ready", "completed"] = "prepared",
    timeout: float = 1800,
    interval: float = 3.0,
    on_status: Callable[[Any], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> Any:
    """Poll a stack configuration until it reaches the requested state.

    The poller everything else here is built on. Three stopping points, because
    a stack has three interesting moments rather than one:

    * ``"prepared"`` - the configuration finished preparing. Until then, listing
      its deployment groups returns an empty page, which is indistinguishable
      from "this stack has no deployments".
    * ``"plans_ready"`` - every deployment run has either reached its approval
      gate or finished. This is the moment a human is needed.
    * ``"completed"`` - every deployment run has finished.

    Args:
        client: The client to poll through.
        configuration_id: The configuration to watch.
        until: Which moment to stop at.
        timeout: Total seconds to wait.
        interval: Initial poll delay; grows to 15s.
        on_status: Called with the configuration on every poll.

    Returns:
        The last observed ``StackConfiguration``.

    Raises:
        WorkflowTimeout: If the state is not reached in time; the last observed
            configuration is attached as ``.last``.
        TFEError: If the configuration cannot be read.

    Example:
        >>> cfg = wait_for_stack_configuration(client, "sc-abc", until="plans_ready")
        >>> cfg.status
        <StackConfigurationStatus.COMPLETED: 'completed'>
    """
    kwargs: dict[str, Any] = {}
    if _sleep is not None:
        kwargs["sleep"] = _sleep
    if _clock is not None:
        kwargs["clock"] = _clock

    def done(configuration: Any) -> bool:
        status = configuration.status
        if until == "prepared":
            # A failed prepare is also "done" - the caller diagnoses it.
            return configuration_is_prepared(status) or status in CONFIG_FAILED
        if not configuration_is_prepared(status):
            return status in CONFIG_FAILED
        runs = [run for _, run in _runs_for_configuration(client, configuration_id)]
        if not runs:
            # Prepared with no deployment runs yet: keep waiting, they appear
            # shortly after the configuration completes.
            return False
        if until == "plans_ready":
            return all(
                run_is_terminal(r.status) or run_is_awaiting_approval(r.status)
                for r in runs
            )
        return all(run_is_terminal(r.status) for r in runs)

    return wait_until(
        lambda: client.stack_configurations.read(configuration_id),
        done,
        timeout=timeout,
        interval=interval,
        on_tick=on_status,
        description=f"stack configuration {configuration_id} to reach {until}",
        **kwargs,
    )


def stack_status(client: TFEClient, stack_id: str) -> StackStatus:
    """Report a stack's health across every one of its deployments.

    A stack has no status of its own - health lives in its latest configuration
    and that configuration's deployment runs - so this resolves the latest
    configuration and builds the per-deployment matrix.

    Args:
        client: The client to read through.
        stack_id: The stack to inspect.

    Returns:
        A :class:`~pytfe.workflows.models.StackStatus`.

    Raises:
        TFEError: If the stack cannot be read.

    Example:
        >>> status = stack_status(client, "st-abc")
        >>> status.health
        'awaiting_approval'
        >>> [d.deployment for d in status.deployments.values() if d.awaiting_approval]
        ['production']
    """
    stack = client.stacks.read(stack_id)
    result = StackStatus(
        stack_id=stack_id,
        name=stack.name,
        upstream_count=getattr(stack, "upstream_count", None),
        downstream_count=getattr(stack, "downstream_count", None),
    )

    # The list endpoint exposes no sort parameter, and the docs' claim that it
    # returns newest first is not backed by the API contract - so sort locally
    # on sequence_number and report which configuration was chosen.
    configurations = sorted(
        client.stack_configurations.list(stack_id),
        key=lambda c: c.sequence_number or 0,
        reverse=True,
    )
    if not configurations:
        result.health = "never_deployed"
        return result

    latest = configurations[0]
    result.configuration_id = latest.id
    result.configuration_status = _value(latest.status)
    result.sequence_number = latest.sequence_number

    if not configuration_is_prepared(latest.status):
        result.health = "errored" if latest.status in CONFIG_FAILED else "deploying"
        return result

    result.deployments = _matrix(client, latest.id or "")
    states = list(result.deployments.values())
    if not states:
        result.health = "never_deployed"
    elif any(d.awaiting_approval for d in states):
        result.health = "awaiting_approval"
    elif any(d.failed_step_ids for d in states):
        result.health = "errored"
    elif all(run_is_terminal(d.status) for d in states):
        failed = any(d.status in {s.value for s in RUN_FAILED} for d in states)
        result.health = "errored" if failed else "healthy"
    else:
        result.health = "deploying"
    return result


def _finish_phase(matrix: dict[str, StackDeploymentState]) -> StackRunPhase:
    """Derive an overall phase from the per-deployment matrix."""
    states = list(matrix.values())
    if not states:
        return "no_changes"
    if any(d.awaiting_approval for d in states):
        return "awaiting_approval"
    if any(d.failed_step_ids for d in states):
        return "errored"
    if any(d.status in {s.value for s in RUN_FAILED} for d in states):
        return "errored"
    if all(run_is_terminal(d.status) for d in states):
        return "completed"
    return "planned"


def stack_fetch_and_run(
    client: TFEClient,
    stack_id: str,
    *,
    deployments: list[str] | None = None,
    speculative: bool = False,
    destroy_all: bool = False,
    confirmed: bool = False,
    confirm: StackConfirm | None = None,
    allow_destroy: bool = False,
    timeout: float = 3600,
    on_status: Callable[[Any], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> StackRunResult:
    """Fetch a stack's configuration from VCS and drive it to a decision.

    The stack analogue of ``run_from_directory``, and the stable one: it uses the
    VCS ``FETCH`` source, because there is no manual upload path in this SDK.

    The loop: create a configuration from the latest VCS commit, wait for it to
    prepare (a failure here is a configuration error - diagnose it), wait until
    every deployment run has reached its approval gate or finished, then stop.
    Approval is a separate, explicit step unless ``confirmed``/``confirm`` says
    otherwise - and unlike a workspace run, approval is *per deployment*.

    Args:
        client: The client to act through.
        stack_id: The stack to run.
        deployments: Restrict the run to these deployment names. Maps to the
            configuration's ``selected_deployments``.
        speculative: Plan only; the configuration can never be applied.
        destroy_all: Plan the destruction of every deployment. Requires
            ``allow_destroy=True``.
        confirmed: The caller asserts a human approved the plans.
        confirm: Called with the deployment matrix; return True to approve.
        allow_destroy: Permit a destroying configuration.
        timeout: Seconds to wait for the whole loop.
        on_status: Called with the configuration on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.StackRunResult`. Branch on ``phase``
        and read ``deployments`` for the per-deployment matrix.

    Raises:
        WorkflowError: If the stack has no VCS repository attached.
        WorkflowTimeout: If the configuration does not settle in time.
        TFEError: If the API rejects a call.

    Example:
        >>> result = stack_fetch_and_run(client, "st-abc")
        >>> result.phase
        'awaiting_approval'
        >>> for name, d in result.deployments.items():
        ...     print(name, d.status)
    """
    started = time.monotonic()

    if destroy_all and not allow_destroy:
        return StackRunResult(
            stack_id=stack_id,
            phase="refused_destructive",
            ok=False,
            warnings=["destroy_all=True requires allow_destroy=True"],
            duration_s=time.monotonic() - started,
        )

    stack = client.stacks.read(stack_id)
    if not getattr(stack, "vcs_repo", None):
        raise WorkflowError(
            f"stack {stack_id} has no VCS repository attached",
            hint=(
                "Only VCS-backed stacks can be run through this workflow: the "
                "SDK exposes no manual configuration upload."
            ),
        )

    configuration = client.stack_configurations.create(
        stack_id,
        StackConfigurationCreateOptions(
            speculative_enabled=speculative,
            destroy_all=destroy_all,
            selected_deployments=deployments,
        ),
        StackConfigurationSource.FETCH,
    )
    configuration_id = configuration.id or ""
    logger.info(
        "created stack configuration %s for stack %s", configuration_id, stack_id
    )

    prepared = wait_for_stack_configuration(
        client,
        configuration_id,
        until="prepared",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    if not configuration_is_prepared(prepared.status):
        return StackRunResult(
            stack_id=stack_id,
            configuration_id=configuration_id,
            configuration_status=_value(prepared.status),
            phase="prepare_failed",
            ok=False,
            speculative=speculative,
            duration_s=time.monotonic() - started,
            warnings=[
                "configuration failed to prepare; call "
                "diagnose_stack_configuration() for the diagnostics"
            ],
        )

    settled = wait_for_stack_configuration(
        client,
        configuration_id,
        until="plans_ready",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    matrix = _matrix(client, configuration_id)

    result = StackRunResult(
        stack_id=stack_id,
        configuration_id=configuration_id,
        configuration_status=_value(settled.status),
        phase=_finish_phase(matrix),
        deployments=matrix,
        speculative=speculative,
        duration_s=time.monotonic() - started,
    )
    if result.phase == "errored":
        result.ok = False

    # A speculative configuration can never be approved, so stop here whatever
    # the caller passed.
    if speculative or result.phase != "awaiting_approval":
        if result.phase == "awaiting_approval":
            result.phase = "planned"
        return result

    if confirm is not None and not confirm(matrix):
        result.phase = "rejected"
        return result
    if confirm is None and not confirmed:
        return result

    approval = approve_stack_plans(
        client,
        configuration_id=configuration_id,
        deployments=deployments,
        confirmed=True,
        allow_destroy=allow_destroy,
    )
    for name in approval.approved:
        if name in result.deployments:
            result.deployments[name].approved = True
    result.warnings.extend(approval.warnings)

    final = wait_for_stack_configuration(
        client,
        configuration_id,
        until="completed",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    result.configuration_status = _value(final.status)
    result.deployments = _matrix(client, configuration_id)
    for name in approval.approved:
        if name in result.deployments:
            result.deployments[name].approved = True
    result.phase = _finish_phase(result.deployments)
    result.ok = result.phase == "completed"
    result.duration_s = time.monotonic() - started
    return result


def speculative_stack_plan(
    client: TFEClient,
    stack_id: str,
    *,
    deployments: list[str] | None = None,
    timeout: float = 3600,
    on_status: Callable[[Any], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> StackRunResult:
    """Plan every deployment without ever approving anything.

    The ``terraform stacks configuration upload -speculative`` equivalent, over
    the VCS fetch path. It doubles as configuration validation, because a
    malformed ``.tfcomponent.hcl`` or ``.tfdeploy.hcl`` fails at prepare time.

    Args:
        client: The client to act through.
        stack_id: The stack to plan.
        deployments: Restrict the plan to these deployment names.
        timeout: Seconds to wait.
        on_status: Called with the configuration on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.StackRunResult` with ``phase`` of
        ``"planned"``, ``"no_changes"``, ``"prepare_failed"`` or ``"errored"``.

    Raises:
        WorkflowError: If the stack has no VCS repository attached.
        WorkflowTimeout: If the configuration does not settle in time.

    Example:
        >>> result = speculative_stack_plan(client, "st-abc")
        >>> result.phase
        'planned'
    """
    return stack_fetch_and_run(
        client,
        stack_id,
        deployments=deployments,
        speculative=True,
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )


def approve_stack_plans(
    client: TFEClient,
    *,
    configuration_id: str | None = None,
    deployment_group_id: str | None = None,
    deployments: list[str] | None = None,
    confirmed: bool = False,
    confirm: StackConfirm | None = None,
    allow_destroy: bool = False,
) -> StackApprovalResult:
    """Approve the deployment plans waiting for an operator.

    Gated: without ``confirmed=True`` or a ``confirm`` callback this enumerates
    what it *would* approve and returns ``phase="awaiting_confirmation"``,
    writing nothing.

    Note:
        ``approve_all_plans`` clears everything pending in a group, so this
        cannot promise it approved only the deployments it enumerated - a run
        that reaches the gate between the read and the POST is approved too. The
        result carries ``enumerated_at`` and the list it saw so that gap is
        visible rather than hidden.

        Approval can also be partial: an approver without permission on every
        plan in a group approves the ones they can. The result reports
        ``phase="partial"`` when some deployments remain unapproved.

    Args:
        client: The client to act through.
        configuration_id: Approve across every group in this configuration.
        deployment_group_id: Approve one group. Takes precedence.
        deployments: Restrict to these deployment names. Because approval is
            per group, naming a subset still approves any sibling in the same
            group; the result reports what actually cleared.
        confirmed: The caller asserts a human approved these plans.
        confirm: Called with the deployment matrix; return True to approve.
        allow_destroy: Required when any deployment is destroying.

    Returns:
        A :class:`~pytfe.workflows.models.StackApprovalResult`.

    Raises:
        ValueError: If neither identifier is given.
        TFEError: If the API rejects an approval.

    Example:
        >>> approve_stack_plans(client, configuration_id="sc-abc", confirmed=True)
    """
    if not configuration_id and not deployment_group_id:
        raise ValueError("pass configuration_id or deployment_group_id")

    result = StackApprovalResult(
        configuration_id=configuration_id,
        enumerated_at=datetime.now(timezone.utc),
    )

    if deployment_group_id:
        groups = [deployment_group_id]
        pairs = [
            (deployment_group_id, run)
            for run in client.stack_deployment_runs.list(deployment_group_id)
        ]
    else:
        pairs = _runs_for_configuration(client, configuration_id or "")
        groups = sorted({group_id for group_id, _ in pairs})
    result.group_ids = groups

    waiting = [
        (group_id, run)
        for group_id, run in pairs
        if run_is_awaiting_approval(run.status)
        and (deployments is None or run.deployment in deployments)
    ]
    if not waiting:
        result.phase = "nothing_to_approve"
        return result

    matrix = {
        run.deployment or run.id or "?": StackDeploymentState(
            deployment=run.deployment or run.id or "?",
            run_id=run.id,
            group_id=group_id,
            status=_value(run.status),
            awaiting_approval=True,
        )
        for group_id, run in waiting
    }
    result.approvals = [
        StackApproval(deployment=name, run_id=state.run_id)
        for name, state in sorted(matrix.items())
    ]

    if confirm is not None:
        if not confirm(matrix):
            result.phase = "rejected"
            return result
    elif not confirmed:
        result.phase = "awaiting_confirmation"
        return result

    approved_groups = sorted({group_id for group_id, _ in waiting})
    for group_id in approved_groups:
        client.stack_deployment_groups.approve_all_plans(group_id)
        logger.info("approved all plans in deployment group %s", group_id)

    # approve_all_plans returns None, so re-read to find out what actually
    # cleared rather than reporting that the request was accepted.
    for approval in result.approvals:
        if not approval.run_id:
            continue
        try:
            run = client.stack_deployment_runs.read(approval.run_id)
            approval.approved = not run_is_awaiting_approval(run.status)
            if not approval.approved:
                approval.reason = f"still {_value(run.status)} after approval"
        except TFEError as exc:
            approval.reason = f"could not re-read: {exc}"

    if all(a.approved for a in result.approvals):
        result.phase = "approved"
    elif any(a.approved for a in result.approvals):
        result.phase = "partial"
        result.warnings.append(
            "some plans were not approved, which usually means the approver "
            "lacks permission on every plan in the group: "
            + ", ".join(result.not_approved)
        )
    else:
        result.phase = "partial"
        result.ok = False
        result.warnings.append("no plan cleared its approval gate")
    return result


def diagnose_stack_configuration(
    client: TFEClient,
    configuration_id: str,
    *,
    max_diagnostics: int = 50,
) -> StackFailure:
    """Explain why a stack configuration or one of its deployments failed.

    Two distinct failure stages, and they need different reads:

    * **prepare** - the configuration itself is invalid. There are no deployment
      runs to inspect.
    * **plan / apply** - the configuration prepared, but a deployment step
      failed. Diagnostics hang off the step.

    Note:
        Two things are reported rather than fetched, both deliberately. Debug-log
        artifacts can carry credentials, so ``debug_log_step_ids`` gives you the
        step to pass to ``download_artifact``. And prepare-time diagnostics are
        not reachable through this SDK at all - the relationship is a bare
        related link with no list method behind it - so ``prepare_log_url`` is
        the usable path to a prepare failure's detail.

    Args:
        client: The client to read through.
        configuration_id: The configuration to diagnose.
        max_diagnostics: Cap on diagnostics collected.

    Returns:
        A :class:`~pytfe.workflows.models.StackFailure`.

    Raises:
        TFEError: If the configuration cannot be read.

    Example:
        >>> failure = diagnose_stack_configuration(client, "sc-abc")
        >>> failure.stage
        'prepare'
        >>> failure.diagnostics[0].summary
        'Unsupported argument'
    """
    configuration = client.stack_configurations.read(configuration_id)
    status = _value(configuration.status)
    result = StackFailure(
        configuration_id=configuration_id, configuration_status=status
    )
    stack = getattr(configuration, "stack", None)
    result.stack_id = getattr(stack, "id", None)

    if configuration.status in CONFIG_FAILED:
        result.stage = "prepare"
        result.ok = False
        # Configuration diagnostics are reachable only as a raw relationship;
        # read each by id.
        for ref in _diagnostic_refs(configuration):
            if len(result.diagnostics) >= max_diagnostics:
                break
            try:
                diagnostic = client.stack_diagnostics.read(ref)
                result.diagnostics.append(_diagnostic_row(diagnostic))
            except TFEError as exc:
                result.warnings.append(f"diagnostic {ref} unreadable: {exc}")
        result.prepare_log_url = (
            getattr(configuration, "preparing_event_stream_url", None) or None
        )
        if not result.diagnostics:
            result.warnings.append(
                "prepare-time diagnostics are not reachable through this SDK: "
                "the configuration's stack-diagnostics relationship carries "
                "only a related link, and client.stack_diagnostics exposes "
                "read(id)/acknowledge(id) but no list-by-configuration. Read "
                "prepare_log_url for the failure detail."
            )
        result.suggestion = _suggest(result.diagnostics)
        return result

    if not configuration_is_prepared(configuration.status):
        result.stage = "none"
        result.warnings.append(f"configuration is {status}, not a failure")
        return result

    for _group_id, run in _runs_for_configuration(client, configuration_id):
        name = run.deployment or run.id or "?"
        if not run.id:
            continue
        for step in client.stack_deployment_steps.list(run.id):
            phase = step_phase(step.status)
            if step.status in STEP_FAILED:
                result.failed_deployments.append(name)
                operation = (step.operation_type or "").lower()
                if operation in ("plan", "apply"):
                    result.stage = operation  # type: ignore[assignment]
                if step.id:
                    result.debug_log_step_ids[name] = step.id
                    for diagnostic in client.stack_deployment_steps.list_diagnostics(
                        step.id
                    ):
                        if len(result.diagnostics) >= max_diagnostics:
                            break
                        row = _diagnostic_row(diagnostic)
                        row.deployment = name
                        row.step_id = step.id
                        result.diagnostics.append(row)
            elif phase.value == "in_progress" and step.status is not None:
                # A step blocked behind a failed predecessor is a symptom, not a
                # cause; record it separately so the caller is not sent to it.
                if _value(step.status) == "blocked":
                    result.blocked_deployments.append(name)

    result.failed_deployments = sorted(set(result.failed_deployments))
    result.blocked_deployments = sorted(
        set(result.blocked_deployments) - set(result.failed_deployments)
    )
    if not result.failed_deployments:
        result.stage = "none"
        result.warnings.append("no deployment step failed")
    else:
        result.ok = False
        result.suggestion = _suggest(result.diagnostics)
    return result


def _diagnostic_refs(configuration: Any) -> list[str]:
    """Ids from a configuration's raw stack-diagnostics relationship."""
    try:
        relationship = (configuration.relationships or {}).get(
            "stack-diagnostics"
        ) or {}
    except (AttributeError, TypeError):
        return []
    data = relationship.get("data")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [
        d["id"] for d in data if isinstance(d, dict) and isinstance(d.get("id"), str)
    ]


def _diagnostic_row(diagnostic: Any) -> StackDiagnosticRow:
    return StackDiagnosticRow(
        id=getattr(diagnostic, "id", None),
        severity=getattr(diagnostic, "severity", None),
        summary=getattr(diagnostic, "summary", None),
        detail=getattr(diagnostic, "detail", None),
        acknowledged=bool(getattr(diagnostic, "acknowledged", False)),
    )


def _suggest(diagnostics: list[StackDiagnosticRow]) -> str | None:
    haystack = " ".join(
        f"{d.summary or ''} {d.detail or ''}" for d in diagnostics
    ).lower()
    for needle, advice in _SUGGESTIONS:
        if needle in haystack:
            return advice
    return None


def teardown_stack(
    client: TFEClient,
    stack_id: str,
    *,
    confirmed: bool = False,
    force: bool = False,
    destroy_first: bool = True,
    timeout: float = 3600,
) -> StackRunResult:
    """Destroy a stack's deployments, then delete the stack.

    Destruction is driven through the API rather than by editing HCL: the
    configuration create option ``destroy_all`` plans the removal of every
    deployment, and this workflow approves and waits for it before deleting.

    Gated twice over. ``confirmed=True`` is required at all times, and
    ``force=True`` is additionally required to delete a stack whose deployments
    still hold resources - which orphans that infrastructure.

    Args:
        client: The client to act through.
        stack_id: The stack to tear down.
        confirmed: The caller asserts a human approved this destruction.
        force: Delete even if resources remain, orphaning them.
        destroy_first: Run a destroying configuration before deleting.
        timeout: Seconds to wait for the destroy run.

    Returns:
        A :class:`~pytfe.workflows.models.StackRunResult` whose ``phase`` is
        ``"completed"`` when the stack was deleted.

    Raises:
        TFEError: If the API rejects the delete.

    Example:
        >>> teardown_stack(client, "st-abc", confirmed=True)
    """
    started = time.monotonic()
    if not confirmed:
        status = stack_status(client, stack_id)
        return StackRunResult(
            stack_id=stack_id,
            phase="awaiting_approval",
            deployments=status.deployments,
            duration_s=time.monotonic() - started,
            warnings=[
                f"would destroy {len(status.deployments)} deployment(s) and "
                f"delete stack {status.name or stack_id}"
            ],
        )

    result = StackRunResult(
        stack_id=stack_id, phase="planned", duration_s=time.monotonic() - started
    )

    if destroy_first:
        destroyed = stack_fetch_and_run(
            client,
            stack_id,
            destroy_all=True,
            confirmed=True,
            allow_destroy=True,
            timeout=timeout,
        )
        result.deployments = destroyed.deployments
        result.configuration_id = destroyed.configuration_id
        result.warnings.extend(destroyed.warnings)
        if destroyed.phase != "completed" and not force:
            result.phase = destroyed.phase
            result.ok = False
            result.warnings.append(
                f"destroy did not complete ({destroyed.phase}); the stack was "
                "not deleted. Pass force=True to delete anyway and orphan any "
                "remaining resources."
            )
            return result

    if force:
        client.stacks.force_delete(stack_id)
    else:
        client.stacks.delete(stack_id)
    result.phase = "completed"
    result.duration_s = time.monotonic() - started
    return result
