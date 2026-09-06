# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Result models shared by every workflow.

These are plain :class:`pydantic.BaseModel` types, deliberately *not*
``TFEModel``: a workflow result is synthesised locally, never parsed from a
JSON:API resource object, so the relationship/included machinery would be
permanently empty while reserving six attribute names and replacing ``__eq__``.

Workflow results *embed* SDK resource models as typed fields (``run: Run``)
rather than re-flattening their wire attributes, so callers keep
``.relationships`` and ``.related()`` on the embedded object. Never round-trip
an embedded resource through ``model_dump``/``model_validate`` - those blocks
are private attributes and are silently dropped.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["Kind", "Change", "WorkflowResult", "EnsureResult", "SENSITIVE"]

Kind = Literal["read", "write", "destructive"]

#: Placeholder substituted for any value that must never be echoed back.
SENSITIVE = "<sensitive>"


class Change(BaseModel):
    """One field a workflow changed, or would change under ``dry_run``."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    field: str
    before: Any = None
    after: Any = None

    @classmethod
    def redacted(cls, field: str) -> Change:
        """A change whose values must not be recorded."""
        return cls(field=field, before=SENSITIVE, after=SENSITIVE)

    def __str__(self) -> str:
        return f"{self.field}: {self.before!r} -> {self.after!r}"


class WorkflowResult(BaseModel):
    """Base class for every workflow return value.

    ``summary()`` is part of the public contract: agents and the skill read its
    keys, so renaming one is a breaking change.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    kind: Kind
    ok: bool = True
    warnings: list[str] = Field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        """Return a small, JSON-serializable digest of this result.

        Sized for an agent's context window: roughly twenty keys, no embedded
        resource payloads, no relationships, and never a secret.

        Returns:
            A JSON-serializable dict.
        """
        out: dict[str, Any] = {"kind": self.kind, "ok": self.ok}
        if self.warnings:
            out["warnings"] = list(self.warnings)
        return out

    def __str__(self) -> str:
        state = "ok" if self.ok else "failed"
        return f"{type(self).__name__}({state})"


class EnsureResult(WorkflowResult):
    """Outcome of an idempotent ``ensure_*`` workflow."""

    kind: Kind = "write"
    action: Literal[
        "created",
        "updated",
        "unchanged",
        "would_create",
        "would_update",
        "awaiting_confirmation",
    ]
    changes: list[Change] = Field(default_factory=list)
    resource_id: str | None = None
    resource_type: str | None = None

    @property
    def changed(self) -> bool:
        """True when the workflow made, or would make, a change."""
        return self.action not in ("unchanged",)

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "resource_id": self.resource_id,
                "resource_type": self.resource_type,
                "changed_fields": [c.field for c in self.changes],
            }
        )
        return out

    def __str__(self) -> str:
        target = self.resource_id or self.resource_type or "resource"
        if not self.changes:
            return f"{target}: {self.action}"
        return f"{target}: {self.action} ({len(self.changes)} field(s))"
