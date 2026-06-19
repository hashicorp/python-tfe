# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

from .._jsonapi import attach_jsonapi
from ..errors import ERR_INVALID_OAUTH_CLIENT_ID, ERR_INVALID_ORG
from ..models.oauth_client import (
    OAuthClient,
    OAuthClientAddProjectsOptions,
    OAuthClientCreateOptions,
    OAuthClientListOptions,
    OAuthClientReadOptions,
    OAuthClientRemoveProjectsOptions,
    OAuthClientUpdateOptions,
)
from ..utils import (
    valid_string_id,
    validate_oauth_client_add_projects_options,
    validate_oauth_client_create_options,
    validate_oauth_client_remove_projects_options,
)
from ._base import _Service


class OAuthClients(_Service):
    """OAuth clients service for managing VCS provider connections."""

    def list(
        self, organization: str, options: OAuthClientListOptions | None = None
    ) -> Iterator[OAuthClient]:
        """List OAuth clients in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional includes and pagination, as a
                :class:`OAuthClientListOptions`.

        Returns:
            A single-use ``Iterator[OAuthClient]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> for oauth_client in client.oauth_clients.list("my-org"):
            ...     print(oauth_client.id, oauth_client.name)
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/oauth-clients"
        params = {}

        if options:
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)
            if options.include:
                params["include"] = ",".join([opt.value for opt in options.include])

        for item in self._list(path, params=params):
            if item is None:
                continue  # type: ignore[unreachable]  # Skip None items
            yield self._parse_oauth_client(item)

    def create(
        self, organization: str, options: OAuthClientCreateOptions
    ) -> OAuthClient:
        """Create an OAuth client for a VCS provider.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: OAuth client provider settings, as a
                :class:`OAuthClientCreateOptions`.

        Returns:
            The created :class:`OAuthClient`.

        Raises:
            ValueError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OAuthClientCreateOptions, ServiceProviderType
            >>> oauth_client = client.oauth_clients.create(
            ...     "my-org",
            ...     OAuthClientCreateOptions(
            ...         name="github", api_url="https://api.github.com",
            ...         http_url="https://github.com",
            ...         service_provider=ServiceProviderType.GITHUB,
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        validate_oauth_client_create_options(options)

        body: dict[str, Any] = {
            "data": {
                "type": "oauth-clients",
                "attributes": options.model_dump(exclude_none=True, by_alias=True),
            }
        }

        # Handle relations separately
        if options.projects:
            body["data"]["relationships"] = {"projects": {"data": options.projects}}

        if options.agent_pool:
            if "relationships" not in body["data"]:
                body["data"]["relationships"] = {}
            body["data"]["relationships"]["agent-pool"] = {"data": options.agent_pool}

        path = f"/api/v2/organizations/{quote(organization)}/oauth-clients"
        response = self.t.request("POST", path, json_body=body)
        data = response.json()["data"]

        return self._parse_oauth_client(data)

    def read(self, oauth_client_id: str) -> OAuthClient:
        """Read an OAuth client by its ID.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).

        Returns:
            The :class:`OAuthClient`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> oauth_client = client.oauth_clients.read("oc-test123")
            >>> print(oauth_client.name)
        """
        return self.read_with_options(oauth_client_id, None)

    def read_with_options(
        self, oauth_client_id: str, options: OAuthClientReadOptions | None
    ) -> OAuthClient:
        """Read an OAuth client by its ID with include options.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).
            options: Optional include controls, as a :class:`OAuthClientReadOptions`.

        Returns:
            The :class:`OAuthClient`.

        Raises:
            ValueError: If ``oauth_client_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OAuthClientReadOptions
            >>> oauth_client = client.oauth_clients.read_with_options(
            ...     "oc-test123", OAuthClientReadOptions()
            ... )
        """
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}"
        params = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        payload = response.json()

        return self._parse_oauth_client(payload["data"], payload.get("included"))

    def update(
        self, oauth_client_id: str, options: OAuthClientUpdateOptions
    ) -> OAuthClient:
        """Update an OAuth client by its ID.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).
            options: OAuth client attributes to update, as a
                :class:`OAuthClientUpdateOptions`.

        Returns:
            The updated :class:`OAuthClient`.

        Raises:
            ValueError: If ``oauth_client_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OAuthClientUpdateOptions
            >>> oauth_client = client.oauth_clients.update(
            ...     "oc-test123", OAuthClientUpdateOptions(name="github-main")
            ... )
        """
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        body = {
            "data": {
                "type": "oauth-clients",
                "attributes": options.model_dump(exclude_none=True, by_alias=True),
            }
        }

        # Handle relations separately
        if options.agent_pool:
            body["data"]["relationships"] = {"agent-pool": {"data": options.agent_pool}}

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}"
        response = self.t.request("PATCH", path, json_body=body)
        data = response.json()["data"]

        return self._parse_oauth_client(data)

    def delete(self, oauth_client_id: str) -> None:
        """Delete an OAuth client by its ID.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            ValueError: If ``oauth_client_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.oauth_clients.delete("oc-test123")
        """
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}"
        self.t.request("DELETE", path)

    def add_projects(
        self, oauth_client_id: str, options: OAuthClientAddProjectsOptions
    ) -> None:
        """Add projects on an OAuth client.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).
            options: Project relationship changes, as a :class:`OAuthClientAddProjectsOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``oauth_client_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OAuthClientAddProjectsOptions
            >>> client.oauth_clients.add_projects(
            ...     "oc-test123",
            ...     OAuthClientAddProjectsOptions(projects=[{"type": "projects", "id": "prj-test1"}]),
            ... )
        """
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        validate_oauth_client_add_projects_options(options)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}/relationships/projects"
        self.t.request("POST", path, json_body={"data": options.projects})

    def remove_projects(
        self, oauth_client_id: str, options: OAuthClientRemoveProjectsOptions
    ) -> None:
        """Remove projects on an OAuth client.

        Args:
            oauth_client_id: The OAuth client ID (e.g. ``"oc-xxxxxxxx"``).
            options: Project relationship changes, as a :class:`OAuthClientRemoveProjectsOptions`.

        Returns:
            None.

        Raises:
            ValueError: If ``oauth_client_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OAuthClientRemoveProjectsOptions
            >>> client.oauth_clients.remove_projects(
            ...     "oc-test123",
            ...     OAuthClientRemoveProjectsOptions(projects=[{"type": "projects", "id": "prj-test1"}]),
            ... )
        """
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        validate_oauth_client_remove_projects_options(options)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}/relationships/projects"
        self.t.request("DELETE", path, json_body={"data": options.projects})

    def _parse_oauth_client(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> OAuthClient:
        """Parse OAuth client data from API response."""
        oauth_client = OAuthClient(
            id=data.get("id"),
            **data.get("attributes", {}),
        )

        # Handle relationships
        relationships = data.get("relationships", {})

        if "organization" in relationships:
            oauth_client.organization = relationships["organization"].get("data")

        if "oauth-tokens" in relationships:
            oauth_client.oauth_tokens = relationships["oauth-tokens"].get("data", [])

        if "agent-pool" in relationships:
            oauth_client.agent_pool = relationships["agent-pool"].get("data")

        if "projects" in relationships:
            oauth_client.projects = relationships["projects"].get("data", [])

        return attach_jsonapi(oauth_client, data, included)
