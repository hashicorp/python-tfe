# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Shared model base class.

``TFEModel`` is the base for every top-level resource model (anything parsed
from a JSON:API *resource object* and returned from a ``read``/``list``/etc.).
It is intentionally config-light — subclasses keep their own ``model_config`` —
and only adds the lossless related-resource escape hatch (``relationships`` /
``included`` and friends). Sub-objects, ``*Options`` models, and enums stay on
``pydantic.BaseModel``. See ``docs/MODELS.md`` (TFEModel vs BaseModel).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, PrivateAttr


class TFEModel(BaseModel):
    """Base for resources parsed from a JSON:API document.

    A JSON:API resource carries a ``relationships`` block (linkage references —
    ``type`` + ``id`` — for every related resource, modelled or not), and a
    response may carry a top-level ``included`` array with the full bodies of
    relations requested via ``?include=``. Declared relationships are hydrated
    into typed fields, but anything the SDK does not model would otherwise be
    dropped. This base keeps **both raw blocks** on the instance so related data
    is never lost — a lossless escape hatch that complements ``extra="allow"``
    (which only retains unknown *attributes*).

    Both are private attributes, so they never appear in ``model_dump()`` and add
    no public fields. Subclasses keep their own ``model_config``.

    The accessors are always present and stably typed — they return ``{}`` / ``[]``
    when the block was empty *or* absent from the wire. Because the API genuinely
    distinguishes the two (e.g. SSH keys omit ``relationships`` entirely, and
    ``included`` only appears when ``?include=`` is used), ``has_relationships`` /
    ``has_included`` report whether the block was actually present on the wire —
    without making the data accessors conditionally disappear.

    Accessors
    ---------
    * ``model.relationships``         — raw ``relationships`` block (dict).
    * ``model.included``              — raw ``included`` array (list of dicts).
    * ``model.has_relationships``     — was a ``relationships`` block on the wire?
    * ``model.has_included``          — was a top-level ``included`` array present?
    * ``model.included_by(type, id)`` — one included object by ``type``+``id``.
    * ``model.related(name)``         — refs of relationship ``name`` resolved to
      their full included bodies (falling back to the bare ``{type, id}`` ref
      when that relation was not ``?include=``-d).
    """

    _relationships: dict[str, Any] = PrivateAttr(default_factory=dict)
    _included: list[dict[str, Any]] = PrivateAttr(default_factory=list)
    _relationships_present: bool = PrivateAttr(default=False)
    _included_present: bool = PrivateAttr(default=False)

    def __eq__(self, other: object) -> bool:
        # Pydantic's default __eq__ also compares ``__pydantic_private__``, which
        # would make two models with identical public fields unequal merely
        # because one captured raw relationships/included. Those private blocks
        # are an out-of-band escape hatch and must NOT affect equality, so we
        # compare only the public surface (fields + model_extra) — keeping
        # equality behaviour identical to a plain BaseModel.
        if not isinstance(other, BaseModel):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__dict__ == other.__dict__
            and self.__pydantic_extra__ == other.__pydantic_extra__
        )

    __hash__ = None  # type: ignore[assignment]  # match BaseModel: unhashable

    @property
    def relationships(self) -> dict[str, Any]:
        """Raw JSON:API ``relationships`` block (untyped), exactly as returned."""
        return self._relationships

    @property
    def included(self) -> list[dict[str, Any]]:
        """Raw JSON:API ``included`` objects (untyped), exactly as returned."""
        return self._included

    @property
    def has_relationships(self) -> bool:
        """Whether a ``relationships`` block was present on the wire.

        Distinguishes "absent" from "present but empty" — both leave
        ``relationships == {}``.
        """
        return self._relationships_present

    @property
    def has_included(self) -> bool:
        """Whether a top-level ``included`` array was present on the wire.

        Distinguishes "absent" (no ``?include=`` / none returned) from "present
        but empty" — both leave ``included == []``.
        """
        return self._included_present

    def included_by(self, type_: str, id_: str) -> dict[str, Any] | None:
        """Return the raw included resource matching JSON:API ``type``+``id``."""
        return next(
            (
                i
                for i in self._included
                if i.get("type") == type_ and i.get("id") == id_
            ),
            None,
        )

    def related(self, name: str) -> list[dict[str, Any]]:
        """Resolve relationship ``name`` to a list of raw related objects.

        Each linkage reference is replaced by its full body from ``included``
        when present, otherwise the bare ``{type, id}`` reference is returned.
        Always returns a list (single relations become a one-item list).
        """
        rel = self._relationships.get(name) or {}
        data = rel.get("data")
        refs = data if isinstance(data, list) else ([data] if data else [])
        out: list[dict[str, Any]] = []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            rtype, rid = ref.get("type"), ref.get("id")
            full = (
                self.included_by(rtype, rid)
                if isinstance(rtype, str) and isinstance(rid, str)
                else None
            )
            out.append(full or ref)
        return out
