# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Attribute-level analysis of a Terraform plan document.

``plan_summary`` answers "how many things change". This answers "*which
attribute* of which resource changes", which is the question a drift review or
an approval gate actually turns on.

One rule governs the whole module: **paths are returned, values never are.** A
plan's ``before``/``after`` blocks contain real infrastructure data - connection
strings, generated passwords, private keys - and a plan document routinely
exceeds 20MB. Returning ``aws_db_instance.main.password`` is actionable;
returning its value is a leak, and returning the whole document is unusable in
an agent's context window.

Terraform marks three things separately in ``resource_changes[].change`` and
they are deliberately kept disjoint here:

* ``before`` vs ``after`` - attributes whose value genuinely changes;
* ``after_unknown`` - attributes computed during apply, which look like changes
  but are not decisions anyone made;
* ``before_sensitive`` / ``after_sensitive`` - attributes whose values must not
  be displayed, which is orthogonal to whether they changed.
"""

from __future__ import annotations

from typing import Any

__all__ = ["changed_paths", "unknown_paths", "sensitive_paths"]

#: Cap on paths collected per resource, so one wide resource cannot dominate.
_MAX_PATHS = 100


def _join(prefix: str, key: Any) -> str:
    if isinstance(key, int):
        return f"{prefix}[{key}]"
    return f"{prefix}.{key}" if prefix else str(key)


def _walk_marks(node: Any, prefix: str, out: list[str]) -> None:
    """Collect paths from Terraform's mark structures.

    ``after_unknown`` and ``*_sensitive`` share a shape: ``true`` marks the
    whole subtree, a dict recurses by key, a list recurses by index.
    """
    if len(out) >= _MAX_PATHS:
        return
    if node is True:
        if prefix:
            out.append(prefix)
        return
    if isinstance(node, dict):
        for key, child in node.items():
            _walk_marks(child, _join(prefix, key), out)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _walk_marks(child, _join(prefix, index), out)


def _walk_diff(before: Any, after: Any, prefix: str, out: list[str]) -> None:
    """Collect paths where ``before`` and ``after`` differ."""
    if len(out) >= _MAX_PATHS:
        return
    if before == after:
        return

    if isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(set(before) | set(after)):
            _walk_diff(before.get(key), after.get(key), _join(prefix, key), out)
        return

    if isinstance(before, list) and isinstance(after, list):
        if len(before) == len(after):
            for index, (b, a) in enumerate(zip(before, after, strict=False)):
                _walk_diff(b, a, _join(prefix, index), out)
            return
        # A length change is a change to the collection itself; reporting every
        # shifted index would be noise.
        if prefix:
            out.append(prefix)
        return

    if prefix:
        out.append(prefix)


def changed_paths(change: dict[str, Any]) -> list[str]:
    """Attribute paths whose value differs between ``before`` and ``after``.

    Paths that are merely unknown-after-apply are excluded: they are computed by
    the provider, not chosen by anyone, and including them makes every plan look
    like it rewrites the world.

    Args:
        change: One ``resource_changes[].change`` block.

    Returns:
        Sorted attribute paths, capped at 100.

    Example:
        >>> changed_paths({"before": {"size": 1}, "after": {"size": 2}})
        ['size']
    """
    before = change.get("before")
    after = change.get("after")
    if before is None and after is None:
        return []

    out: list[str] = []
    _walk_diff(before, after, "", out)
    computed = set(unknown_paths(change))
    return sorted(p for p in out if p not in computed)


def unknown_paths(change: dict[str, Any]) -> list[str]:
    """Attribute paths the provider will compute during apply.

    Args:
        change: One ``resource_changes[].change`` block.

    Returns:
        Sorted attribute paths, capped at 100.

    Example:
        >>> unknown_paths({"after_unknown": {"arn": True}})
        ['arn']
    """
    out: list[str] = []
    _walk_marks(change.get("after_unknown"), "", out)
    return sorted(set(out))


def sensitive_paths(change: dict[str, Any]) -> list[str]:
    """Attribute paths Terraform flagged sensitive, on either side of the change.

    Reported so a reviewer knows a secret is involved. The values themselves are
    never read.

    Args:
        change: One ``resource_changes[].change`` block.

    Returns:
        Sorted attribute paths, capped at 100.

    Example:
        >>> sensitive_paths({"after_sensitive": {"password": True}})
        ['password']
    """
    out: list[str] = []
    _walk_marks(change.get("before_sensitive"), "", out)
    _walk_marks(change.get("after_sensitive"), "", out)
    return sorted(set(out))
