# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Read an organization's HCP Terraform subscription.

- ``GET /api/v2/organizations/{org}/subscription`` — the org's subscription
- ``GET /api/v2/subscriptions/{id}`` — a subscription by id

The subscription links to a feature set (pass nothing special; the feature set
is returned in the document's ``included`` array and reachable via
``subscription.related("feature-set")``). Subscriptions are HCP Terraform only.

API reference:
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/subscriptions
"""

from __future__ import annotations

from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidOrgError, InvalidSubscriptionIDError
from ..models.subscription import Subscription
from ..utils import valid_string_id
from ._base import _Service


def _rel_id(relationships: dict[str, Any], name: str) -> str | None:
    data = (relationships.get(name) or {}).get("data")
    return data.get("id") if isinstance(data, dict) else None


def _subscription_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> Subscription:
    """Parse a JSON:API subscriptions resource into a Subscription."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    rels = data.get("relationships") or {}
    if org := _rel_id(rels, "organization"):
        attrs["organization-id"] = org
    if fs := _rel_id(rels, "feature-set"):
        attrs["feature-set-id"] = fs
    if ba := _rel_id(rels, "billing-account"):
        attrs["billing-account-id"] = ba
    return attach_jsonapi(Subscription.model_validate(attrs), data, included)


class Subscriptions(_Service):
    """Service for reading organization subscriptions (HCP Terraform only)."""

    def read_for_organization(self, organization: str) -> Subscription:
        """Read the subscription for an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`Subscription`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> subscription = client.subscriptions.read_for_organization("my-org")
            >>> print(subscription.is_active)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        r = self.t.request("GET", f"/api/v2/organizations/{organization}/subscription")
        body = r.json()
        return _subscription_from(body["data"], body.get("included"))

    def read(self, subscription_id: str) -> Subscription:
        """Read a subscription by its ID.

        Args:
            subscription_id: The subscription ID (e.g. ``"sub-xxxxxxxx"``).

        Returns:
            The :class:`Subscription`.

        Raises:
            InvalidSubscriptionIDError: If ``subscription_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> subscription = client.subscriptions.read("sub-kyjptCZYXQ6amEVu")
            >>> print(subscription.runs_ceiling)
        """
        if not valid_string_id(subscription_id):
            raise InvalidSubscriptionIDError()
        r = self.t.request("GET", f"/api/v2/subscriptions/{subscription_id}")
        body = r.json()
        return _subscription_from(body["data"], body.get("included"))
