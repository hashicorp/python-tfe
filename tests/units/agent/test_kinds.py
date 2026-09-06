# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Method classification, checked against every real method on the client."""

from __future__ import annotations

import inspect

import pytest

from pytfe import TFEClient, TFEConfig
from pytfe.agent import OVERRIDES, PREFIXES, Kind, classify
from tests.contract.surface import _namespaces


def all_methods() -> list[tuple[str, str]]:
    client = TFEClient(TFEConfig(address="", token=""))
    try:
        found: set[tuple[str, str]] = set()
        for resource, service in _namespaces(client).items():
            for name, _ in inspect.getmembers(service, callable):
                if name.startswith("_") or not hasattr(type(service), name):
                    continue
                found.add((resource, name))
        return sorted(found)
    finally:
        client.close()


ALL_METHODS = all_methods()


def _prefix_matches(method: str) -> bool:
    return any(
        method.startswith(prefix)
        for prefixes in PREFIXES.values()
        for prefix in prefixes
    )


def test_the_walk_finds_the_whole_surface() -> None:
    assert len(ALL_METHODS) > 400
    # The shared transport hangs off every service as `.t`; it is not a
    # namespace and must not appear as `<resource>.t.request`.
    assert not [pair for pair in ALL_METHODS if pair[0].endswith(".t")]


def test_nothing_falls_through_to_the_default() -> None:
    """A new SDK method must fail here, not silently default to WRITE.

    The default exists as a fail-safe, not as a routine outcome: an
    unclassified destructive method would be waved through a Kind-based gate.
    """
    unclassified = [
        f"{resource}.{method}"
        for resource, method in ALL_METHODS
        if (resource, method) not in OVERRIDES and not _prefix_matches(method)
    ]
    assert not unclassified, (
        "these methods match no verb prefix and have no override, so they "
        "silently default to WRITE: " + ", ".join(unclassified)
    )


def test_every_method_classifies_to_a_real_kind() -> None:
    for resource, method in ALL_METHODS:
        assert isinstance(classify(resource, method), Kind)


@pytest.mark.parametrize(
    ("resource", "method", "expected"),
    [
        # The single most consequential call in the SDK, behind a write-shaped verb.
        ("runs", "apply", Kind.DESTRUCTIVE),
        ("runs", "force_cancel", Kind.DESTRUCTIVE),
        ("runs", "discard", Kind.DESTRUCTIVE),
        ("policy_checks", "override", Kind.DESTRUCTIVE),
        ("workspaces", "delete", Kind.DESTRUCTIVE),
        ("workspaces", "safe_delete", Kind.DESTRUCTIVE),
        ("state_versions", "create", Kind.DESTRUCTIVE),
        # Approving is what triggers the apply.
        ("stack_deployment_groups", "approve_all_plans", Kind.DESTRUCTIVE),
        ("no_code_modules", "confirm_workspace_upgrade", Kind.DESTRUCTIVE),
        # Longest-prefix wins: apply_to_* is scope management, not an apply.
        ("variable_sets", "apply_to_workspaces", Kind.WRITE),
        # An override beats the force_ prefix; forcing a lock destroys nothing.
        ("workspaces", "force_unlock", Kind.WRITE),
        ("workspaces", "remove_tags", Kind.WRITE),
        ("workspaces", "add_tags", Kind.WRITE),
        ("team_workspace_accesses", "add", Kind.WRITE),
        # Reads
        ("workspaces", "list", Kind.READ),
        ("workspaces", "read_by_id", Kind.READ),
        ("plans", "logs", Kind.READ),
        ("plans", "read_json_output_for_run", Kind.READ),
        ("applies", "errored_state", Kind.READ),
        ("explorer", "query", Kind.READ),
        ("registry", "latest_for_provider", Kind.READ),
        # Pure local helpers: a read-only gate must not block these.
        ("organizations", "validate", Kind.LOCAL),
        ("policy_set_outcomes", "build_query_string", Kind.LOCAL),
    ],
)
def test_known_classifications(resource: str, method: str, expected: Kind) -> None:
    assert classify(resource, method) is expected


def test_unknown_verb_defaults_to_write_not_read() -> None:
    """Guessing 'safe' for something that mutates is the failure that matters."""
    assert classify("widgets", "frobnicate") is Kind.WRITE


def test_admin_privileged_calls_are_gated() -> None:
    """These are exactly the calls a Kind gate exists to catch."""
    assert classify("admin.users", "suspend") is Kind.DESTRUCTIVE
    assert classify("admin.users", "revoke_admin") is Kind.DESTRUCTIVE
    assert classify("admin.runs", "force_cancel") is Kind.DESTRUCTIVE
    assert classify("admin.users", "unsuspend") is Kind.WRITE


def test_every_destructive_method_is_reachable_for_review() -> None:
    """Print-worthy inventory: the calls a harness must gate."""
    destructive = [
        f"{r}.{m}" for r, m in ALL_METHODS if classify(r, m) is Kind.DESTRUCTIVE
    ]
    assert len(destructive) > 50
    assert "runs.apply" in destructive
