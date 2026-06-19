# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import RelationMap, attach_jsonapi, parse_relationships
from ..errors import (
    InvalidAgentPoolIDError,
    InvalidCIDRRangeIDError,
    InvalidCIDRRangeListIDError,
    InvalidOrgError,
)
from ..models.cidr_range_list import (
    CIDRRange,
    CIDRRangeCreateOptions,
    CIDRRangeList,
    CIDRRangeListCreateOptions,
    CIDRRangeListListOptions,
    CIDRRangeListUpdateOptions,
    CIDRRangeUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service

_CIDR_RANGE_LIST_REL_MAP: RelationMap = {"cidr-ranges": CIDRRange}


def _cidr_range_list_from(
    d: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> CIDRRangeList:
    """Parse a JSON:API ``cidr-range-lists`` resource into a CIDRRangeList."""
    attrs = dict(d.get("attributes") or {})
    attrs["id"] = d.get("id")
    attrs.update(
        parse_relationships(
            d.get("relationships"), _CIDR_RANGE_LIST_REL_MAP, included=included
        )
    )
    return attach_jsonapi(CIDRRangeList.model_validate(attrs), d, included)


def _cidr_range_from(
    d: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> CIDRRange:
    """Parse a JSON:API ``cidr-ranges`` resource into a CIDRRange."""
    attrs = dict(d.get("attributes") or {})
    attrs["id"] = d.get("id")
    return attach_jsonapi(CIDRRange.model_validate(attrs), d, included)


class CIDRRangeLists(_Service):
    """Service for managing IP allowlists (JSON:API ``cidr-range-lists``)."""

    def list(
        self, organization: str, options: CIDRRangeListListOptions | None = None
    ) -> Iterator[CIDRRangeList]:
        """List IP allowlists for an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional search and pagination options, as a
                :class:`CIDRRangeListListOptions`.

        Returns:
            A single-use ``Iterator[CIDRRangeList]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for allowlist in client.cidr_range_lists.list("my-org"):
            ...     print(allowlist.id, allowlist.name)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True, mode="json")
            if options
            else {}
        )
        path = f"/api/v2/organizations/{organization}/cidr-range-lists"
        for item in self._list(path, params=params):
            yield _cidr_range_list_from(item)

    def create(
        self, organization: str, options: CIDRRangeListCreateOptions
    ) -> CIDRRangeList:
        """Create an IP allowlist in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The allowlist settings, as a
                :class:`CIDRRangeListCreateOptions`.

        Returns:
            The created :class:`CIDRRangeList`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CIDRRangeListCreateOptions, EnforcementScope
            >>> allowlist = client.cidr_range_lists.create(
            ...     "my-org",
            ...     CIDRRangeListCreateOptions(
            ...         name="Office Network",
            ...         enforcement_scope=EnforcementScope.SELECTED_AGENT_POOLS,
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        payload = {
            "data": {
                "type": "cidr-range-lists",
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                ),
            }
        }
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/cidr-range-lists",
            json_body=payload,
        )
        body = r.json()
        return _cidr_range_list_from(body["data"], body.get("included"))

    def read(self, cidr_range_list_id: str) -> CIDRRangeList:
        """Read an IP allowlist by its ID.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).

        Returns:
            The :class:`CIDRRangeList`.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> allowlist = client.cidr_range_lists.read("crl-xKw8dxQPqVQRZmCe")
            >>> print(allowlist.name)
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        r = self.t.request("GET", f"/api/v2/cidr-range-lists/{cidr_range_list_id}")
        body = r.json()
        return _cidr_range_list_from(body["data"], body.get("included"))

    def update(
        self, cidr_range_list_id: str, options: CIDRRangeListUpdateOptions
    ) -> CIDRRangeList:
        """Update an IP allowlist by its ID.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).
            options: The allowlist updates, as a
                :class:`CIDRRangeListUpdateOptions`.

        Returns:
            The updated :class:`CIDRRangeList`.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CIDRRangeListUpdateOptions
            >>> allowlist = client.cidr_range_lists.update(
            ...     "crl-xKw8dxQPqVQRZmCe",
            ...     CIDRRangeListUpdateOptions(name="Office Network"),
            ... )
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        attributes = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        # The API rejects a PATCH that omits enforcement-scope ("Enforcement
        # scope is not included in the list") even though the docs say an
        # omitted scope is preserved. Emulate that documented preserve-on-omit
        # behaviour by carrying the current scope forward when none was given.
        if "enforcement-scope" not in attributes:
            current = self.read(cidr_range_list_id)
            if current.enforcement_scope is not None:
                attributes["enforcement-scope"] = current.enforcement_scope.value
        payload = {"data": {"type": "cidr-range-lists", "attributes": attributes}}
        r = self.t.request(
            "PATCH",
            f"/api/v2/cidr-range-lists/{cidr_range_list_id}",
            json_body=payload,
        )
        body = r.json()
        return _cidr_range_list_from(body["data"], body.get("included"))

    def delete(self, cidr_range_list_id: str) -> None:
        """Delete an IP allowlist by its ID.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> client.cidr_range_lists.delete("crl-xKw8dxQPqVQRZmCe")
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        self.t.request("DELETE", f"/api/v2/cidr-range-lists/{cidr_range_list_id}")

    def list_cidr_ranges(self, cidr_range_list_id: str) -> Iterator[CIDRRange]:
        """List CIDR ranges attached to an IP allowlist.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).

        Returns:
            A single-use ``Iterator[CIDRRange]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> ranges = client.cidr_range_lists.list_cidr_ranges(
            ...     "crl-xKw8dxQPqVQRZmCe"
            ... )
            >>> for cidr_range in ranges:
            ...     print(cidr_range.cidr_block)
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        path = (
            f"/api/v2/cidr-range-lists/{cidr_range_list_id}/relationships/cidr-ranges"
        )
        for item in self._list(path):
            yield _cidr_range_from(item)

    def add_cidr_range(
        self, cidr_range_list_id: str, options: CIDRRangeCreateOptions
    ) -> CIDRRange:
        """Add a CIDR range to an IP allowlist.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).
            options: The CIDR range settings, as a :class:`CIDRRangeCreateOptions`.

        Returns:
            The created :class:`CIDRRange`.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CIDRRangeCreateOptions
            >>> cidr_range = client.cidr_range_lists.add_cidr_range(
            ...     "crl-xKw8dxQPqVQRZmCe",
            ...     CIDRRangeCreateOptions(cidr_block="192.168.1.0/24"),
            ... )
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        payload = {
            "data": {
                "type": "cidr-ranges",
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                ),
            }
        }
        r = self.t.request(
            "POST",
            f"/api/v2/cidr-range-lists/{cidr_range_list_id}/relationships/cidr-ranges",
            json_body=payload,
        )
        body = r.json()
        return _cidr_range_from(body["data"], body.get("included"))

    def add_agent_pools(
        self, cidr_range_list_id: str, agent_pool_ids: builtins.list[str]
    ) -> None:
        """Associate agent pools with an IP allowlist.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).
            agent_pool_ids: The agent pool IDs (e.g. ``["apool-xxxxxxxx"]``).

        Returns:
            None.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            InvalidAgentPoolIDError: If an agent pool ID is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.cidr_range_lists.add_agent_pools(
            ...     "crl-xKw8dxQPqVQRZmCe",
            ...     ["apool-abc123"],
            ... )
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        payload = {"data": self._agent_pool_refs(agent_pool_ids)}
        self.t.request(
            "POST",
            f"/api/v2/cidr-range-lists/{cidr_range_list_id}/relationships/agent-pools",
            json_body=payload,
        )

    def remove_agent_pools(
        self, cidr_range_list_id: str, agent_pool_ids: builtins.list[str]
    ) -> None:
        """Remove agent pool associations from an IP allowlist.

        Args:
            cidr_range_list_id: The IP allowlist ID (e.g. ``"crl-xxxxxxxx"``).
            agent_pool_ids: The agent pool IDs (e.g. ``["apool-xxxxxxxx"]``).

        Returns:
            None.

        Raises:
            InvalidCIDRRangeListIDError: If ``cidr_range_list_id`` is not valid.
            InvalidAgentPoolIDError: If an agent pool ID is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.cidr_range_lists.remove_agent_pools(
            ...     "crl-xKw8dxQPqVQRZmCe",
            ...     ["apool-abc123"],
            ... )
        """
        if not valid_string_id(cidr_range_list_id):
            raise InvalidCIDRRangeListIDError()
        payload = {"data": self._agent_pool_refs(agent_pool_ids)}
        self.t.request(
            "DELETE",
            f"/api/v2/cidr-range-lists/{cidr_range_list_id}/relationships/agent-pools",
            json_body=payload,
        )

    @staticmethod
    def _agent_pool_refs(
        agent_pool_ids: builtins.list[str],
    ) -> builtins.list[dict[str, str]]:
        # JSON:API to-many relationship modification: an array of identifier
        # objects (the request body the docs reference via @payload.json).
        if not agent_pool_ids:
            raise InvalidAgentPoolIDError("at least one agent pool ID is required")
        refs: builtins.list[dict[str, str]] = []
        for apid in agent_pool_ids:
            if not valid_string_id(apid):
                raise InvalidAgentPoolIDError()
            refs.append({"type": "agent-pools", "id": apid})
        return refs


