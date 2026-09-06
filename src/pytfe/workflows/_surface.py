# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""The exact public SDK surface the workflow layer depends on.

Core may be regenerated from an OpenAPI spec. When that happens, a renamed
method or a dropped parameter must fail loudly here rather than at runtime in a
user's pipeline, so every ``(resource, method)`` pair the workflows call is
declared below and checked against a committed snapshot by
``tests/contract/test_public_surface.py``.

Add a pair here whenever a workflow starts calling a new method, then run
``make surface-snapshot`` to re-record the signatures.
"""

from __future__ import annotations

__all__ = ["REQUIRED"]

#: Every ``(resource, method)`` reached from ``pytfe.workflows``.
REQUIRED: frozenset[tuple[str, str]] = frozenset(
    {
        ("applies", "errored_state"),
        ("applies", "logs"),
        ("applies", "read"),
        ("comments", "create"),
        ("configuration_versions", "create"),
        ("configuration_versions", "read"),
        ("configuration_versions", "upload_tar_gzip"),
        ("cost_estimates", "read"),
        ("plans", "logs"),
        ("plans", "read"),
        ("plans", "read_for_run"),
        ("plans", "read_json_output"),
        ("plans", "read_json_output_for_run"),
        ("policy_checks", "list"),
        ("runs", "apply"),
        ("runs", "create"),
        ("runs", "discard"),
        ("runs", "list"),
        ("runs", "read"),
        ("state_version_outputs", "read_current"),
        ("state_versions", "read_current"),
        ("variables", "create"),
        ("variables", "delete"),
        ("variables", "list"),
        ("variables", "update"),
        ("workspaces", "add_tags"),
        ("workspaces", "create"),
        ("workspaces", "list"),
        ("workspaces", "read"),
        ("workspaces", "read_by_id"),
        ("workspaces", "remove_tags"),
        ("workspaces", "update_by_id"),
    }
)
