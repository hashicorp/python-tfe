# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Derive the live public surface of a TFEClient, offline.

Shared by ``test_public_surface.py`` and ``make surface-snapshot``.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterable
from typing import Any

from pytfe import TFEClient, TFEConfig
from pytfe._http import HTTPTransport


def _namespaces(client: TFEClient) -> dict[str, Any]:
    """Public resource namespaces on a client, including nested ones."""
    out: dict[str, Any] = {}
    for name, value in vars(client).items():
        if name.startswith("_") or name == "config":
            continue
        if type(value).__module__.split(".")[0] != "pytfe":
            continue
        out[name] = value
        # Grouping namespaces such as `admin` hold their own sub-services;
        # describe() nests these, and a flat walk would drop all of them.
        for sub_name, sub in vars(value).items():
            if sub_name.startswith("_"):
                continue
            # Every service holds the shared transport as `.t`; it is not a
            # resource namespace, and including it would surface
            # `<resource>.t.request` for all 81 of them.
            if isinstance(sub, HTTPTransport):
                continue
            if type(sub).__module__.split(".")[0] == "pytfe":
                out[f"{name}.{sub_name}"] = sub
    return out


def current_surface(
    required: Iterable[tuple[str, str]] | None = None,
) -> dict[str, dict[str, list[str]]]:
    """Map ``{resource: {method: [parameter names]}}`` for the live client.

    Args:
        required: Restrict the walk to these ``(resource, method)`` pairs.
            ``None`` records everything.

    Returns:
        Parameter names per method, with ``self`` removed.
    """
    wanted: dict[str, set[str]] | None = None
    if required is not None:
        wanted = {}
        for resource, method in required:
            wanted.setdefault(resource, set()).add(method)

    client = TFEClient(TFEConfig(address="", token=""))
    try:
        out: dict[str, dict[str, list[str]]] = {}
        for resource, service in _namespaces(client).items():
            if wanted is not None and resource not in wanted:
                continue
            methods: dict[str, list[str]] = {}
            for name, member in inspect.getmembers(service, callable):
                if name.startswith("_"):
                    continue
                if wanted is not None and name not in wanted[resource]:
                    continue
                if not hasattr(type(service), name):
                    continue
                try:
                    signature = inspect.signature(member)
                except (TypeError, ValueError):  # pragma: no cover - defensive
                    continue
                methods[name] = [p for p in signature.parameters if p != "self"]
            if methods:
                out[resource] = dict(sorted(methods.items()))
        return dict(sorted(out.items()))
    finally:
        client.close()
