# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""analyze_plan, the policy gate, sensitive outputs, and attribute inventories."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pytfe.errors import NotFound
from pytfe.models.run import Run
from pytfe.models.state_version import StateVersion
from pytfe.models.workspace import Workspace
from pytfe.workflows import (
    analyze_plan,
    apply_with_gate,
    queue_run,
    read_outputs,
    state_inventory,
)

# --------------------------------------------------------------------------
# analyze_plan
# --------------------------------------------------------------------------

PLAN = {
    "format_version": "1.2",
    "resource_changes": [
        {
            "address": "aws_instance.web",
            "type": "aws_instance",
            "name": "web",
            "provider_name": "registry.terraform.io/hashicorp/aws",
            "action_reason": "replace_because_cannot_update",
            "change": {
                "actions": ["delete", "create"],
                "before": {"ami": "ami-old", "instance_type": "t3.micro", "id": "i-1"},
                "after": {"ami": "ami-new", "instance_type": "t3.micro"},
                "after_unknown": {"id": True, "arn": True},
            },
        },
        {
            "address": "aws_db_instance.main",
            "type": "aws_db_instance",
            "name": "main",
            "change": {
                "actions": ["update"],
                "before": {"password": "old", "size": 10},
                "after": {"password": "new", "size": 20},
                "after_sensitive": {"password": True},
            },
        },
        {
            "address": "aws_vpc.main",
            "change": {"actions": ["no-op"], "before": {}, "after": {}},
        },
    ],
    "output_changes": {
        "endpoint": {"actions": ["update"]},
        "secret": {"actions": ["update"], "after_sensitive": True},
        "unchanged": {"actions": ["no-op"]},
    },
    "resource_drift": [{"address": "aws_iam_role.app"}],
}