class CIDRRanges(_Service):
    """Service for managing individual CIDR ranges within IP allowlists."""

    def read(self, cidr_range_id: str) -> CIDRRange:
        """Read a CIDR range by its ID.

        Args:
            cidr_range_id: The CIDR range ID (e.g. ``"cidr-xxxxxxxx"``).

        Returns:
            The :class:`CIDRRange`.

        Raises:
            InvalidCIDRRangeIDError: If ``cidr_range_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> cidr_range = client.cidr_ranges.read("cidr-6huHpM7asDp7TaiP")
            >>> print(cidr_range.cidr_block)
        """
        if not valid_string_id(cidr_range_id):
            raise InvalidCIDRRangeIDError()
        r = self.t.request("GET", f"/api/v2/cidr-ranges/{cidr_range_id}")
        body = r.json()
        return _cidr_range_from(body["data"], body.get("included"))

    def update(self, cidr_range_id: str, options: CIDRRangeUpdateOptions) -> CIDRRange:
        """Update a CIDR range by its ID.

        Args:
            cidr_range_id: The CIDR range ID (e.g. ``"cidr-xxxxxxxx"``).
            options: The CIDR range updates, as a :class:`CIDRRangeUpdateOptions`.

        Returns:
            The updated :class:`CIDRRange`.

        Raises:
            InvalidCIDRRangeIDError: If ``cidr_range_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CIDRRangeUpdateOptions
            >>> cidr_range = client.cidr_ranges.update(
            ...     "cidr-6huHpM7asDp7TaiP",
            ...     CIDRRangeUpdateOptions(cidr_block="192.168.2.0/24"),
            ... )
        """
        if not valid_string_id(cidr_range_id):
            raise InvalidCIDRRangeIDError()
        payload = {
            "data": {
                "type": "cidr-ranges",
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                ),
            }
        }
        r = self.t.request(
            "PATCH", f"/api/v2/cidr-ranges/{cidr_range_id}", json_body=payload
        )
        body = r.json()
        return _cidr_range_from(body["data"], body.get("included"))

    def delete(self, cidr_range_id: str) -> None:
        """Delete a CIDR range by its ID.

        Args:
            cidr_range_id: The CIDR range ID (e.g. ``"cidr-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidCIDRRangeIDError: If ``cidr_range_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> client.cidr_ranges.delete("cidr-6huHpM7asDp7TaiP")
        """
        if not valid_string_id(cidr_range_id):
            raise InvalidCIDRRangeIDError()
        self.t.request("DELETE", f"/api/v2/cidr-ranges/{cidr_range_id}")
