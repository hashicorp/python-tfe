# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""GitHub App installation discovery resource.

Read-only lookup of GitHub App installations the authenticated user can
see on HCP Terraform. Used to discover the ``github-app-installation-id``
value that workspace/stack/registry-module VCS configuration takes.
The App authorisation itself happens in the HCP Terraform UI; this
resource only exposes the lookup.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidGitHubAppInstallationIDError
from ..models.github_app_installation import (
    GitHubAppInstallation,
    GitHubAppInstallationListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


def _parse(data: dict[str, Any]) -> GitHubAppInstallation:
    attrs = data.get("attributes") or {}
    return attach_jsonapi(
        GitHubAppInstallation.model_validate({"id": data.get("id"), **attrs}), data
    )


class GitHubAppInstallations(_Service):
    """Resource for ``/api/v2/github-app/installations`` (list) and
    ``/api/v2/github-app/installation/{id}`` (read — singular ``installation``).
    """

    def list(
        self, options: GitHubAppInstallationListOptions | None = None
    ) -> Iterator[GitHubAppInstallation]:
        """List GitHub App installations visible to the authenticated user.

        Args:
            options: Optional installation filters, as a
                :class:`GitHubAppInstallationListOptions`.

        Returns:
            A single-use ``Iterator[GitHubAppInstallation]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import GitHubAppInstallationListOptions
            >>> for installation in client.github_app_installations.list(
            ...     GitHubAppInstallationListOptions(name="my-github-org")
            ... ):
            ...     print(installation.id, installation.installation_id)
        """
        # Endpoint is not documented as paginated; we fetch a single page
        # and yield from it rather than going through the paginating
        # ``self._list`` helper which would add unwanted page[] params.
        params = (
            options.model_dump(by_alias=True, exclude_none=True, mode="json")
            if options
            else None
        )
        r = self.t.request("GET", "/api/v2/github-app/installations", params=params)
        for item in r.json().get("data") or []:
            yield _parse(item)

    def read(self, github_app_installation_id: str) -> GitHubAppInstallation:
        """Read a GitHub App installation by its HCP Terraform ID.

        Args:
            github_app_installation_id: The GitHub App installation ID (e.g.
                ``"ghainst-xxxxxxxx"``).

        Returns:
            The :class:`GitHubAppInstallation`.

        Raises:
            InvalidGitHubAppInstallationIDError: If ``github_app_installation_id`` is
                not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> installation = client.github_app_installations.read(
            ...     "ghainst-xxxxxxxx"
            ... )
            >>> print(installation.name)
        """
        if not valid_string_id(github_app_installation_id):
            raise InvalidGitHubAppInstallationIDError()
        # Note: read uses the singular path segment ``installation`` (not
        # the plural ``installations`` that list uses). This is the
        # documented shape — not a typo.
        r = self.t.request(
            "GET",
            f"/api/v2/github-app/installation/{github_app_installation_id}",
        )
        return _parse(r.json()["data"])
