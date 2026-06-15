# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any


def build_headers(user_agent_suffix: str | None = None) -> dict[str, str]:
    ua = "pytfe/1.0"
    if user_agent_suffix:
        ua = f"{ua} {user_agent_suffix}"
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "User-Agent": ua,
    }


def parse_error_payload(payload: dict[str, Any]) -> list[dict | str]:
    errs = payload.get("errors")
    if isinstance(errs, list):
        return errs
    if "message" in payload:
        return [{"detail": payload.get("message")}]
    return []


# --------------------------------------------------------------------------- #
# Relationship / included parsing
#
# HCP Terraform speaks JSON:API: a resource object carries an ``attributes`` map
# and a ``relationships`` map, and a response may carry a top-level ``included``
# array holding the full bodies of related resources requested via ``?include=``.
#
# These helpers are the single canonical implementation that resource parsers
# converge on, replacing the per-resource hand-rolled relationship parsing
# (``workspaces._ws_from`` if-ladder, ``run.transform_relationships``,
# ``no_code_module`` included-index).
# --------------------------------------------------------------------------- #

IncludedIndex = dict[tuple[Any, Any], dict[str, Any]]

# A relation map value is either the model class (attr name derived from the
# wire relation name by ``-`` -> ``_``) or an explicit ``(python_attr, Model)``
# tuple for the cases where they diverge (e.g. ``vars`` -> ``variables``).
RelationSpec = "type | tuple[str, type]"
RelationMap = dict[str, Any]


def build_included_index(included: list[dict[str, Any]] | None) -> IncludedIndex:
    """Index a JSON:API ``included`` array by ``(type, id)``.

    JSON:API guarantees ``(type, id)`` uniqueness within a document, so the
    first occurrence wins deterministically if a server ever violates that.
    """
    index: IncludedIndex = {}
    for item in included or []:
        index.setdefault((item.get("type"), item.get("id")), item)
    return index


def _hydrate(ref: dict[str, Any], model: Any, index: IncludedIndex) -> Any | None:
    """Resolve a single relationship reference to a model instance.

    If the full resource body is present in ``index`` (because it was requested
    via ``?include=``), validate it into a fully-populated model. Otherwise
    return a lightweight ``{id}`` stub via ``model_construct`` (no validation —
    correct, because only ``id``/``type`` are known).
    """
    rid = ref.get("id")
    if rid is None:
        return None
    full = index.get((ref.get("type"), rid))
    if full is not None:
        attrs = dict(full.get("attributes") or {})
        attrs["id"] = rid
        try:
            return model.model_validate(attrs)
        except Exception:
            # A hydration failure must never break parsing of the parent.
            return model.model_construct(id=rid)
    return model.model_construct(id=rid)


def parse_relationships(
    relationships: dict[str, Any] | None,
    rel_map: RelationMap,
    *,
    included: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Parse a JSON:API ``relationships`` block into ``{python_attr: value}``.

    ``rel_map`` maps each wire relationship name to either a model class (the
    python attribute is derived as ``wire.replace("-", "_")``) or an explicit
    ``(python_attr, Model)`` tuple. Single references become a model instance;
    lists become a list of model instances. Null/empty relationships and
    relations absent from ``rel_map`` are skipped, so they never clobber model
    defaults (undeclared relations are caught by ``extra="allow"``).
    """
    rels = relationships or {}
    index = build_included_index(included)
    out: dict[str, Any] = {}

    for wire, spec in rel_map.items():
        if isinstance(spec, tuple):
            attr, model = spec
        else:
            attr, model = wire.replace("-", "_"), spec

        rel = rels.get(wire)
        if not isinstance(rel, dict):
            continue
        data = rel.get("data")
        if data is None:
            continue
        if isinstance(data, list):
            out[attr] = [
                m
                for ref in data
                if isinstance(ref, dict)
                and (m := _hydrate(ref, model, index)) is not None
            ]
        elif isinstance(data, dict):
            m = _hydrate(data, model, index)
            if m is not None:
                out[attr] = m

    return out
