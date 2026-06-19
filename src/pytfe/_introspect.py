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

import collections.abc as cabc
import enum
import inspect
import types
import typing
from collections.abc import Iterable, Iterator
from importlib.resources import files
from typing import Any

from pydantic import BaseModel

from ._http import HTTPTransport

__all__ = ["describe", "llms_txt", "tool_schemas"]


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


_PRIMITIVE_SCHEMAS: dict[type, str] = {
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
}


def _is_optional(tp: Any) -> bool:
    """True if the annotation is ``X | None`` / ``Optional[X]``."""
    union_types = (typing.Union, getattr(types, "UnionType", None))
    if typing.get_origin(tp) in union_types:
        return type(None) in typing.get_args(tp)
    return False


def _py_type_to_schema(tp: Any) -> dict[str, Any]:
    """Best-effort JSON Schema for a Python type annotation.

    Pydantic ``*Options`` models are embedded via ``model_json_schema()``; common
    containers, enums, unions, and primitives are mapped; anything unrecognised
    becomes an unconstrained ``{}`` (valid JSON Schema for "any").
    """
    if tp is Any or tp is None or tp is type(None):
        return {}

    origin = typing.get_origin(tp)
    args = typing.get_args(tp)

    union_types = (typing.Union, getattr(types, "UnionType", None))
    if origin in union_types:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _py_type_to_schema(non_none[0])
        return {"anyOf": [_py_type_to_schema(a) for a in non_none]}

    if origin in (list, tuple, set, frozenset) or (
        isinstance(origin, type)
        and issubclass(origin, cabc.Sequence)
        and origin not in (str, bytes)
    ):
        item = args[0] if args else Any
        return {"type": "array", "items": _py_type_to_schema(item)}

    if origin is dict or (
        isinstance(origin, type) and issubclass(origin, cabc.Mapping)
    ):
        return {"type": "object"}

    if isinstance(tp, type):
        if issubclass(tp, BaseModel):
            return tp.model_json_schema()
        if issubclass(tp, enum.Enum):
            return {"type": "string", "enum": [e.value for e in tp]}
        if tp in _PRIMITIVE_SCHEMAS:
            return {"type": _PRIMITIVE_SCHEMAS[tp]}

    return {}


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Dereference all ``$ref``/``$defs`` into a self-contained schema.

    LLM tool-calling layers behind many MCP clients reject ``$ref``/``$defs``
    outright, so we inline them. Recursive models are broken with a permissive
    ``{"type": "object"}`` placeholder to avoid infinite expansion.
    """
    defs: dict[str, Any] = schema.get("$defs", {})

    def resolve(node: Any, seen: frozenset[str]) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                name = ref[len("#/$defs/") :]
                if name in seen:
                    return {"type": "object"}
                target = defs.get(name)
                if not isinstance(target, dict):
                    return {}
                return resolve(target, seen | {name})
            return {k: resolve(v, seen) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [resolve(item, seen) for item in node]
        return node

    result: dict[str, Any] = resolve(schema, frozenset())
    return result


def _method_input_schema(method: Any) -> dict[str, Any]:
    """Build a self-contained JSON Schema describing a method's call arguments.

    Embedded Pydantic ``*Options`` models are inlined (no ``$ref``/``$defs``) for
    maximum MCP-client compatibility.
    """
    func = getattr(method, "__func__", method)
    try:
        hints = typing.get_type_hints(func)
    except Exception:
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []
    defs: dict[str, Any] = {}
    for pname, param in inspect.signature(method).parameters.items():
        if pname == "self" or param.kind in (
            param.VAR_POSITIONAL,
            param.VAR_KEYWORD,
        ):
            continue
        tp = hints.get(pname, Any)
        prop = _py_type_to_schema(tp)
        if isinstance(prop, dict) and "$defs" in prop:
            prop = dict(prop)
            defs.update(prop.pop("$defs"))
        properties[pname] = prop
        has_default = param.default is not inspect.Parameter.empty
        if not has_default and not _is_optional(tp):
            required.append(pname)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    schema["additionalProperties"] = False
    if defs:
        schema["$defs"] = defs
    return _inline_refs(schema)


def _iter_methods(obj: Any, prefix: str) -> Iterator[tuple[str, str, Any]]:
    """Yield ``(dotted_name, method_name, bound_method)`` for a resource tree."""
    cls = type(obj)
    for name, member in inspect.getmembers(obj, callable):
        if name.startswith("_") or not hasattr(cls, name):
            continue
        yield (f"{prefix}.{name}", name, member)
    for sub_name, sub in sorted(vars(obj).items()):
        if sub_name.startswith("_") or not _service_like(sub):
            continue
        yield from _iter_methods(sub, f"{prefix}.{sub_name}")


def tool_schemas(*, resources: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Return MCP-style tool definitions for every resource method.

    Each entry is ``{"name", "resource", "method", "description", "input_schema"}``
    where ``input_schema`` is a JSON Schema object composed of the method's
    positional identifiers plus its Pydantic ``*Options`` model (embedded via
    ``model_json_schema()``). Nested namespaces use dotted names, e.g.
    ``"admin.saml_settings.read"``.

    No network calls are made and the result is JSON-serializable, so it can back
    an MCP server (``Tool(name, description, inputSchema)``) or any LLM tool
    framework. Because the schemas come from the *installed* package, a newly
    added or updated resource appears automatically — no hand-maintained list.

    Security: the output describes the *entire* SDK surface, including
    destructive methods (``delete``, ``force_cancel``), endpoints that upload a
    local path to an arbitrary URL (``configuration_versions.upload``), and
    options that carry secrets (tokens, passwords, SAML/OAuth keys).
    ``tool_schemas()`` only describes the surface and never makes a call, but a
    consumer that *executes* these calls from model output should not expose
    them unrestricted: default to read-only methods, gate mutations behind an
    allowlist or human confirmation, constrain upload hosts/paths, and keep
    secret-bearing arguments out of logs and transcripts.

    Pass ``resources={"workspaces", "runs"}`` to limit output to specific
    top-level namespaces.
    """
    from .client import TFEClient
    from .config import TFEConfig

    wanted = set(resources) if resources is not None else None
    client = TFEClient(TFEConfig(address="", token=""))
    try:
        out: list[dict[str, Any]] = []
        for name, obj in sorted(vars(client).items()):
            if name.startswith("_") or not _service_like(obj):
                continue
            if wanted is not None and name not in wanted:
                continue
            for dotted, method_name, member in _iter_methods(obj, name):
                out.append(
                    {
                        "name": dotted,
                        "resource": name,
                        "method": method_name,
                        "description": _summary(member) or "",
                        "input_schema": _method_input_schema(member),
                    }
                )
        return out
    finally:
        client.close()


def llms_txt() -> str:
    """Return the packaged ``llms.txt`` orientation guide as text.

    The guide ships inside the wheel (``site-packages/pytfe/llms.txt``) so AI
    tooling can read a concise description of the SDK from the installed package.
    """
    return (files("pytfe") / "llms.txt").read_text(encoding="utf-8")
