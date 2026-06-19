from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import quote

from ..errors import ERR_INVALID_ORG
from ..models.organization_token import (
    OrganizationToken,
    OrganizationTokenCreateOptions,
    OrganizationTokenDeleteOptions,
    OrganizationTokenReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class OrganizationTokens(_Service):
    """Organization tokens service for managing TFE organization tokens."""

    def create(self, organization: str) -> OrganizationToken:
        """Create a new organization token, replacing any existing token.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`OrganizationToken`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> token = client.organization_tokens.create("my-org")
            >>> print(token.id)
        """
        return self.create_with_options(organization)

    def create_with_options(
        self,
        organization: str,
        options: OrganizationTokenCreateOptions | None = None,
    ) -> OrganizationToken:
        """Create a new organization token with options.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Token creation options, as a
                :class:`OrganizationTokenCreateOptions`.

        Returns:
            The :class:`OrganizationToken`.

        Raises:
            ValueError: If ``organization`` is invalid or the response shape is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from datetime import datetime
            >>> from pytfe.models import OrganizationTokenCreateOptions
            >>> token = client.organization_tokens.create_with_options(
            ...     "my-org",
            ...     OrganizationTokenCreateOptions(expired_at=datetime(2027, 1, 1)),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/authentication-token"

        # Build request body
        body: dict[str, Any] = {
            "data": {
                "type": "authentication-token",
                "attributes": {},
            }
        }

        # Add optional attributes
        if options and options.expired_at is not None:
            body["data"]["attributes"]["expired-at"] = options.expired_at.isoformat()

        # Add query parameters for token type if specified
        params = {}
        if options and options.token_type is not None:
            params["token"] = options.token_type.value

        if params:
            response = self.t.request("POST", path, json_body=body, params=params)
        else:
            response = self.t.request("POST", path, json_body=body)

        data = response.json()

        if "data" in data:
            return self._parse_organization_token(data["data"])

        raise ValueError("Invalid response format")

    def read(self, organization: str) -> OrganizationToken:
        """Read the organization token.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`OrganizationToken`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> token = client.organization_tokens.read("my-org")
            >>> print(token.description)
        """
        return self.read_with_options(organization, None)

    def read_with_options(
        self,
        organization: str,
        options: OrganizationTokenReadOptions | None = None,
    ) -> OrganizationToken:
        """Read the organization token with options.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Token read options, as a :class:`OrganizationTokenReadOptions`.

        Returns:
            The :class:`OrganizationToken`.

        Raises:
            ValueError: If ``organization`` is invalid or the response shape is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationTokenReadOptions, TokenType
            >>> token = client.organization_tokens.read_with_options(
            ...     "my-org",
            ...     OrganizationTokenReadOptions(token_type=TokenType.AUDIT_TRAILS),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/authentication-token"

        # Add query parameters for token type if specified
        params = {}
        if options and options.token_type is not None:
            params["token"] = options.token_type.value

        response = self.t.request("GET", path, params=params if params else None)
        data = response.json()

        if "data" in data:
            return self._parse_organization_token(data["data"])

        raise ValueError("Invalid response format")

    def delete(self, organization: str) -> None:
        """Delete the organization token.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.organization_tokens.delete("my-org")
        """
        return self.delete_with_options(organization, None)

    def delete_with_options(
        self,
        organization: str,
        options: OrganizationTokenDeleteOptions | None = None,
    ) -> None:
        """Delete the organization token with options.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Token delete options, as a
                :class:`OrganizationTokenDeleteOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``organization`` is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationTokenDeleteOptions, TokenType
            >>> client.organization_tokens.delete_with_options(
            ...     "my-org",
            ...     OrganizationTokenDeleteOptions(token_type=TokenType.AUDIT_TRAILS),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/authentication-token"

        # Add query parameters for token type if specified
        params = {}
        if options and options.token_type is not None:
            params["token"] = options.token_type.value

        if params:
            self.t.request("DELETE", path, params=params)
        else:
            self.t.request("DELETE", path)

    def _parse_organization_token(self, data: dict[str, Any]) -> OrganizationToken:
        """Parse organization token data from API response.

        Args:
            data: The token data from the API response

        Returns:
            OrganizationToken: The parsed organization token
        """
        attributes = data.get("attributes", {})

        # Parse timestamps
        created_at_str = attributes.get("created-at")
        created_at = (
            datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at_str
            else datetime.now()
        )

        last_used_at_str = attributes.get("last-used-at")
        last_used_at = (
            datetime.fromisoformat(last_used_at_str.replace("Z", "+00:00"))
            if last_used_at_str
            else None
        )

        expired_at_str = attributes.get("expired-at")
        expired_at = (
            datetime.fromisoformat(expired_at_str.replace("Z", "+00:00"))
            if expired_at_str
            else None
        )

        # Parse created-by relationship
        created_by = None
        # For now, just set to None since it's mainly for display

        return OrganizationToken(
            id=data.get("id", ""),
            created_at=created_at,
            description=attributes.get("description", ""),
            last_used_at=last_used_at,
            token=attributes.get("token", ""),
            expired_at=expired_at,
            created_by=created_by,
        )
