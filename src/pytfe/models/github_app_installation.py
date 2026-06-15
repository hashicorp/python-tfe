# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for HCP Terraform's GitHub App installation discovery API.

These resources are read-only. The actual GitHub App authorisation flow
happens through the HCP Terraform UI; this SDK only exposes the lookup
needed when callers want to find the ``github-app-installation-id`` to
plug into workspace, stack, or registry-module VCS configuration.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GitHubAppInstallationType(str, Enum):
    """Whether the GitHub App is installed against a user account or
    an organization. The upstream API returns these as wire strings
    capitalized (verified live: ``"Organization"`` / ``"User"``); the
    enum mirrors that exactly so equality checks work without case
    coercion. The model field itself is typed ``str | None`` because
    the API has historically been case-inconsistent across versions
    and we don't want construction to fail on a value we haven't seen
    before."""

    USER = "User"
    ORGANIZATION = "Organization"


class GitHubAppInstallation(BaseModel):
    """A GitHub App installation visible to the authenticated user."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    name: str | None = None
    # `installation-id` is the *GitHub-side* numeric installation ID, not
    # the HCP Terraform internal `id`. Modelled as int for type fidelity
    # against the API which returns it unquoted.
    installation_id: int | None = Field(default=None, alias="installation-id")
    icon_url: str | None = Field(default=None, alias="icon-url")
    installation_type: str | None = Field(default=None, alias="installation-type")
    installation_url: str | None = Field(default=None, alias="installation-url")


class GitHubAppInstallationListOptions(BaseModel):
    """List filters for GitHub App installations.

    The upstream API documents two filter parameters and does not
    document pagination on this endpoint.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Filter by the GitHub login/organization name (matches `name`).
    name: str | None = Field(default=None, alias="filter[name]")
    # Filter by the GitHub-side numeric installation ID (matches
    # `installation-id`), not HCP Terraform's internal `id`.
    installation_id: int | None = Field(default=None, alias="filter[installation_id]")
