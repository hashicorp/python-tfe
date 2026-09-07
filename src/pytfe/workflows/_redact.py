# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Strip Terraform-flagged sensitive values out of a state document.

Terraform records, per resource instance, a ``sensitive_attributes`` list of
paths whose values must not be shown. Each path is a list of traversal steps
shaped like ``{"type": "get_attr", "value": "<name>"}`` or
``{"type": "index", "value": <int|str>}``. State-level outputs carry a simpler
``sensitive: true`` flag.

Sensitive values are **removed**, not masked: a masked placeholder still has to
be carried around and re-redacted at every boundary, whereas a removed value
cannot leak. What was removed is reported separately, so a caller can tell the
difference between "this resource has no password" and "the password was
stripped".

The traversal rules here follow the implementation in the ``hashicorp.terraform``
Ansible collection (``plugins/module_utils/inventory/sources/statefile.py``),
which had to solve the same problem before it could write state to an on-disk
cache. Two behaviours are deliberately kept from it, and one is added:

* an unwalkable or ambiguous path falls back to dropping the first top-level
  attribute it names, rather than silently leaving the value in place;
* a sensitive *list index* drops the whole owning attribute, because deleting
  one element shifts the indices that later sensitive paths refer to;
* **added here:** state-level sensitive outputs are redacted too. The
  collection's version walks ``resources`` only, so a sensitive root output
  keeps its value.
"""

from __future__ import annotations

import copy
from typing import Any

__all__ = ["redact_state", "redact_attributes"]


def _first_top_level_attribute(path: list[Any]) -> str | None:
    """Return the first ``get_attr`` name in ``path``, or None if malformed.

    Terraform always begins a sensitive path with a ``get_attr`` step naming a
    top-level attribute; anything else is treated as malformed.
    """
    if not path:
        return None
    first = path[0]
    if not isinstance(first, dict) or first.get("type") != "get_attr":
        return None
    value = first.get("value")
    return value if isinstance(value, str) else None


def _step_into(parent: Any, step: Any) -> Any:
    """Follow one traversal step into ``parent``; None when impossible."""
    if not isinstance(step, dict):
        return None
    step_type = step.get("type")
    value = step.get("value")
    if step_type == "get_attr":
        if isinstance(value, str) and isinstance(parent, dict) and value in parent:
            return parent[value]
        return None
    if step_type == "index":
        if (
            isinstance(parent, list)
            and isinstance(value, int)
            and 0 <= value < len(parent)
        ):
            return parent[value]
        if (
            isinstance(parent, dict)
            and isinstance(value, (str, int))
            and value in parent
        ):
            return parent[value]
    return None


def _path_label(path: list[Any]) -> str:
    """Render a sensitive path for reporting, e.g. ``config.credentials[0]``."""
    parts: list[str] = []
    for step in path:
        if not isinstance(step, dict):
            continue
        value = step.get("value")
        if step.get("type") == "get_attr":
            parts.append(f".{value}" if parts else str(value))
        elif step.get("type") == "index":
            parts.append(f"[{value!r}]" if isinstance(value, str) else f"[{value}]")
    return "".join(parts) or "<unknown>"


def _drop_sensitive_path(attributes: dict[str, Any], path: list[Any]) -> bool:
    """Remove one sensitive path from ``attributes`` in place.

    Returns True when something was removed.
    """
    top_level = _first_top_level_attribute(path)

    def drop_top_level() -> bool:
        if top_level is not None and top_level in attributes:
            del attributes[top_level]
            return True
        return False

    if len(path) == 1:
        return drop_top_level()

    parent: Any = attributes
    for step in path[:-1]:
        parent = _step_into(parent, step)
        if parent is None:
            return drop_top_level()

    last = path[-1]
    if not isinstance(last, dict):
        return drop_top_level()

    last_type = last.get("type")
    last_value = last.get("value")

    if (
        last_type == "get_attr"
        and isinstance(last_value, str)
        and isinstance(parent, dict)
        and last_value in parent
    ):
        del parent[last_value]
        return True
    if last_type == "index":
        if (
            isinstance(parent, list)
            and isinstance(last_value, int)
            and 0 <= last_value < len(parent)
        ):
            # Deleting one list element shifts the indices that later sensitive
            # paths refer to, which would strand a second secret. Drop the whole
            # owning attribute instead.
            return drop_top_level()
        if (
            isinstance(parent, dict)
            and isinstance(last_value, (str, int))
            and last_value in parent
        ):
            del parent[last_value]
            return True

    return drop_top_level()


def redact_attributes(
    attributes: dict[str, Any], sensitive_paths: list[Any]
) -> tuple[dict[str, Any], list[str]]:
    """Return a copy of ``attributes`` with Terraform-flagged paths removed.

    Args:
        attributes: One resource instance's ``attributes`` block.
        sensitive_paths: The instance's ``sensitive_attributes`` list.

    Returns:
        ``(redacted_attributes, removed_labels)``.

    Example:
        >>> attrs, removed = redact_attributes(
        ...     {"user": "admin", "password": "hunter2"},
        ...     [[{"type": "get_attr", "value": "password"}]],
        ... )
        >>> attrs
        {'user': 'admin'}
    """
    if not isinstance(attributes, dict) or not sensitive_paths:
        return attributes, []

    sanitized = copy.deepcopy(attributes)
    removed: list[str] = []
    for path in sensitive_paths:
        if not isinstance(path, list) or not path:
            continue
        if _drop_sensitive_path(sanitized, path):
            removed.append(_path_label(path))
    return sanitized, removed


def redact_state(state: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a copy of a Terraform state document with sensitive values removed.

    Handles both halves of the document: every resource instance's
    ``sensitive_attributes`` paths, and any root output flagged
    ``sensitive: true``. The ``sensitive_attributes`` markers are dropped
    afterwards, since the values they point at are gone.

    Args:
        state: A parsed Terraform state document.

    Returns:
        ``(redacted_state, removed_paths)`` where each removed path is labelled
        ``<resource address>.<attribute path>`` or ``output.<name>``.

    Example:
        >>> clean, removed = redact_state(raw_state)
        >>> removed
        ['aws_db_instance.main.password', 'output.connection_string']
    """
    cleaned = copy.deepcopy(state)
    removed: list[str] = []

    for resource in cleaned.get("resources") or []:
        if not isinstance(resource, dict):
            continue
        module = resource.get("module")
        prefix = f"{module}." if module else ""
        address = f"{prefix}{resource.get('type')}.{resource.get('name')}"
        for instance in resource.get("instances") or []:
            if not isinstance(instance, dict):
                continue
            attributes = instance.get("attributes") or {}
            paths = instance.get("sensitive_attributes") or []
            instance["attributes"], dropped = redact_attributes(attributes, paths)
            removed.extend(f"{address}.{label}" for label in dropped)
            # The marker is meaningless once the values are gone, and keeping it
            # would make a second redaction pass look like it found new secrets.
            instance.pop("sensitive_attributes", None)

    outputs = cleaned.get("outputs")
    if isinstance(outputs, dict):
        for name, output in outputs.items():
            if (
                isinstance(output, dict)
                and output.get("sensitive")
                and "value" in output
            ):
                del output["value"]
                removed.append(f"output.{name}")

    return cleaned, removed
