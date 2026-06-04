# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._http import HTTPTransport
from .._logging import logger


def _to_int(value: Any) -> int | None:
    """Best-effort integer coercion for pagination metadata values."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


class _Service:
    def __init__(self, t: HTTPTransport) -> None:
        self.t = t

    def _list(
        self, path: str, *, params: dict | None = None, paginated: bool = True
    ) -> Iterator[dict[str, Any]]:
        base_params = dict(params or {})

        # Some TFE endpoints are not paginated: they return the full collection
        # in a single response, ignore page[number]/page[size], and emit no
        # meta.pagination block (e.g. workspace /vars and /all-vars). Callers
        # opt those out so we issue exactly one request and never loop trying to
        # fetch a "next" page that re-returns the same set
        # (see hashicorp/python-tfe#181).
        if not paginated:
            r = self.t.request("GET", path, params=base_params)
            json_response = r.json()
            if not isinstance(json_response, dict):
                json_response = {}
            data = json_response.get("data", [])
            if isinstance(data, list):
                yield from data
            return

        page = int(base_params.get("page[number]", 1))
        while True:
            p = dict(base_params)
            p["page[number]"] = page
            p.setdefault("page[size]", 100)
            r = self.t.request("GET", path, params=p)

            # Handle cases where r.json() returns None or is not a dict
            json_response = r.json()
            if json_response is None or not isinstance(json_response, dict):
                json_response = {}

            data = json_response.get("data", [])
            if not isinstance(data, list):
                data = []
            yield from data
            if not data:
                # Defensive stop: some endpoints can return inconsistent pagination
                # metadata while yielding no rows; avoid unbounded follow-up requests.
                break

            # Prefer server pagination metadata when available. This avoids
            # prematurely terminating when servers clamp requested page sizes.
            meta = json_response.get("meta")
            pagination = meta.get("pagination", {}) if isinstance(meta, dict) else {}
            if isinstance(pagination, dict) and pagination:
                next_page = _to_int(
                    pagination.get("next-page", pagination.get("next_page"))
                )
                if next_page is not None and next_page > page:
                    page = next_page
                    continue

                current_page = _to_int(
                    pagination.get("current-page", pagination.get("current_page"))
                )
                total_pages = _to_int(
                    pagination.get("total-pages", pagination.get("total_pages"))
                )
                if (
                    current_page is not None
                    and total_pages is not None
                    and current_page < total_pages
                ):
                    candidate_page = current_page + 1
                    if candidate_page > page:
                        page = candidate_page
                        continue

                # Metadata present and indicates no next page.
                break

            # No pagination metadata. Genuine TFE list endpoints always include
            # meta.pagination, so a response without it is a non-paginated
            # collection returned in full. Treat it as a single complete page
            # and stop. Re-requesting would loop forever when the endpoint
            # ignores page[number]/page[size] and re-returns the same full set
            # (the root cause of hashicorp/python-tfe#181).
            if len(data) >= int(p["page[size]"]):
                logger.debug(
                    "List endpoint %s returned a full page (%d rows) without "
                    "pagination metadata; treating it as a single, "
                    "non-paginated response.",
                    path,
                    len(data),
                )
            break
