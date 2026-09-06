# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Pin the SDK methods the workflow layer calls.

``pytfe.describe()`` is not usable for this: it records each signature as a
*string*, and at least one of them is not even re-parseable
(``stack_configurations.create`` embeds a repr of an enum member). This walks
the live client with ``inspect.signature`` instead, which yields real parameter
names, and recurses into grouping namespaces such as ``admin``.

Regenerate the snapshot deliberately with ``make surface-snapshot`` when a
signature change is intended.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytfe.workflows._surface import REQUIRED
from tests.contract.surface import current_surface

SNAPSHOT = Path(__file__).with_name("public_surface.json")


def test_snapshot_exists() -> None:
    assert SNAPSHOT.is_file(), (
        "public_surface.json is missing; run `make surface-snapshot`"
    )


def test_every_required_method_exists() -> None:
    surface = current_surface(REQUIRED)
    missing = sorted(
        f"{resource}.{method}"
        for resource, method in REQUIRED
        if method not in surface.get(resource, {})
    )
    assert not missing, (
        "the workflow layer calls SDK methods that no longer exist: "
        + ", ".join(missing)
    )


def test_signatures_match_snapshot() -> None:
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    actual = current_surface(REQUIRED)

    problems: list[str] = []
    for resource, methods in expected.items():
        for method, params in methods.items():
            live = actual.get(resource, {}).get(method)
            if live is None:
                problems.append(f"{resource}.{method}: method disappeared")
                continue
            removed = [p for p in params if p not in live]
            if removed:
                problems.append(
                    f"{resource}.{method}: parameter(s) removed or renamed: "
                    f"{', '.join(removed)}"
                )
    if problems:
        pytest.fail(
            "The public surface the workflow layer depends on changed:\n  "
            + "\n  ".join(problems)
            + "\n\nIf this is intended, run `make surface-snapshot` and commit."
        )
