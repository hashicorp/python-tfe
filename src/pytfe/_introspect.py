# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Discovery helpers for AI agents, MCP servers, and tooling.

These functions let a consumer enumerate the SDK's surface from the *installed*
package alone — no network access and no hardcoded resource names:

* :func:`describe` introspects every resource namespace on
  :class:`pytfe.TFEClient` and returns a machine-readable manifest of methods,
  signatures, and one-line summaries. The Pydantic ``*Options`` models referenced
  in those signatures expose JSON Schema via ``model_json_schema()``, which is
  exactly what an MCP tool definition needs.
* :func:`llms_txt` returns the packaged ``llms.txt`` orientation guide.
"""

from __future__ import annotations

import inspect
from importlib.resources import files
from typing import Any

from pydantic import BaseModel

from ._http import HTTPTransport

__all__ = ["describe", "llms_txt"]


def _summary(obj: Any) -> str | None:
    """Return the first line of an object's docstring, if any."""
    doc = inspect.getdoc(obj)
    if not doc:
        return None
    return doc.strip().splitlines()[0]


def _service_like(value: Any) -> bool:
    """True for pytfe resource services / namespaces worth introspecting.

    Excludes the HTTP transport, Pydantic models, and non-pytfe values (e.g. the
    plain ``base_url`` string the registry service holds) so they never get
    mistaken for a resource namespace.
    """
    if isinstance(value, (HTTPTransport, BaseModel)):
        return False
    return type(value).__module__.split(".")[0] == "pytfe"


def _methods(obj: Any) -> dict[str, dict[str, Any]]:
    """Map public method name -> {signature, summary} for a resource object."""
    out: dict[str, dict[str, Any]] = {}
    cls = type(obj)
    for name, member in inspect.getmembers(obj, callable):
        if name.startswith("_") or not hasattr(cls, name):
            continue
        try:
            signature = str(inspect.signature(member))
        except (TypeError, ValueError):
            signature = "(...)"
        out[name] = {"signature": signature, "summary": _summary(member)}
    return out


def _describe_obj(obj: Any) -> dict[str, Any]:
    """Describe one resource service, recursing into grouping namespaces."""
    entry: dict[str, Any] = {"class": type(obj).__name__}
    summary = _summary(obj)
    if summary:
        entry["summary"] = summary

    methods = _methods(obj)
    if methods:
        entry["methods"] = methods

    namespaces: dict[str, Any] = {}
    for sub_name, sub in sorted(vars(obj).items()):
        if sub_name.startswith("_") or not _service_like(sub):
            continue
        namespaces[sub_name] = _describe_obj(sub)
    if namespaces:
        entry["namespaces"] = namespaces

    return entry


def describe() -> dict[str, Any]:
    """Return a machine-readable manifest of the SDK's API surface.

    Introspects every resource namespace on :class:`pytfe.TFEClient` and its
    public methods (name, signature, one-line summary), recursing into grouping
    namespaces such as ``admin``. No network calls are made; a throwaway client
    is constructed with an empty config purely to enumerate the wiring.

    The shape is::

        {
          "sdk": "pytfe",
          "version": "1.2.0",
          "client": "pytfe.TFEClient",
          "resource_count": 70,
          "resources": {
            "workspaces": {
              "class": "Workspaces",
              "summary": "...",
              "methods": {"list": {"signature": "(...)", "summary": "..."}, ...},
            },
            "admin": {"class": "AdminClient", "namespaces": {...}},
            ...
          },
        }

    Intended for AI agents and MCP servers that need to enumerate the SDK
    without hardcoding resource names. Combine each method's ``*Options`` model
    with ``model_json_schema()`` to build typed tool definitions.
    """
    from . import __version__
    from .client import TFEClient
    from .config import TFEConfig

    client = TFEClient(TFEConfig(address="", token=""))
    try:
        resources: dict[str, Any] = {}
        for name, obj in sorted(vars(client).items()):
            if name.startswith("_") or not _service_like(obj):
                continue
            resources[name] = _describe_obj(obj)
        return {
            "sdk": "pytfe",
            "version": __version__,
            "client": "pytfe.TFEClient",
            "resource_count": len(resources),
            "resources": resources,
        }
    finally:
        client.close()


def llms_txt() -> str:
    """Return the packaged ``llms.txt`` orientation guide as text.

    The guide ships inside the wheel (``site-packages/pytfe/llms.txt``) so AI
    tooling can read a concise description of the SDK from the installed package.
    """
    return (files("pytfe") / "llms.txt").read_text(encoding="utf-8")
