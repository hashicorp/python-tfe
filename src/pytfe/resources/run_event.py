# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..errors import InvalidRunEventIDError, InvalidRunIDError
from ..models.comment import Comment
from ..models.run_event import (
    RunEvent,
    RunEventListOptions,
    RunEventReadOptions,
)
from ..models.user import User
from ..utils import _safe_str, valid_string_id
from ._base import _Service

# Typed relations hydrated from ?include= (actor, comment); see RunEventIncludeOpt.
_RUN_EVENT_REL_MAP: RelationMap = {"actor": User, "comment": Comment}


def _run_event_from(
    d: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> RunEvent:
    attr = d.get("attributes", {}) or {}
    rels = parse_relationships(
        d.get("relationships"), _RUN_EVENT_REL_MAP, included=included
    )
    return attach_jsonapi(
        RunEvent(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
            **rels,
        ),
        d,
        included,
    )


class RunEvents(_Service):
    def list(
        self, run_id: str, options: RunEventListOptions | None = None
    ) -> Iterator[RunEvent]:
        """List run events for a run.

        Args:
            run_id: The run ID (e.g. ``"run-xxxxxxxx"``).
            options: Optional include options, as a :class:`RunEventListOptions`.

        Returns:
            A single-use ``Iterator[RunEvent]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for event in client.run_events.list("run-CZcmD7eagjhyX0vN"):
            ...     print(event.action, event.description)
        """
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)
        # The run-events endpoint is not paginated; fetch the full set in one request.
        path = f"/api/v2/runs/{run_id}/run-events"
        for item in self._list(path, params=params, paginated=False):
            yield _run_event_from(item)

    def read(self, run_event_id: str) -> RunEvent:
        """Read a run event by its ID.

        Args:
            run_event_id: The run event ID (e.g. ``"re-xxxxxxxx"``).

        Returns:
            The :class:`RunEvent`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> event = client.run_events.read("re-read-123")
            >>> print(event.action)
        """
        return self.read_with_options(run_event_id)

    def read_with_options(
        self, run_event_id: str, options: RunEventReadOptions | None = None
    ) -> RunEvent:
        """Read a run event by its ID with include options.

        Args:
            run_event_id: The run event ID (e.g. ``"re-xxxxxxxx"``).
            options: Optional include options, as a :class:`RunEventReadOptions`.

        Returns:
            The :class:`RunEvent`.

        Raises:
            InvalidRunEventIDError: If ``run_event_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import RunEventIncludeOpt, RunEventReadOptions
            >>> event = client.run_events.read_with_options(
            ...     "re-read-456",
            ...     RunEventReadOptions(include=[RunEventIncludeOpt.RUN_EVENT_ACTOR]),
            ... )
        """
        if not valid_string_id(run_event_id):
            raise InvalidRunEventIDError()
        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)
        r = self.t.request(
            "GET",
            f"/api/v2/run-events/{run_event_id}",
            params=params,
        )
        payload = r.json()
        return _run_event_from(payload.get("data", {}), payload.get("included"))