def test_reports_changed_attributes_not_values(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    web = next(r for r in analysis.resources if r.address == "aws_instance.web")
    assert web.changed_attributes == ["ami"]
    # Values must never appear anywhere in the result.
    assert "ami-new" not in json.dumps(analysis.model_dump(mode="json"))


def test_computed_attributes_stay_disjoint_from_changes(client: Any) -> None:
    """`id` differs between before and after only because it is computed;
    counting it as a change makes every plan look like a rewrite."""
    analysis = analyze_plan(client, payload=PLAN)
    web = next(r for r in analysis.resources if r.address == "aws_instance.web")
    assert "id" in web.computed_attributes
    assert "id" not in web.changed_attributes
    assert set(web.computed_attributes) == {"arn", "id"}


def test_surfaces_the_replacement_reason(client: Any) -> None:
    """The answer to 'why is this being destroyed when I changed one field'."""
    analysis = analyze_plan(client, payload=PLAN)
    assert analysis.replaced_because == {
        "aws_instance.web": "replace_because_cannot_update"
    }


def test_classifies_destructive_changes(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    web = next(r for r in analysis.resources if r.address == "aws_instance.web")
    db = next(r for r in analysis.resources if r.address == "aws_db_instance.main")
    assert web.is_replace and web.is_destructive and not web.is_destroy
    assert not db.is_destructive
    assert [r.address for r in analysis.destructive] == ["aws_instance.web"]


def test_flags_sensitive_attributes_without_reading_them(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    db = next(r for r in analysis.resources if r.address == "aws_db_instance.main")
    assert db.sensitive_attributes == ["password"]
    assert "password" in db.changed_attributes  # it changed...
    rendered = json.dumps(analysis.model_dump(mode="json"))
    assert "old" not in rendered and '"new"' not in rendered  # ...but not its value


def test_skips_noops_and_collects_outputs_and_drift(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    assert [r.address for r in analysis.resources] == [
        "aws_instance.web",
        "aws_db_instance.main",
    ]
    assert {o.name for o in analysis.output_changes} == {"endpoint", "secret"}
    assert next(o for o in analysis.output_changes if o.name == "secret").sensitive
    assert analysis.drift == ["aws_iam_role.app"]


def test_touching_finds_resources_by_attribute(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    assert [r.address for r in analysis.touching("ami")] == ["aws_instance.web"]


def test_summary_is_small_and_serializable(client: Any) -> None:
    analysis = analyze_plan(client, payload=PLAN)
    summary = analysis.summary()
    json.dumps(summary)
    assert summary["destructive_count"] == 1
    assert summary["destructive"] == ["delete/create aws_instance.web"]


def test_truncates_a_huge_plan(client: Any) -> None:
    payload = {
        "resource_changes": [
            {"address": f"aws_instance.n{i}", "change": {"actions": ["create"]}}
            for i in range(50)
        ]
    }
    analysis = analyze_plan(client, payload=payload, max_resources=10)
    assert len(analysis.resources) == 10
    assert analysis.truncated is True


def test_reads_plan_json_when_no_payload(client: Any) -> None:
    client.plans.read_json_output_for_run.return_value = PLAN
    analysis = analyze_plan(client, "run-1")
    client.plans.read_json_output_for_run.assert_called_once_with("run-1")
    assert analysis.resources


def test_missing_plan_json_is_reported_not_raised(client: Any) -> None:
    client.plans.read_json_output_for_run.return_value = None
    analysis = analyze_plan(client, "run-1")
    assert analysis.ok is False
    assert analysis.warnings


def test_requires_an_identifier(client: Any) -> None:
    with pytest.raises(ValueError, match="run_id, plan_id or payload"):
        analyze_plan(client)


# --------------------------------------------------------------------------
# the policy gate
# --------------------------------------------------------------------------


def make_run(status: str, *, confirmable: bool = True) -> Run:
    return Run.model_validate(
        {
            "id": "run-1",
            "status": status,
            "actions": {
                "is-cancelable": True,
                "is-confirmable": confirmable,
                "is-discardable": True,
                "is-force-cancelable": False,
            },
        }
    )


def _planned_with_policy(client: Any, status: str) -> None:
    """Stage a planned run whose single policy check has ``status``.

    ``runs.read`` is driven by a callable because apply_with_gate reads the run
    for the confirmable check, again for the cost estimate, and again while
    polling after the apply - and the last of those must report a finished run.
    """
    from pytfe.models.policy_check import PolicyCheck

    state = {"applied": False}

    def read(_run_id: str) -> Run:
        return make_run("applied" if state["applied"] else "planned")

    def apply(_run_id: str, _options: Any = None) -> None:
        state["applied"] = True

    client.runs.read.side_effect = read
    client.runs.apply.side_effect = apply
    client.plans.read_json_output_for_run.return_value = {
        "resource_changes": [
            {"address": "aws_s3_bucket.logs", "change": {"actions": ["create"]}}
        ]
    }
    # A fresh iterator per call: plan_summary consumes it, and so does any
    # later diagnose_run.
    client.policy_checks.list.side_effect = lambda *a, **k: iter(
        [PolicyCheck.model_validate({"id": "polchk-1", "status": status})]
    )


def test_hard_failed_policy_blocks_the_apply(client: Any) -> None:
    """The gate collected policy_results and used to ignore them entirely."""
    _planned_with_policy(client, "hard_failed")
    result = apply_with_gate(client, "run-1", confirmed=True)
    assert result.phase == "refused_policy"
    assert result.ok is False
    client.runs.apply.assert_not_called()


def test_soft_failed_policy_blocks_by_default(client: Any) -> None:
    _planned_with_policy(client, "soft_failed")
    result = apply_with_gate(client, "run-1", confirmed=True)
    assert result.phase == "refused_policy"
    client.runs.apply.assert_not_called()


def test_allow_advisory_permits_a_soft_failure(client: Any, clock: Any) -> None:
    _planned_with_policy(client, "soft_failed")
    apply_with_gate(
        client,
        "run-1",
        confirmed=True,
        policy="allow_advisory",
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    client.runs.apply.assert_called_once()


def test_overridden_policy_is_not_treated_as_a_failure(client: Any, clock: Any) -> None:
    """Someone already made that call; blocking again would be a deadlock."""
    _planned_with_policy(client, "overridden")
    apply_with_gate(
        client, "run-1", confirmed=True, _sleep=clock.sleep, _clock=clock.time
    )
    client.runs.apply.assert_called_once()


def test_passed_policy_permits_the_apply(client: Any, clock: Any) -> None:
    _planned_with_policy(client, "passed")
    apply_with_gate(
        client, "run-1", confirmed=True, _sleep=clock.sleep, _clock=clock.time
    )
    client.runs.apply.assert_called_once()


def test_policy_ignore_bypasses_the_check(client: Any, clock: Any) -> None:
    _planned_with_policy(client, "hard_failed")
    apply_with_gate(
        client,
        "run-1",
        confirmed=True,
        policy="ignore",
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    client.runs.apply.assert_called_once()


def test_destructive_still_outranks_policy(client: Any) -> None:
    """A refusal the caller cannot override is reported first."""
    _planned_with_policy(client, "hard_failed")
    client.plans.read_json_output_for_run.return_value = {
        "resource_changes": [
            {"address": "aws_instance.web", "change": {"actions": ["delete"]}}
        ]
    }
    result = apply_with_gate(client, "run-1", confirmed=True)
    assert result.phase == "refused_destructive"


# --------------------------------------------------------------------------
# sensitive outputs
# --------------------------------------------------------------------------


def make_output(name: str, value: Any, sensitive: bool, oid: str) -> Any:
    from pytfe.models.state_version_output import StateVersionOutput

    return StateVersionOutput.model_validate(
        {
            "id": oid,
            "name": name,
            "value": value,
            "sensitive": sensitive,
            "type": "string",
        }
    )


def _outputs(client: Any) -> None:
    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.state_versions.read_current.return_value = StateVersion.model_validate(
        {"id": "sv-1", "serial": 1, "resources-processed": True}
    )
    client.state_version_outputs.read_current.return_value = iter(
        [
            make_output("vpc_id", "vpc-123", False, "wsout-1"),
            # The listing endpoint nulls sensitive values.
            make_output("db_password", None, True, "wsout-2"),
        ]
    )


def test_sensitive_outputs_are_masked_by_default(client: Any) -> None:
    _outputs(client)
    outputs = read_outputs(client, "ws-1")
    assert outputs.values["db_password"] == "<sensitive>"
    client.state_version_outputs.read.assert_not_called()


def test_include_sensitive_rereads_the_individual_output(client: Any) -> None:
    """Regression: the flag used to return None, because the listing endpoint
    redacts. Only the per-output read carries the value."""
    _outputs(client)
    client.state_version_outputs.read.return_value = make_output(
        "db_password", "hunter2", True, "wsout-2"
    )
    outputs = read_outputs(client, "ws-1", include_sensitive=True)
    client.state_version_outputs.read.assert_called_once_with("wsout-2")
    assert outputs.values["db_password"] == "hunter2"


def test_summary_never_leaks_even_with_include_sensitive(client: Any) -> None:
    _outputs(client)
    client.state_version_outputs.read.return_value = make_output(
        "db_password", "hunter2", True, "wsout-2"
    )
    outputs = read_outputs(client, "ws-1", include_sensitive=True)
    assert "hunter2" not in json.dumps(outputs.summary())


def test_unreadable_sensitive_output_is_reported(client: Any) -> None:
    _outputs(client)
    client.state_version_outputs.read.side_effect = NotFound("gone")
    outputs = read_outputs(client, "ws-1", include_sensitive=True)
    assert outputs.values["db_password"] == "<sensitive>"
    assert any("db_password" in w for w in outputs.warnings)


# --------------------------------------------------------------------------
# state_inventory with attributes
# --------------------------------------------------------------------------

STATE = {
    "version": 4,
    "resources": [
        {
            "mode": "managed",
            "type": "aws_instance",
            "name": "web",
            "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
            "instances": [
                {
                    "index_key": 0,
                    "attributes": {"public_ip": "10.0.0.1", "password": "s3cret"},
                    "sensitive_attributes": [
                        [{"type": "get_attr", "value": "password"}]
                    ],
                },
                {"index_key": 1, "attributes": {"public_ip": "10.0.0.2"}},
            ],
        }
    ],
}


def _state(client: Any) -> None:
    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.state_versions.read_current.return_value = StateVersion.model_validate(
        {"id": "sv-1", "serial": 1, "resources-processed": True}
    )
    client.state_versions.download.return_value = json.dumps(STATE).encode()


def test_attributes_answer_the_ip_question(client: Any) -> None:
    """The whole point: 'give me every machine with its IP'."""
    _state(client)
    inventory = state_inventory(client, "ws-1", include_attributes=True)
    ips = [
        r.attributes["public_ip"]
        for r in inventory.resources
        if r.type == "aws_instance" and r.attributes
    ]
    assert ips == ["10.0.0.1", "10.0.0.2"]


def test_each_instance_becomes_its_own_row(client: Any) -> None:
    _state(client)
    inventory = state_inventory(client, "ws-1", include_attributes=True)
    assert [r.address for r in inventory.resources] == [
        "aws_instance.web[0]",
        "aws_instance.web[1]",
    ]


def test_attributes_are_redacted_by_default(client: Any) -> None:
    _state(client)
    inventory = state_inventory(client, "ws-1", include_attributes=True)
    first = inventory.resources[0]
    assert first.attributes is not None
    assert "password" not in first.attributes
    assert first.attributes["public_ip"] == "10.0.0.1"
    assert inventory.redacted_paths == ["aws_instance.web.password"]


def test_attributes_are_omitted_from_summary(client: Any) -> None:
    _state(client)
    inventory = state_inventory(client, "ws-1", include_attributes=True)
    assert "resources" not in inventory.summary()
    assert "10.0.0.1" not in json.dumps(inventory.summary())


def test_provider_source_address_is_parsed(client: Any) -> None:
    _state(client)
    inventory = state_inventory(client, "ws-1", include_attributes=True)
    assert inventory.by_provider == {"registry.terraform.io/hashicorp/aws": 2}


def test_include_attributes_bypasses_the_cheap_endpoint(client: Any) -> None:
    """workspace_resources carries no attributes, so it cannot serve this."""
    _state(client)
    state_inventory(client, "ws-1", include_attributes=True)
    client.workspace_resources.list.assert_not_called()


# --------------------------------------------------------------------------
# queue_run
# --------------------------------------------------------------------------


def test_queue_run_needs_no_local_directory(client: Any, clock: Any) -> None:
    """The VCS-driven case: run the workspace's existing configuration."""
    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.runs.create.return_value = make_run("pending")
    client.runs.read.return_value = make_run("planned_and_finished")
    client.plans.read_json_output_for_run.return_value = {"resource_changes": []}
    client.policy_checks.list.return_value = iter([])

    result = queue_run(
        client,
        workspace_id="ws-1",
        plan_only=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    assert result.phase == "no_changes"
    client.configuration_versions.create.assert_not_called()
    options = client.runs.create.call_args.args[0]
    assert options.configuration_version is None


def test_queue_run_supports_refresh_only(client: Any, clock: Any) -> None:
    """Drift detection: refresh state without proposing changes."""
    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    client.runs.create.return_value = make_run("pending")
    client.runs.read.return_value = make_run("planned")
    client.plans.read_json_output_for_run.return_value = {"resource_changes": []}
    client.policy_checks.list.return_value = iter([])

    result = queue_run(
        client,
        workspace_id="ws-1",
        refresh_only=True,
        _sleep=clock.sleep,
        _clock=clock.time,
    )
    assert client.runs.create.call_args.args[0].refresh_only is True
    assert result.phase == "planned"
    client.runs.apply.assert_not_called()


def test_queue_run_refuses_destroy_without_permission(client: Any) -> None:
    client.workspaces.read_by_id.return_value = Workspace.model_validate(
        {"id": "ws-1", "name": "web"}
    )
    result = queue_run(client, workspace_id="ws-1", is_destroy=True)
    assert result.phase == "refused_destructive"
    client.runs.create.assert_not_called()
