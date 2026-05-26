# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Convention checks for pyTFE Pydantic models.

These are not behavior tests — they enforce repo-wide conventions documented in
``docs/MODELS.md`` so a regression cannot ship.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Iterator

from pydantic import BaseModel

import pytfe.models


# Models that intentionally accept only their wire-format alias and reject the
# Python field name as a constructor kwarg. Every entry needs a reason. The
# test verifies allowlisted models really do have alias fields and really do
# omit populate_by_name=True — stale entries are flagged so this list cannot
# silently rot.
#
# Default for new work is the empty allowlist. If you are tempted to add an
# entry, first ask whether populate_by_name=True would actually break anything.
# Usually the answer is "no" and the right fix is to set the ConfigDict, not
# to allowlist.
ALIAS_POPULATE_ALLOWLIST: dict[str, str] = {
    # "SomeModel": "Reason this model intentionally rejects field-name kwargs",
}


def _iter_model_classes() -> Iterator[type[BaseModel]]:
    """Yield every BaseModel subclass defined in pytfe.models submodules.

    Walks the package without importing submodules eagerly so failures in an
    unrelated module surface as test failures, not import errors at collection.
    """
    seen: set[type[BaseModel]] = set()
    for module_info in pkgutil.iter_modules(pytfe.models.__path__):
        module = importlib.import_module(f"pytfe.models.{module_info.name}")
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj is not BaseModel
                # Skip re-exports from other modules so each class is checked
                # once in its defining module.
                and obj.__module__ == module.__name__
                and obj not in seen
            ):
                seen.add(obj)
                yield obj


def _has_alias_field(cls: type[BaseModel]) -> bool:
    return any(
        getattr(field, "alias", None) is not None
        for field in cls.model_fields.values()
    )


def _populate_by_name(cls: type[BaseModel]) -> bool:
    return bool(cls.model_config.get("populate_by_name", False))


def test_aliased_models_set_populate_by_name() -> None:
    """Models that declare an ``alias=`` field must allow construction by field
    name. Without ``populate_by_name=True`` callers cannot pass the Python
    field name as a kwarg (and for aliases that are Python keywords like
    ``global``, they cannot pass the alias as a kwarg either — they would have
    to use ``**{"global": ...}`` or ``model_validate({...})``).

    See ``docs/MODELS.md`` "Python keyword aliases require populate_by_name=True".
    """
    offenders: list[str] = []
    for cls in _iter_model_classes():
        if not _has_alias_field(cls):
            continue
        if _populate_by_name(cls):
            continue
        if cls.__name__ in ALIAS_POPULATE_ALLOWLIST:
            continue
        offenders.append(f"{cls.__module__}.{cls.__name__}")

    assert not offenders, (
        "Models with alias= fields must set "
        "`model_config = ConfigDict(populate_by_name=True, validate_by_name=True)`.\n"
        "Either add the ConfigDict or, if the model intentionally rejects "
        "field-name kwargs, add it to ALIAS_POPULATE_ALLOWLIST with a reason.\n"
        "Offenders:\n  - " + "\n  - ".join(offenders)
    )


def test_allowlist_entries_are_not_stale() -> None:
    """Each allowlist entry must correspond to a real model that still has
    alias fields and still omits populate_by_name. If a model has been fixed
    or no longer has aliases, its allowlist entry must be removed.
    """
    by_name: dict[str, type[BaseModel]] = {
        cls.__name__: cls for cls in _iter_model_classes()
    }

    stale: list[str] = []
    for name in ALIAS_POPULATE_ALLOWLIST:
        cls = by_name.get(name)
        if cls is None:
            stale.append(f"{name}: no such model in pytfe.models")
            continue
        if not _has_alias_field(cls):
            stale.append(f"{name}: no longer has alias= fields — remove from allowlist")
            continue
        if _populate_by_name(cls):
            stale.append(
                f"{name}: already sets populate_by_name=True — remove from allowlist"
            )

    assert not stale, (
        "Stale entries in ALIAS_POPULATE_ALLOWLIST:\n  - " + "\n  - ".join(stale)
    )
