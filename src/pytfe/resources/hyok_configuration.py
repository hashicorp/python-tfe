# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""HCP Terraform HYOK (Hold Your Own Key) configurations.

Manages ``hyok-configurations`` resources, which let an organization encrypt
workspace state and plan data with a customer-controlled KMS key:

- ``POST   /api/v2/organizations/{org}/hyok-configurations``
- ``GET    /api/v2/organizations/{org}/hyok-configurations``
- ``GET    /api/v2/hyok-configurations/{id}``
- ``DELETE /api/v2/hyok-configurations/{id}``
- ``POST   /api/v2/hyok-configurations/{id}/actions/test``
- ``POST   /api/v2/hyok-configurations/{id}/actions/revoke``

A HYOK configuration references an OIDC configuration (``client.*_oidc_configurations``)
and an agent pool. Requires the HYOK entitlement on the organization.

API reference:
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/configurations
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidHYOKConfigurationIDError, InvalidOrgError
from ..models.hyok_configuration import (
    HYOKConfiguration,
    HYOKConfigurationCreateOptions,
    HYOKConfigurationListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


def _rel_data(relationships: dict[str, Any], name: str) -> dict[str, Any]:
    return (relationships.get(name) or {}).get("data") or {}


def _hyok_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> HYOKConfiguration:
    """Parse a JSON:API hyok-configurations resource into a HYOKConfiguration."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    rels = data.get("relationships") or {}
    if org := _rel_data(rels, "organization").get("id"):
        attrs["organization-id"] = org
    if pool := _rel_data(rels, "agent-pool").get("id"):
        attrs["agent-pool-id"] = pool
    oidc = _rel_data(rels, "oidc-configuration")
    if oidc.get("id"):
        attrs["oidc-configuration-id"] = oidc["id"]
    if oidc.get("type"):
        attrs["oidc-configuration-type"] = oidc["type"]
    return attach_jsonapi(HYOKConfiguration.model_validate(attrs), data, included)


class HYOKConfigurations(_Service):
    """Service for managing HYOK (Hold Your Own Key) configurations."""

    def list(
        self,
        organization: str,
        options: HYOKConfigurationListOptions | None = None,
    ) -> Iterator[HYOKConfiguration]:
        """List the HYOK configurations for an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Optional pagination controls, as a
                :class:`HYOKConfigurationListOptions`.

        Returns:
            A single-use ``Iterator[HYOKConfiguration]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import HYOKConfigurationListOptions
            >>> for config in client.hyok_configurations.list(
            ...     "my-org", HYOKConfigurationListOptions(page_size=20)
            ... ):
            ...     print(config.id, config.status)
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True, mode="json")
            if options
            else {}
        )
        path = f"/api/v2/organizations/{organization}/hyok-configurations"
        for item in self._list(path, params=params):
            yield _hyok_from(item)

    def create(
        self, organization: str, options: HYOKConfigurationCreateOptions
    ) -> HYOKConfiguration:
        """Create a HYOK configuration in an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: HYOK key, agent pool, and OIDC settings, as a
                :class:`HYOKConfigurationCreateOptions`.

        Returns:
            The :class:`HYOKConfiguration`.

        Raises:
            InvalidOrgError: If ``organization`` is not a valid organization name.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import HYOKConfigurationCreateOptions
            >>> from pytfe.models import OIDCConfigurationType
            >>> config = client.hyok_configurations.create(
            ...     "my-org",
            ...     HYOKConfigurationCreateOptions(
            ...         name="prod-key", kek_id="key1", agent_pool_id="apool-x",
            ...         oidc_configuration_id="voidc-x",
            ...         oidc_configuration_type=OIDCConfigurationType.VAULT,
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()
        attributes: dict[str, Any] = {"name": options.name, "kek-id": options.kek_id}
        if options.primary is not None:
            attributes["primary"] = options.primary
        if options.kms_options is not None:
            attributes["kms-options"] = options.kms_options.model_dump(
                by_alias=True, exclude_none=True
            )
        payload = {
            "data": {
                "type": "hyok-configurations",
                "attributes": attributes,
                "relationships": {
                    "organization": {
                        "data": {"type": "organizations", "id": organization}
                    },
                    "agent-pool": {
                        "data": {"type": "agent-pools", "id": options.agent_pool_id}
                    },
                    "oidc-configuration": {
                        "data": {
                            "type": options.oidc_configuration_type.value,
                            "id": options.oidc_configuration_id,
                        }
                    },
                },
            }
        }
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/hyok-configurations",
            json_body=payload,
        )
        body = r.json()
        return _hyok_from(body["data"], body.get("included"))

    def read(self, hyok_configuration_id: str) -> HYOKConfiguration:
        """Read a HYOK configuration by its ID.

        Args:
            hyok_configuration_id: The HYOK configuration ID (e.g.
                ``"hyokc-xxxxxxxx"``).

        Returns:
            The :class:`HYOKConfiguration`.

        Raises:
            InvalidHYOKConfigurationIDError: If ``hyok_configuration_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> config = client.hyok_configurations.read("hyokc-L4CxAJEEn8vEUEkj")
            >>> print(config.name)
        """
        if not valid_string_id(hyok_configuration_id):
            raise InvalidHYOKConfigurationIDError()
        r = self.t.request(
            "GET", f"/api/v2/hyok-configurations/{hyok_configuration_id}"
        )
        body = r.json()
        return _hyok_from(body["data"], body.get("included"))

    def delete(self, hyok_configuration_id: str) -> None:
        """Delete a HYOK configuration by its ID.

        The configuration must be **revoked** first — the API rejects deleting a
        configuration whose key may still be in use (call ``revoke`` and wait for
        ``status == revoked``).

        Args:
            hyok_configuration_id: The HYOK configuration ID (e.g.
                ``"hyokc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidHYOKConfigurationIDError: If ``hyok_configuration_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.hyok_configurations.delete("hyokc-L4CxAJEEn8vEUEkj")
        """
        if not valid_string_id(hyok_configuration_id):
            raise InvalidHYOKConfigurationIDError()
        self.t.request("DELETE", f"/api/v2/hyok-configurations/{hyok_configuration_id}")

    def revoke(self, hyok_configuration_id: str) -> None:
        """Revoke a HYOK configuration.

        Triggers an async revocation (HTTP 202); poll ``read(...).status`` until
        it reaches ``revoked``. A configuration must be revoked before it can be
        deleted.

        Args:
            hyok_configuration_id: The HYOK configuration ID (e.g.
                ``"hyokc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidHYOKConfigurationIDError: If ``hyok_configuration_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.hyok_configurations.revoke("hyokc-L4CxAJEEn8vEUEkj")
        """
        if not valid_string_id(hyok_configuration_id):
            raise InvalidHYOKConfigurationIDError()
        self.t.request(
            "POST",
            f"/api/v2/hyok-configurations/{hyok_configuration_id}/actions/revoke",
            json_body={},
        )

    def test(self, hyok_configuration_id: str) -> None:
        """Test a persisted HYOK configuration's key access.

        Triggers an async test (HTTP 202/204); poll ``read(...).status`` to
        observe the result (``testing`` -> ``available`` / ``test_failed``).

        Args:
            hyok_configuration_id: The HYOK configuration ID (e.g.
                ``"hyokc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidHYOKConfigurationIDError: If ``hyok_configuration_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.hyok_configurations.test("hyokc-L4CxAJEEn8vEUEkj")
        """
        if not valid_string_id(hyok_configuration_id):
            raise InvalidHYOKConfigurationIDError()
        self.t.request(
            "POST",
            f"/api/v2/hyok-configurations/{hyok_configuration_id}/actions/test",
            json_body={},
        )
