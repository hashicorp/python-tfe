# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Run-shaped workflows: plan, inspect, gate, apply, diagnose.

Every workflow here is built from public ``client.<resource>.<verb>`` calls.
Nothing reaches into the transport or the pagination helper.
"""

from __future__ import annotations

import io
import logging
import os
import time
from collections.abc import Callable
from typing import Any, Literal

from ..client import TFEClient
from ..errors import (
    NotFound,
    RunNotConfirmable,
    TFEError,
    UploadFailed,
    WorkflowTimeout,
)
from ..models.configuration_version import (
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
)
from ..models.run import Run, RunApplyOptions, RunCreateOptions, RunVariable
from ..models.workspace import Workspace
from ._package import package_directory
from ._poll import wait_until
from ._resolve import organization_of, resolve_workspace, run_web_url
from .models import PlanSummary, PolicyResult, RunFailure, RunResult
from .status import RunPhase, is_plan_done, is_terminal, phase_of, run_is_confirmable

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "Confirm",
    "wait_for_run",
    "plan_summary",
    "diagnose_run",
    "apply_with_gate",
    "run_from_directory",
    "speculative_plan",
    "resolve_policy_override",
    "cancel_run",
    "destroy_run",
]

#: Called with the plan summary; return True to proceed with a destructive step.
Confirm = Callable[[PlanSummary], bool]

#: Matched against a failure message to suggest a next step.
_SUGGESTIONS: tuple[tuple[str, str], ...] = (
    (
        "Error acquiring the state lock",
        "The workspace is locked. Inspect with workspace_status(), then "
        "unlock(client, workspace_id) once you are sure no run is active.",
    ),
    (
        "No valid credential sources",
        "The workspace has no provider credentials. Set them as env-category "
        "variables with ensure_variables(..., category='env').",
    ),
    (
        "Unsupported Terraform Core version",
        "Pin a supported version with "
        "ensure_workspace(spec=WorkspaceSpec(terraform_version=...)).",
    ),
    (
        "Invalid provider configuration",
        "Check the workspace's variables and backend configuration.",
    ),
    (
        "Insufficient permissions",
        "The run's token lacks permission on the target provider account.",
    ),
)


def wait_for_run(
    client: TFEClient,
    run_id: str,
    *,
    until: Literal["plan_done", "terminal"] = "terminal",
    timeout: float = 1800,
    interval: float = 3.0,
    on_status: Callable[[Run], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> Run:
    """Poll a run until its plan is done, or until it reaches a terminal state.

    Returns the run itself rather than a bool, so the caller does not need a
    second read to see what happened.

    Args:
        client: The client to poll through.
        run_id: The run to watch.
        until: ``"plan_done"`` stops as soon as the plan finishes - including
            when the run is waiting to be applied or for a policy override.
            ``"terminal"`` waits for the run to finish entirely.
        timeout: Total seconds to wait.
        interval: Initial poll delay; grows to 15s.
        on_status: Called with the run on every poll.

    Returns:
        The last observed run.

    Raises:
        WorkflowTimeout: If the run does not reach the requested state in time.
            The last observed run is attached as ``.last``.

    Example:
        >>> run = wait_for_run(client, "run-CZcmD7eagjhyXAvx", until="plan_done")
        >>> run.status
        <RunStatus.Run_Planned: 'planned'>
    """
    done = is_terminal if until == "terminal" else is_plan_done
    kwargs: dict[str, Any] = {}
    if _sleep is not None:
        kwargs["sleep"] = _sleep
    if _clock is not None:
        kwargs["clock"] = _clock
    return wait_until(
        lambda: client.runs.read(run_id),
        lambda run: done(run.status),
        timeout=timeout,
        interval=interval,
        on_tick=on_status,
        description=f"run {run_id} to reach {until}",
        **kwargs,
    )


def _policy_results(client: TFEClient, run_id: str) -> list[PolicyResult]:
    """Best-effort policy checks for a run."""
    out: list[PolicyResult] = []
    try:
        for check in client.policy_checks.list(run_id):
            status = getattr(check, "status", None)
            status_value = getattr(status, "value", status)
            actions = getattr(check, "actions", None)
            out.append(
                PolicyResult(
                    id=getattr(check, "id", None),
                    name=getattr(check, "scope", None) or getattr(check, "id", None),
                    status=status_value,
                    passed=status_value == "passed" if status_value else None,
                    hard_failed=status_value == "hard_failed",
                    overridable=bool(getattr(actions, "is_overridable", False)),
                )
            )
    except TFEError:
        logger.debug("policy checks unavailable for run %s", run_id)
    return out


def _counts_from_plan_json(
    payload: dict[str, Any], max_resources: int
) -> dict[str, Any]:
    """Derive change counts and addresses from Terraform plan JSON."""
    add = change = destroy = replace = imported = 0
    added: list[str] = []
    changed: list[str] = []
    destroyed: list[str] = []
    replaced: list[str] = []
    truncated = False

    for entry in payload.get("resource_changes") or []:
        addr = entry.get("address", "")
        actions = list((entry.get("change") or {}).get("actions") or [])
        if "create" in actions and "delete" in actions:
            replace += 1
            if len(replaced) < max_resources:
                replaced.append(addr)
            else:
                truncated = True
            continue
        if actions == ["no-op"] or actions == ["read"]:
            continue
        if "create" in actions:
            add += 1
            if len(added) < max_resources:
                added.append(addr)
            else:
                truncated = True
        elif "update" in actions:
            change += 1
            if len(changed) < max_resources:
                changed.append(addr)
            else:
                truncated = True
        elif "delete" in actions:
            destroy += 1
            if len(destroyed) < max_resources:
                destroyed.append(addr)
            else:
                truncated = True
        if (entry.get("change") or {}).get("importing") is not None:
            imported += 1

    return {
        "add": add,
        "change": change,
        "destroy": destroy,
        "replace": replace,
        "import": imported,
        "drift": len(payload.get("resource_drift") or []),
        "added_addresses": added,
        "changed_addresses": changed,
        "destroy_addresses": destroyed,
        "replace_addresses": replaced,
        "output_changes": sorted(payload.get("output_changes") or {}),
        "truncated": truncated,
    }


def plan_summary(
    client: TFEClient,
    run_id: str | None = None,
    *,
    plan_id: str | None = None,
    max_resources: int = 200,
) -> PlanSummary:
    """Summarize what a plan would do.

    Prefers the plan's JSON output, which carries per-resource addresses. When
    that is unavailable - speculative, archived, or permission-limited - falls
    back to the plan resource's own counters and reports
    ``source="plan_attributes"``.

    Args:
        client: The client to read through.
        run_id: The run whose plan to summarize.
        plan_id: A plan ID, as an alternative to ``run_id``.
        max_resources: Cap on addresses collected per category.

    Returns:
        A :class:`~pytfe.workflows.models.PlanSummary`.

    Raises:
        ValueError: If neither ``run_id`` nor ``plan_id`` is given.
        TFEError: If the plan cannot be read at all.

    Example:
        >>> summary = plan_summary(client, "run-CZcmD7eagjhyXAvx")
        >>> print(summary)
        +3 ~1 -0 (no destroys)
    """
    if not run_id and not plan_id:
        raise ValueError("pass run_id or plan_id")

    result = PlanSummary(run_id=run_id, plan_id=plan_id)
    payload: dict[str, Any] | None = None
    try:
        payload = (
            client.plans.read_json_output_for_run(run_id)
            if run_id
            else client.plans.read_json_output(plan_id or "")
        )
    except TFEError as exc:
        result.warnings.append(f"plan JSON unavailable: {exc}")

    if payload:
        for key, value in _counts_from_plan_json(payload, max_resources).items():
            setattr(result, "import_" if key == "import" else key, value)
        result.source = "plan_json"
    else:
        # Fall back to the plan resource's counters.
        result.source = "plan_attributes"
        try:
            plan = (
                client.plans.read_for_run(run_id)
                if run_id
                else client.plans.read(plan_id or "")
            )
            result.plan_id = plan.id or result.plan_id
            result.add = plan.resource_additions or 0
            result.change = plan.resource_changes or 0
            result.destroy = plan.resource_destructions or 0
            result.import_ = getattr(plan, "resource_imports", 0) or 0
        except TFEError as exc:
            result.ok = False
            result.warnings.append(f"plan unavailable: {exc}")

    if run_id:
        result.policy_results = _policy_results(client, run_id)
        try:
            run = client.runs.read(run_id)
            estimate = run.related("cost_estimate") if run.has_relationships else None
            estimate_id = getattr(estimate, "id", None)
            if estimate_id:
                cost = client.cost_estimates.read(estimate_id)
                result.monthly_cost_delta = getattr(cost, "delta_monthly_cost", None)
        except (TFEError, AttributeError):
            logger.debug("cost estimate unavailable for run %s", run_id)

    return result


def _error_lines(log: str, max_lines: int) -> list[str]:
    """Extract Terraform ``Error:`` blocks from a log body."""
    lines = log.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        stripped = line.lstrip("│ ").strip()
        if stripped.startswith("Error:"):
            capturing = True
        if capturing:
            if not stripped and out:
                capturing = False
                continue
            out.append(line.rstrip())
            if len(out) >= max_lines:
                break
    if not out and lines:
        out = [line.rstrip() for line in lines[-max_lines:]]
    return out


def _suggest(message: str | None, lines: list[str]) -> str | None:
    haystack = "\n".join([message or "", *lines])
    for needle, advice in _SUGGESTIONS:
        if needle.lower() in haystack.lower():
            return advice
    return None


def diagnose_run(client: TFEClient, run_id: str, *, max_lines: int = 60) -> RunFailure:
    """Explain why a run failed, and suggest what to do about it.

    Note:
        ``client.plans.logs()`` and ``client.applies.logs()`` are placeholder
        implementations in pytfe |version| and always return an empty string, so
        the log excerpt will be empty. The ``log_read_url`` field carries the
        URL to fetch the log from directly, and a warning records the gap. The
        structured signals - stage, status, policy failures, errored-state
        availability - are derived without logs and are always populated.

    Args:
        client: The client to read through.
        run_id: The failed run.
        max_lines: Cap on extracted log lines.

    Returns:
        A :class:`~pytfe.workflows.models.RunFailure`.

    Raises:
        TFEError: If the run cannot be read.

    Example:
        >>> failure = diagnose_run(client, "run-CZcmD7eagjhyXAvx")
        >>> print(failure.stage, failure.suggestion)
    """
    run = client.runs.read(run_id)
    status = getattr(run.status, "value", run.status)
    result = RunFailure(run_id=run_id, status=status)

    phase = phase_of(run.status)
    if phase is not RunPhase.TERMINAL:
        result.stage = "none"
        result.message = f"run is {status}, not a failure"
        return result

    if status == "canceled":
        result.stage = "canceled"
        result.message = "run was canceled"
        return result
    if status in ("applied", "planned_and_finished"):
        result.stage = "none"
        result.message = f"run finished successfully ({status})"
        return result

    policies = _policy_results(client, run_id)
    result.policy_failures = [p for p in policies if p.passed is False]

    log = ""
    plan_id = apply_id = None
    try:
        plan = client.plans.read_for_run(run_id)
        plan_id = plan.id
        plan_status = getattr(plan.status, "value", plan.status)
        if plan_status == "errored":
            result.stage = "plan"
            result.log_read_url = plan.log_read_url
            log = client.plans.logs(plan_id or "")
    except TFEError:
        logger.debug("no plan for run %s", run_id)

    if result.stage == "unknown":
        try:
            apply_rel = run.related("apply") if run.has_relationships else None
            apply_id = getattr(apply_rel, "id", None)
            if apply_id:
                apply_obj = client.applies.read(apply_id)
                apply_status = getattr(apply_obj.status, "value", apply_obj.status)
                if apply_status == "errored":
                    result.stage = "apply"
                    result.log_read_url = apply_obj.log_read_url
                    log = client.applies.logs(apply_id)
                try:
                    client.applies.errored_state(apply_id)
                    result.errored_state_available = True
                except NotFound:
                    result.errored_state_available = False
        except (TFEError, AttributeError):
            logger.debug("no apply for run %s", run_id)

    if result.stage == "unknown" and result.policy_failures:
        result.stage = "policy"
        result.message = "; ".join(
            f"{p.name}: {p.status}" for p in result.policy_failures
        )

    if log:
        result.error_lines = _error_lines(log, max_lines)
        result.log_excerpt = "\n".join(result.error_lines)
    else:
        result.warnings.append(
            "log body unavailable: client.plans.logs/applies.logs are placeholder "
            "implementations that return an empty string. Fetch log_read_url "
            "directly for the full log."
        )

    if not result.message:
        result.message = (
            result.error_lines[0] if result.error_lines else f"run {status}"
        )
    result.suggestion = _suggest(result.message, result.error_lines)
    result.ok = False
    return result


def _gate(
    plan: PlanSummary,
    *,
    confirmed: bool,
    confirm: Confirm | None,
    allow_destroy: bool,
) -> str | None:
    """Apply the destructive-gate rules. Returns a blocking phase, or None."""
    if plan.is_destructive and not allow_destroy:
        return "refused_destructive"
    if confirm is not None:
        return None if confirm(plan) else "rejected"
    if not confirmed:
        return "awaiting_confirmation"
    return None


def apply_with_gate(
    client: TFEClient,
    run_id: str,
    *,
    confirmed: bool = False,
    confirm: Confirm | None = None,
    allow_destroy: bool = False,
    comment: str | None = None,
    timeout: float = 1800,
    on_status: Callable[[Run], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> RunResult:
    """Apply a planned run, but only behind an explicit gate.

    There is no ``auto_apply=True``. A caller must either pass
    ``confirmed=True`` - asserting a human approved this - or supply a
    ``confirm`` callback. Without one, the workflow stops and returns
    ``phase="awaiting_confirmation"`` rather than raising. A plan containing
    destroys or replaces is refused outright unless ``allow_destroy=True``,
    even when ``confirmed=True``.

    Args:
        client: The client to act through.
        run_id: The run to apply.
        confirmed: The caller asserts a human approved this apply.
        confirm: Called with the plan summary; return True to proceed.
        allow_destroy: Permit a plan that destroys or replaces resources.
        comment: Posted with the apply.
        timeout: Seconds to wait for the apply to finish.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult`.

    Raises:
        RunNotConfirmable: If the run cannot be applied in its current state.

    Example:
        >>> result = apply_with_gate(client, run.id, confirmed=True)
        >>> result.phase
        'applied'
    """
    started = time.monotonic()
    run = client.runs.read(run_id)
    if not run_is_confirmable(run):
        raise RunNotConfirmable(
            f"run {run_id} is {getattr(run.status, 'value', run.status)} "
            "and cannot be applied"
        )

    summary = plan_summary(client, run_id)
    blocked = _gate(
        summary, confirmed=confirmed, confirm=confirm, allow_destroy=allow_destroy
    )
    if blocked:
        return RunResult(
            run_id=run_id,
            workspace_id=_workspace_id_of(run),
            phase=blocked,
            status=getattr(run.status, "value", run.status),
            plan=summary,
            ok=blocked != "refused_destructive",
            run=run,
            duration_s=time.monotonic() - started,
        )

    if comment:
        try:
            from ..models.comment import CommentCreateOptions

            client.comments.create(run_id, CommentCreateOptions(body=comment))
        except TFEError as exc:
            logger.debug("could not post comment on run %s: %s", run_id, exc)

    logger.info("applying run %s", run_id)
    client.runs.apply(run_id, RunApplyOptions(comment=comment))
    final = wait_for_run(
        client,
        run_id,
        until="terminal",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    return _finish(client, final, summary, started)


def _workspace_id_of(run: Run) -> str | None:
    try:
        workspace = run.related("workspace") if run.has_relationships else None
        return getattr(workspace, "id", None)
    except (AttributeError, TFEError):
        return None


def _finish(
    client: TFEClient, run: Run, summary: PlanSummary | None, started: float
) -> RunResult:
    """Build the terminal RunResult for a finished run."""
    status = getattr(run.status, "value", run.status)
    workspace_id = _workspace_id_of(run)
    result = RunResult(
        run_id=run.id,
        workspace_id=workspace_id,
        phase="applied" if status == "applied" else "errored",
        status=status,
        plan=summary,
        applied=status == "applied",
        run=run,
        duration_s=time.monotonic() - started,
    )
    if status != "applied":
        result.ok = False
        result.failure = diagnose_run(client, run.id or "")
        return result

    if workspace_id:
        try:
            from .state import read_outputs

            result.outputs = read_outputs(client, workspace_id).values
        except TFEError as exc:
            result.warnings.append(f"outputs unavailable: {exc}")
    return result


def run_from_directory(
    client: TFEClient,
    directory: str | os.PathLike[str],
    *,
    workspace_id: str | None = None,
    organization: str | None = None,
    workspace_name: str | None = None,
    message: str = "Queued by pytfe.workflows",
    speculative: bool = False,
    plan_only: bool = False,
    is_destroy: bool = False,
    target_addrs: list[str] | None = None,
    replace_addrs: list[str] | None = None,
    run_variables: dict[str, str] | None = None,
    confirmed: bool = False,
    confirm: Confirm | None = None,
    allow_destroy: bool = False,
    on_reject: Literal["discard", "leave"] = "discard",
    timeout: float = 1800,
    upload_timeout: float = 120,
    on_status: Callable[[Run], None] | None = None,
) -> RunResult:
    """Upload a configuration directory and drive it to a decision.

    The end-to-end API-driven run: create a configuration version, upload the
    directory, queue a run, wait for the plan, then stop at the gate. Applies
    only when explicitly permitted - see :func:`apply_with_gate`.

    The directory is packaged with Terraform's own exclusions
    (``.git/``, ``.terraform/``, and any ``.terraformignore``), not with
    ``pytfe.utils.pack_contents``, which would ship provider binaries.

    Args:
        client: The client to act through.
        directory: Local configuration directory to upload.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        message: Run message.
        speculative: Create a speculative (plan-only, never applied) run.
        plan_only: Queue a plan-only run.
        is_destroy: Queue a destroy run.
        target_addrs: ``-target`` addresses.
        replace_addrs: ``-replace`` addresses.
        run_variables: One-off run variables.
        confirmed: The caller asserts a human approved applying this.
        confirm: Called with the plan summary; return True to apply.
        allow_destroy: Permit a destructive plan.
        on_reject: What to do when ``confirm`` returns False.
        timeout: Seconds to wait for the run.
        upload_timeout: Seconds to wait for the upload to be processed.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult`. Branch on ``.phase``.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.
        UploadFailed: If the configuration version does not reach ``uploaded``.
        WorkflowTimeout: If the run does not settle in time.

    Example:
        >>> result = run_from_directory(
        ...     client, "./terraform", organization="acme", workspace_name="web"
        ... )
        >>> if result.phase == "awaiting_confirmation":
        ...     print(result.plan)
    """
    started = time.monotonic()
    workspace = resolve_workspace(
        client,
        workspace_id,
        organization=organization,
        workspace_name=workspace_name,
    )
    ws_id = workspace.id or ""

    if is_destroy and not allow_destroy:
        return RunResult(
            workspace_id=ws_id,
            phase="refused_destructive",
            ok=False,
            warnings=["is_destroy=True requires allow_destroy=True"],
            duration_s=time.monotonic() - started,
        )

    logger.info("creating configuration version for workspace %s", ws_id)
    config_version = client.configuration_versions.create(
        ws_id,
        ConfigurationVersionCreateOptions(
            auto_queue_runs=False, speculative=speculative or None
        ),
    )
    if not config_version.upload_url:
        raise UploadFailed("configuration version did not include an upload URL")

    archive = package_directory(directory)
    client.configuration_versions.upload_tar_gzip(
        config_version.upload_url, io.BytesIO(archive)
    )

    cv_id = config_version.id or ""
    processed = wait_until(
        lambda: client.configuration_versions.read(cv_id),
        lambda cv: getattr(cv.status, "value", cv.status) in ("uploaded", "errored"),
        timeout=upload_timeout,
        interval=1.0,
        description=f"configuration version {cv_id} to finish uploading",
    )
    if getattr(processed.status, "value", processed.status) == "errored":
        raise UploadFailed(f"configuration version {cv_id} errored during upload")

    variables = (
        [RunVariable(key=k, value=v) for k, v in run_variables.items()]
        if run_variables
        else None
    )
    run = client.runs.create(
        RunCreateOptions(
            workspace=Workspace(id=ws_id),
            configuration_version=ConfigurationVersion(id=cv_id),
            message=message,
            is_destroy=is_destroy or None,
            plan_only=(plan_only or speculative) or None,
            target_addrs=target_addrs,
            replace_addrs=replace_addrs,
            variables=variables,
        )
    )
    run_id = run.id or ""
    url = run_web_url(
        client,
        organization_of(client, workspace, organization),
        workspace.name or "",
        run_id,
    )
    logger.info("queued run %s", run_id)

    planned = wait_for_run(
        client, run_id, until="plan_done", timeout=timeout, on_status=on_status
    )
    status = getattr(planned.status, "value", planned.status)

    def _result(phase: str, **kw: Any) -> RunResult:
        return RunResult(
            run_id=run_id,
            workspace_id=ws_id,
            configuration_version_id=cv_id,
            phase=phase,
            status=status,
            url=url,
            run=planned,
            duration_s=time.monotonic() - started,
            **kw,
        )

    if status in ("errored", "canceled", "discarded"):
        return _result("errored", ok=False, failure=diagnose_run(client, run_id))
    if status == "planned_and_finished":
        return _result("no_changes", plan=plan_summary(client, run_id))

    summary = plan_summary(client, run_id)
    if phase_of(planned.status) is RunPhase.AWAITING_DECISION:
        return _result("awaiting_policy_override", plan=summary, ok=False)
    if speculative or plan_only:
        return _result("planned", plan=summary)

    blocked = _gate(
        summary, confirmed=confirmed, confirm=confirm, allow_destroy=allow_destroy
    )
    if blocked == "rejected" and on_reject == "discard":
        try:
            client.runs.discard(run_id)
        except TFEError as exc:
            logger.debug("could not discard run %s: %s", run_id, exc)
    if blocked:
        return _result(
            blocked, plan=summary, ok=blocked not in ("refused_destructive",)
        )

    client.runs.apply(run_id, RunApplyOptions(comment=None))
    final = wait_for_run(
        client, run_id, until="terminal", timeout=timeout, on_status=on_status
    )
    result = _finish(client, final, summary, started)
    result.configuration_version_id = cv_id
    result.url = url
    return result


def speculative_plan(
    client: TFEClient,
    directory: str | os.PathLike[str],
    *,
    workspace_id: str | None = None,
    organization: str | None = None,
    workspace_name: str | None = None,
    message: str = "Speculative plan by pytfe.workflows",
    run_variables: dict[str, str] | None = None,
    timeout: float = 1800,
    on_status: Callable[[Run], None] | None = None,
) -> RunResult:
    """Plan a configuration directory without ever applying it.

    The safe default for "what would this change?" - PR checks, drift questions,
    and anything an agent runs before a human is in the loop.

    Args:
        client: The client to act through.
        directory: Local configuration directory to plan.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        message: Run message.
        run_variables: One-off run variables.
        timeout: Seconds to wait for the plan.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult` with ``phase="planned"``
        or ``"errored"``.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.
        WorkflowTimeout: If the plan does not finish in time.

    Example:
        >>> result = speculative_plan(
        ...     client, "./terraform", organization="acme", workspace_name="web"
        ... )
        >>> print(result.plan)
    """
    return run_from_directory(
        client,
        directory,
        workspace_id=workspace_id,
        organization=organization,
        workspace_name=workspace_name,
        message=message,
        speculative=True,
        plan_only=True,
        run_variables=run_variables,
        timeout=timeout,
        on_status=on_status,
    )


def resolve_policy_override(
    client: TFEClient,
    run_id: str,
    *,
    action: Literal["override", "discard"],
    reason: str = "",
    confirmed: bool = False,
    confirm: Confirm | None = None,
    allow_destroy: bool = False,
    timeout: float = 1800,
    on_status: Callable[[Run], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> RunResult:
    """Resolve a run paused on a failed policy check.

    A soft-failed policy leaves a run in a state that never resolves on its own.
    This either overrides the failing checks and continues to the gated apply,
    or discards the run.

    Overriding is destructive and gated exactly like an apply: ``confirmed=True``
    or a ``confirm`` callback is required, and a destructive plan still needs
    ``allow_destroy=True``. Discarding is not gated - it destroys nothing.

    Args:
        client: The client to act through.
        run_id: The paused run.
        action: ``"override"`` to continue, ``"discard"`` to abandon the run.
        reason: Comment recorded with the decision.
        confirmed: The caller asserts a human approved the override.
        confirm: Called with the plan summary; return True to override.
        allow_destroy: Permit a destructive plan after overriding.
        timeout: Seconds to wait for the run to finish.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult` whose ``phase`` is
        ``"applied"``, ``"errored"``, ``"rejected"``, ``"refused_destructive"``
        or ``"awaiting_confirmation"``.

    Raises:
        TFEError: If the run or its policy checks cannot be read.

    Example:
        >>> resolve_policy_override(client, run.id, action="override",
        ...                         reason="approved by platform team",
        ...                         confirmed=True)
    """
    started = time.monotonic()
    run = client.runs.read(run_id)
    status = getattr(run.status, "value", run.status)
    checks = _policy_results(client, run_id)
    failed = [c for c in checks if c.passed is False]

    if action == "discard":
        from ..models.run import RunDiscardOptions

        client.runs.discard(run_id, RunDiscardOptions(comment=reason or None))
        return RunResult(
            run_id=run_id,
            workspace_id=_workspace_id_of(run),
            phase="rejected",
            status=status,
            run=run,
            duration_s=time.monotonic() - started,
        )

    summary = plan_summary(client, run_id)
    summary.policy_results = checks
    blocked = _gate(
        summary, confirmed=confirmed, confirm=confirm, allow_destroy=allow_destroy
    )
    if blocked:
        return RunResult(
            run_id=run_id,
            workspace_id=_workspace_id_of(run),
            phase=blocked,
            status=status,
            plan=summary,
            ok=blocked != "refused_destructive",
            run=run,
            duration_s=time.monotonic() - started,
        )

    overridden: list[str] = []
    for check in failed:
        if not check.overridable or not check.id:
            continue
        client.policy_checks.override(check.id)
        overridden.append(check.id)
    logger.info("overrode %d policy check(s) on run %s", len(overridden), run_id)

    client.runs.apply(run_id, RunApplyOptions(comment=reason or None))
    final = wait_for_run(
        client,
        run_id,
        until="terminal",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    result = _finish(client, final, summary, started)
    if not overridden and failed:
        result.warnings.append(
            "no failing policy check was overridable; the run was applied without "
            "overriding anything"
        )
    return result


def cancel_run(
    client: TFEClient,
    run_id: str,
    *,
    reason: str = "",
    force_after: float = 60,
    timeout: float = 300,
    on_status: Callable[[Run], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> RunResult:
    """Cancel a run, escalating to a force-cancel if it does not stop.

    Note:
        This is the one destructive-tier workflow that is *not* gated. Cancelling
        stops work in progress; it never destroys infrastructure. A run cancelled
        mid-apply can leave partially-applied resources, which is why
        ``force_after`` gives the graceful cancel a chance first.

    Args:
        client: The client to act through.
        run_id: The run to cancel.
        reason: Comment recorded with the cancellation.
        force_after: Seconds to wait for a graceful cancel before force-cancelling.
        timeout: Total seconds to wait for the run to stop.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult`.

    Raises:
        WorkflowTimeout: If the run never reaches a terminal state.
        TFEError: If the cancel is rejected.

    Example:
        >>> cancel_run(client, "run-CZcmD7eagjhyXAvx", reason="superseded")
    """
    from ..models.run import RunCancelOptions, RunForceCancelOptions

    started = time.monotonic()
    run = client.runs.read(run_id)
    if is_terminal(run.status):
        return RunResult(
            run_id=run_id,
            workspace_id=_workspace_id_of(run),
            phase="errored" if run.status != "applied" else "applied",
            status=getattr(run.status, "value", run.status),
            run=run,
            warnings=["run had already finished; nothing to cancel"],
            duration_s=time.monotonic() - started,
        )

    client.runs.cancel(run_id, RunCancelOptions(comment=reason or None))

    try:
        final = wait_for_run(
            client,
            run_id,
            until="terminal",
            timeout=force_after,
            on_status=on_status,
            _sleep=_sleep,
            _clock=_clock,
        )
    except WorkflowTimeout:
        current = client.runs.read(run_id)
        actions = current.actions
        if actions is not None and actions.is_force_cancelable:
            logger.info("escalating to force-cancel for run %s", run_id)
            client.runs.force_cancel(
                run_id, RunForceCancelOptions(comment=reason or None)
            )
        final = wait_for_run(
            client,
            run_id,
            until="terminal",
            timeout=timeout,
            on_status=on_status,
            _sleep=_sleep,
            _clock=_clock,
        )

    status = getattr(final.status, "value", final.status)
    return RunResult(
        run_id=run_id,
        workspace_id=_workspace_id_of(final),
        phase="errored" if status != "applied" else "applied",
        status=status,
        ok=status in ("canceled", "discarded"),
        run=final,
        duration_s=time.monotonic() - started,
    )


def destroy_run(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
    message: str = "Destroy by pytfe.workflows",
    confirmed: bool = False,
    confirm: Confirm | None = None,
    timeout: float = 3600,
    on_status: Callable[[Run], None] | None = None,
    _sleep: Callable[[float], None] | None = None,
    _clock: Callable[[], float] | None = None,
) -> RunResult:
    """Queue and apply a destroy run against a workspace's current configuration.

    The most destructive operation in this package. It is gated unconditionally:
    ``confirmed=True`` or a ``confirm`` callback is mandatory, and unlike other
    workflows there is no ``allow_destroy`` to set, because destruction is the
    entire point.

    Requires the workspace's ``allow_destroy_plan`` to be enabled; otherwise the
    workflow refuses before queueing anything.

    Args:
        client: The client to act through.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        message: Run message.
        confirmed: The caller asserts a human approved this destruction.
        confirm: Called with the plan summary; return True to destroy.
        timeout: Seconds to wait for the run.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult`.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.
        WorkflowTimeout: If the run does not settle in time.

    Example:
        >>> destroy_run(client, organization="acme", workspace_name="scratch",
        ...             confirmed=True)
    """
    started = time.monotonic()
    workspace = resolve_workspace(
        client, workspace_id, organization=organization, workspace_name=workspace_name
    )
    ws_id = workspace.id or ""

    if not workspace.allow_destroy_plan:
        return RunResult(
            workspace_id=ws_id,
            phase="refused_destructive",
            ok=False,
            warnings=[
                "workspace has allow_destroy_plan disabled; enable it with "
                "ensure_workspace(spec=WorkspaceSpec(allow_destroy_plan=True)) "
                "before destroying"
            ],
            duration_s=time.monotonic() - started,
        )

    run = client.runs.create(
        RunCreateOptions(
            workspace=Workspace(id=ws_id), message=message, is_destroy=True
        )
    )
    run_id = run.id or ""
    url = run_web_url(
        client,
        organization_of(client, workspace, organization),
        workspace.name or "",
        run_id,
    )

    planned = wait_for_run(
        client,
        run_id,
        until="plan_done",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    status = getattr(planned.status, "value", planned.status)
    if status in ("errored", "canceled", "discarded"):
        return RunResult(
            run_id=run_id,
            workspace_id=ws_id,
            phase="errored",
            status=status,
            ok=False,
            failure=diagnose_run(client, run_id),
            url=url,
            run=planned,
            duration_s=time.monotonic() - started,
        )

    summary = plan_summary(client, run_id)
    # allow_destroy is implied - destruction is the whole point - but an
    # explicit human decision is not.
    blocked = _gate(summary, confirmed=confirmed, confirm=confirm, allow_destroy=True)
    if blocked:
        return RunResult(
            run_id=run_id,
            workspace_id=ws_id,
            phase=blocked,
            status=status,
            plan=summary,
            url=url,
            run=planned,
            duration_s=time.monotonic() - started,
        )

    client.runs.apply(run_id, RunApplyOptions(comment=message))
    final = wait_for_run(
        client,
        run_id,
        until="terminal",
        timeout=timeout,
        on_status=on_status,
        _sleep=_sleep,
        _clock=_clock,
    )
    result = _finish(client, final, summary, started)
    result.url = url
    if result.applied:
        remaining = client.workspaces.read_by_id(ws_id).resource_count
        if remaining:
            result.warnings.append(
                f"{remaining} resource(s) still tracked after the destroy run"
            )
    return result
