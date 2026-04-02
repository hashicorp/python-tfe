# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import quote

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
        """List all OAuth clients for a given organization."""
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
        """Create an OAuth client to connect an organization and a VCS provider."""
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
        """Read an OAuth client by its ID."""
        return self.read_with_options(oauth_client_id, None)

    def read_with_options(
        self, oauth_client_id: str, options: OAuthClientReadOptions | None
    ) -> OAuthClient:
        """Read an OAuth client by its ID with options."""
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}"
        params = {}

        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])

        response = self.t.request("GET", path, params=params)
        data = response.json()["data"]

        return self._parse_oauth_client(data)

    def update(
        self, oauth_client_id: str, options: OAuthClientUpdateOptions
    ) -> OAuthClient:
        """Update an OAuth client by its ID."""
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
        """Delete an OAuth client by its ID."""
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}"
        self.t.request("DELETE", path)

    def add_projects(
        self, oauth_client_id: str, options: OAuthClientAddProjectsOptions
    ) -> None:
        """Add projects to a given OAuth client."""
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        validate_oauth_client_add_projects_options(options)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}/relationships/projects"
        self.t.request("POST", path, json_body={"data": options.projects})

    def remove_projects(
        self, oauth_client_id: str, options: OAuthClientRemoveProjectsOptions
    ) -> None:
        """Remove projects from an OAuth client."""
        if not valid_string_id(oauth_client_id):
            raise ValueError(ERR_INVALID_OAUTH_CLIENT_ID)

        validate_oauth_client_remove_projects_options(options)

        path = f"/api/v2/oauth-clients/{quote(oauth_client_id)}/relationships/projects"
        self.t.request("DELETE", path, json_body={"data": options.projects})

    def _parse_oauth_client(self, data: dict[str, Any]) -> OAuthClient:
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

        return oauth_client
