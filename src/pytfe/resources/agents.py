# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Agent resource implementation for the Python TFE SDK.

This module provides the Agents service for managing individual Terraform Enterprise/Cloud
agents within agent pools.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

from .._jsonapi import attach_jsonapi
from ..models.agent import (
    Agent,
    AgentListOptions,
    AgentReadOptions,
    AgentStatus,
    AgentToken,
    AgentTokenCreateOptions,
    AgentTokenListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


def _safe_str(value: Any, default: str = "") -> str:
    """Safely convert a value to string with optional default."""
    if value is None:
        return default
    return str(value)


def _safe_agent_status(value: Any) -> AgentStatus | None:
    """Safely convert a value to an AgentStatus enum."""
    if value is None:
        return None
    if isinstance(value, AgentStatus):
        return value
    try:
        # Convert string to AgentStatus
        return AgentStatus(str(value))
    except (ValueError, TypeError):
        return AgentStatus.UNKNOWN


class Agents(_Service):
    """Agents service for managing individual Terraform Enterprise agents."""

    def list(
        self, agent_pool_id: str, options: AgentListOptions | None = None
    ) -> Iterator[Agent]:
        """List agents in an agent pool.

        Args:
            agent_pool_id: The agent pool ID (e.g. ``"apool-xxxxxxxx"``).
            options: Optional filters and pagination, as a :class:`AgentListOptions`.

        Returns:
            A single-use ``Iterator[Agent]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``agent_pool_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AgentListOptions, AgentStatus
            >>> for agent in client.agents.list(
            ...     "apool-123456789abcdef0", AgentListOptions(status=AgentStatus.IDLE)
            ... ):
            ...     print(agent.id, agent.status)
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        path = f"/api/v2/agent-pools/{agent_pool_id}/agents"
        params: dict[str, str | int] = {}

        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.status:
                params["filter[status]"] = options.status.value

        items_iter = self._list(path, params=params)

        for item in items_iter:
            # Extract agent data from API response
            attr = item.get("attributes", {}) or {}

            # Parse status
            status_str = attr.get("status")
            status = None
            if status_str:
                try:
                    status = AgentStatus(status_str)
                except ValueError:
                    status = AgentStatus.UNKNOWN

            agent_data = {
                "id": _safe_str(item.get("id")),
                "name": _safe_str(attr.get("name")),
                "status": status,
                "version": _safe_str(attr.get("version")),
                "last_ping_at": attr.get("last-ping-at"),
                "ip_address": _safe_str(attr.get("ip-address")),
            }

            yield Agent(
                id=_safe_str(agent_data["id"]) or "",
                name=agent_data["name"],
                status=_safe_agent_status(agent_data["status"]),
                version=agent_data["version"],
                last_ping_at=cast(Any, agent_data["last_ping_at"]),
                ip_address=agent_data["ip_address"],
            )

    def read(self, agent_id: str, options: AgentReadOptions | None = None) -> Agent:
        """Read an agent by its ID.

        Args:
            agent_id: The agent ID (e.g. ``"agent-xxxxxxxx"``).
            options: Related resources to include, as a :class:`AgentReadOptions`.

        Returns:
            The :class:`Agent`.

        Raises:
            ValueError: If ``agent_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> agent = client.agents.read("agent-123456789abcdef0")
            >>> print(agent.name)
        """
        if not valid_string_id(agent_id):
            raise ValueError("Agent ID is required and must be valid")

        path = f"/api/v2/agents/{agent_id}"
        params: dict[str, str] = {}

        if options and options.include:
            params["include"] = ",".join(options.include)

        if params:
            response = self.t.request("GET", path, params=params)
        else:
            response = self.t.request("GET", path)

        payload = response.json()
        data = payload["data"]

        # Extract agent data from response
        attr = data.get("attributes", {}) or {}

        # Parse status
        status_str = attr.get("status")
        status = None
        if status_str:
            try:
                status = AgentStatus(status_str)
            except ValueError:
                status = AgentStatus.UNKNOWN

        agent_data = {
            "id": _safe_str(data.get("id")),
            "name": _safe_str(attr.get("name")),
            "status": status,
            "version": _safe_str(attr.get("version")),
            "last_ping_at": attr.get("last-ping-at"),
            "ip_address": _safe_str(attr.get("ip-address")),
        }

        return attach_jsonapi(
            Agent(
                id=_safe_str(agent_data["id"]) or "",
                name=agent_data["name"],
                status=_safe_agent_status(agent_data["status"]),
                version=agent_data["version"],
                last_ping_at=cast(Any, agent_data["last_ping_at"]),
                ip_address=agent_data["ip_address"],
            ),
            data,
            payload.get("included"),
        )

    def delete(self, agent_id: str) -> None:
        """Delete an agent.

        Args:
            agent_id: The agent ID (e.g. ``"agent-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``agent_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.agents.delete("agent-123456789abcdef0")
        """
        if not valid_string_id(agent_id):
            raise ValueError("Agent ID is required and must be valid")

        path = f"/api/v2/agents/{agent_id}"
        self.t.request("DELETE", path)


class AgentTokens(_Service):
    """Agent Tokens service for managing authentication tokens for agents."""

    def list(
        self, agent_pool_id: str, options: AgentTokenListOptions | None = None
    ) -> Iterator[AgentToken]:
        """List agent tokens for an agent pool.

        Args:
            agent_pool_id: The agent pool ID (e.g. ``"apool-xxxxxxxx"``).
            options: Optional pagination, as a :class:`AgentTokenListOptions`.

        Returns:
            A single-use ``Iterator[AgentToken]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``agent_pool_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for token in client.agent_tokens.list("apool-123456789abcdef0"):
            ...     print(token.id, token.description)
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        path = f"/api/v2/agent-pools/{agent_pool_id}/authentication-tokens"
        params: dict[str, str | int] = {}

        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        items_iter = self._list(path, params=params)

        for item in items_iter:
            # Extract token data from API response
            attr = item.get("attributes", {}) or {}

            token_data = {
                "id": _safe_str(item.get("id")),
                "description": _safe_str(attr.get("description")),
                "created_at": attr.get("created-at"),
                "last_used_at": attr.get("last-used-at"),
                # Token value is not returned in list operations for security
                "token": None,
            }

            yield AgentToken(
                id=_safe_str(token_data["id"]) or "",
                description=token_data["description"],
                created_at=cast(Any, token_data["created_at"]),
                last_used_at=cast(Any, token_data["last_used_at"]),
                token=token_data["token"],
            )

    def create(
        self, agent_pool_id: str, options: AgentTokenCreateOptions
    ) -> AgentToken:
        """Create an agent token for an agent pool.

        Args:
            agent_pool_id: The agent pool ID (e.g. ``"apool-xxxxxxxx"``).
            options: The token description, as a :class:`AgentTokenCreateOptions`.

        Returns:
            The created :class:`AgentToken` with its one-time token value.

        Raises:
            ValueError: If ``agent_pool_id`` is invalid or the description is empty.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AgentTokenCreateOptions
            >>> options = AgentTokenCreateOptions(description="ci-runner")
            >>> token = client.agent_tokens.create(
            ...     "apool-123456789abcdef0", options
            ... )
        """
        if not valid_string_id(agent_pool_id):
            raise ValueError("Agent pool ID is required and must be valid")

        if not options.description:
            raise ValueError("Token description is required")

        path = f"/api/v2/agent-pools/{agent_pool_id}/authentication-tokens"
        attributes = {"description": options.description}

        payload = {"data": {"type": "authentication-tokens", "attributes": attributes}}

        response = self.t.request("POST", path, json_body=payload)
        data = response.json()["data"]

        # Extract token data from response
        attr = data.get("attributes", {}) or {}

        token_data = {
            "id": _safe_str(data.get("id")),
            "description": _safe_str(attr.get("description")),
            "created_at": attr.get("created-at"),
            "last_used_at": attr.get("last-used-at"),
            # Token value is only returned on creation
            "token": _safe_str(attr.get("token")),
        }

        return AgentToken(
            id=_safe_str(token_data["id"]) or "",
            description=token_data["description"],
            created_at=cast(Any, token_data["created_at"]),
            last_used_at=cast(Any, token_data["last_used_at"]),
            token=token_data["token"],
        )

    def read(self, agent_token_id: str) -> AgentToken:
        """Read an agent token by its ID.

        Args:
            agent_token_id: The agent token ID (e.g. ``"at-xxxxxxxx"``).

        Returns:
            The :class:`AgentToken` without the secret token value.

        Raises:
            ValueError: If ``agent_token_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> token = client.agent_tokens.read("at-123456789abcdef0")
            >>> print(token.description)
        """
        if not valid_string_id(agent_token_id):
            raise ValueError("Agent token ID is required and must be valid")

        path = f"/api/v2/authentication-tokens/{agent_token_id}"
        response = self.t.request("GET", path)
        data = response.json()["data"]

        # Extract token data from response
        attr = data.get("attributes", {}) or {}

        token_data = {
            "id": _safe_str(data.get("id")),
            "description": _safe_str(attr.get("description")),
            "created_at": attr.get("created-at"),
            "last_used_at": attr.get("last-used-at"),
            # Token value is never returned in read operations for security
            "token": None,
        }

        return AgentToken(
            id=_safe_str(token_data["id"]) or "",
            description=token_data["description"],
            created_at=cast(Any, token_data["created_at"]),
            last_used_at=cast(Any, token_data["last_used_at"]),
            token=token_data["token"],
        )

    def delete(self, agent_token_id: str) -> None:
        """Delete an agent token.

        Args:
            agent_token_id: The agent token ID (e.g. ``"at-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``agent_token_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.agent_tokens.delete("at-123456789abcdef0")
        """
        if not valid_string_id(agent_token_id):
            raise ValueError("Agent token ID is required and must be valid")

        path = f"/api/v2/authentication-tokens/{agent_token_id}"
        self.t.request("DELETE", path)
