from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from .._http import HTTPTransport


class _Service:
    def __init__(self, t: HTTPTransport) -> None:
        self.t = t

    def _list(
        self, path: str, *, params: dict | None = None
    ) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            p = dict(params or {})
            p.setdefault("page[number]", page)
            p.setdefault("page[size]", 100)
            r = self.t.request("GET", path, params=p)

            # Handle cases where r.json() returns None or is not a dict
            json_response = r.json()
            if json_response is None:
                json_response = {}

            data = json_response.get("data", [])
            yield from data
            page_size = int(p["page[size]"])
            if len(data) < page_size:
                break
            page += 1


"""
Warning: Do Not Use this Async Service as its not stable with HashiCorp API.
"""


class _AService:
    def __init__(self, t: HTTPTransport) -> None:
        self.t = t

    async def _alist(
        self, path: str, *, params: dict | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        page = 1
        while True:
            p = dict(params or {})
            p.setdefault("page[number]", page)
            p.setdefault("page[size]", 100)
            r = await self.t.arequest("GET", path, params=p)
            data = r.json().get("data", [])
            for item in data:
                yield item
            page_size = int(p["page[size]"])
            if len(data) < page_size:
                break
            page += 1
