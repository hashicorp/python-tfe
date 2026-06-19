# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""HCP Terraform HYOK OIDC configuration resources.

All four provider types (AWS, Azure, GCP, Vault) share a single HCP endpoint
group:

- ``POST   /api/v2/organizations/{org}/oidc-configurations``
- ``GET    /api/v2/oidc-configurations/{id}``
- ``PATCH  /api/v2/oidc-configurations/{id}``
- ``DELETE /api/v2/oidc-configurations/{id}``

Provider type is encoded in the JSON:API ``data.type`` string
(``aws-oidc-configurations``, ``azure-oidc-configurations``,
``gcp-oidc-configurations``, ``vault-oidc-configurations``). Each provider
gets its own service class for ergonomic IDE autocomplete and typed
options/response models; internally they share build/parse helpers.

These resources require Hold Your Own Key (HYOK) entitlement on the
organization. Calls against an org without HYOK will return ``404`` or
``403`` from the server.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ..errors import InvalidOIDCConfigurationIDError, InvalidOrgError
from ..models.oidc_configuration import (
    AWSOIDCConfiguration,
    AWSOIDCConfigurationCreateOptions,
    AWSOIDCConfigurationUpdateOptions,
    AzureOIDCConfiguration,
    AzureOIDCConfigurationCreateOptions,
    AzureOIDCConfigurationUpdateOptions,
    GCPOIDCConfiguration,
    GCPOIDCConfigurationCreateOptions,
    GCPOIDCConfigurationUpdateOptions,
    VaultOIDCConfiguration,
    VaultOIDCConfigurationCreateOptions,
    VaultOIDCConfigurationUpdateOptions,
)
from ..models.organization import Organization
from ..utils import valid_string_id
from ._base import _Service

_AWS_TYPE = "aws-oidc-configurations"
_AZURE_TYPE = "azure-oidc-configurations"
_GCP_TYPE = "gcp-oidc-configurations"
_VAULT_TYPE = "vault-oidc-configurations"


# Pydantic config / response models share BaseModel — pick typevars so the
# generic helpers below can be statically typed without losing the concrete
# provider type at the call site.
R = TypeVar("R", bound=BaseModel)  # response model
T = TypeVar("T", bound=BaseModel)  # local parse() typevar


def _build_payload(type_str: str, options: BaseModel) -> dict[str, Any]:
    """Build a JSON:API request body for create/update.

    Emits the wire-aliased keys (e.g. ``role-arn`` not ``role_arn``) and
    omits ``None`` fields so partial updates don't clobber unset values.
    """
    attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
    return {"data": {"type": type_str, "attributes": attrs}}


def _parse_response(data: dict[str, Any], model: type[T]) -> T:
    """Parse a JSON:API ``data`` block into a typed response model.

    The model's own field aliases handle attribute name mapping; we only
    need to lift the ``organization`` relationship into the parsed object
    so callers can reach ``config.organization.id`` without traversing the
    JSON:API envelope themselves.
    """
    attrs = data.get("attributes") or {}
    relationships = data.get("relationships") or {}

    parsed = model.model_validate({"id": data.get("id"), **attrs})

    org_data = (relationships.get("organization") or {}).get("data")
    if org_data and org_data.get("id") and hasattr(parsed, "organization"):
        parsed.organization = Organization.model_construct(id=org_data["id"])

    return parsed


class _OIDCConfigurationsBase(_Service, Generic[R]):
    """Internal: shared CRUD plumbing for all four provider services.

    Subclasses set ``_type`` (wire-format JSON:API type string) and the
    response model class; the four public methods are otherwise identical.

    Parametrising on the response model means each subclass's
    ``_create/_read/_update`` returns its concrete provider type, not
    ``Any`` — so callers and mypy both see the right shape.
    """

    _type: str
    _response_model: type[R]

    def _create(self, organization: str, options: BaseModel) -> R:
        if not valid_string_id(organization):
            raise InvalidOrgError()
        body = _build_payload(self._type, options)
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/oidc-configurations",
            json_body=body,
        )
        return _parse_response(r.json()["data"], self._response_model)

    def _read(self, oidc_configuration_id: str) -> R:
        if not valid_string_id(oidc_configuration_id):
            raise InvalidOIDCConfigurationIDError()
        r = self.t.request(
            "GET", f"/api/v2/oidc-configurations/{oidc_configuration_id}"
        )
        return _parse_response(r.json()["data"], self._response_model)

    def _update(self, oidc_configuration_id: str, options: BaseModel) -> R:
        if not valid_string_id(oidc_configuration_id):
            raise InvalidOIDCConfigurationIDError()
        body = _build_payload(self._type, options)
        r = self.t.request(
            "PATCH",
            f"/api/v2/oidc-configurations/{oidc_configuration_id}",
            json_body=body,
        )
        return _parse_response(r.json()["data"], self._response_model)

    def _delete(self, oidc_configuration_id: str) -> None:
        if not valid_string_id(oidc_configuration_id):
            raise InvalidOIDCConfigurationIDError()
        self.t.request("DELETE", f"/api/v2/oidc-configurations/{oidc_configuration_id}")


class AWSOIDCConfigurations(_OIDCConfigurationsBase[AWSOIDCConfiguration]):
    """Manage AWS OIDC configurations.

    Stores the IAM role ARN that HCP Terraform should assume via OIDC
    federation. Does not create the AWS-side IAM role or trust policy.
    """

    _type = _AWS_TYPE
    _response_model = AWSOIDCConfiguration

    def create(
        self, organization: str, options: AWSOIDCConfigurationCreateOptions
    ) -> AWSOIDCConfiguration:
        """Create an AWS OIDC configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The AWS configuration attributes, as a
                :class:`AWSOIDCConfigurationCreateOptions`.

        Returns:
            The created :class:`AWSOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AWSOIDCConfigurationCreateOptions
            >>> config = client.aws_oidc_configurations.create(
            ...     "my-org",
            ...     AWSOIDCConfigurationCreateOptions(
            ...         role_arn="arn:aws:iam::111122223333:role/tfc"
            ...     ),
            ... )
        """
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> AWSOIDCConfiguration:
        """Read an AWS OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            The :class:`AWSOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.aws_oidc_configurations.read("oidc-aws-1")
            >>> print(config.id)
        """
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: AWSOIDCConfigurationUpdateOptions,
    ) -> AWSOIDCConfiguration:
        """Update an AWS OIDC configuration.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).
            options: The changed AWS attributes, as a
                :class:`AWSOIDCConfigurationUpdateOptions`.

        Returns:
            The updated :class:`AWSOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AWSOIDCConfigurationUpdateOptions
            >>> config = client.aws_oidc_configurations.update(
            ...     "oidc-aws-1",
            ...     AWSOIDCConfigurationUpdateOptions(
            ...         role_arn="arn:aws:iam::111122223333:role/tfc-updated"
            ...     ),
            ... )
        """
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
        """Delete an AWS OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.aws_oidc_configurations.delete("oidc-aws-1")
        """
        self._delete(oidc_configuration_id)


class AzureOIDCConfigurations(_OIDCConfigurationsBase[AzureOIDCConfiguration]):
    """Manage Azure OIDC configurations.

    Stores the Azure AD application/subscription/tenant identifiers HCP
    Terraform federates against. Does not create the Azure-side app
    registration, service principal, or federated credential.
    """

    _type = _AZURE_TYPE
    _response_model = AzureOIDCConfiguration

    def create(
        self, organization: str, options: AzureOIDCConfigurationCreateOptions
    ) -> AzureOIDCConfiguration:
        """Create an Azure OIDC configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The Azure configuration attributes, as a
                :class:`AzureOIDCConfigurationCreateOptions`.

        Returns:
            The created :class:`AzureOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AzureOIDCConfigurationCreateOptions
            >>> config = client.azure_oidc_configurations.create(
            ...     "my-org",
            ...     AzureOIDCConfigurationCreateOptions(
            ...         client_id="client-uuid",
            ...         subscription_id="sub-uuid",
            ...         tenant_id="tenant-uuid",
            ...     ),
            ... )
        """
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> AzureOIDCConfiguration:
        """Read an Azure OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            The :class:`AzureOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.azure_oidc_configurations.read("oidc-azure-1")
            >>> print(config.id)
        """
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: AzureOIDCConfigurationUpdateOptions,
    ) -> AzureOIDCConfiguration:
        """Update an Azure OIDC configuration.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).
            options: The changed Azure attributes, as a
                :class:`AzureOIDCConfigurationUpdateOptions`.

        Returns:
            The updated :class:`AzureOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import AzureOIDCConfigurationUpdateOptions
            >>> config = client.azure_oidc_configurations.update(
            ...     "oidc-azure-1",
            ...     AzureOIDCConfigurationUpdateOptions(client_id="new-client-uuid"),
            ... )
        """
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
        """Delete an Azure OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.azure_oidc_configurations.delete("oidc-azure-1")
        """
        self._delete(oidc_configuration_id)


class GCPOIDCConfigurations(_OIDCConfigurationsBase[GCPOIDCConfiguration]):
    """Manage GCP OIDC configurations.

    Stores the GCP service account email and Workload Identity Federation
    provider that HCP Terraform impersonates. Does not create the GCP-side
    workload identity pool, provider, or service-account IAM bindings.
    """

    _type = _GCP_TYPE
    _response_model = GCPOIDCConfiguration

    def create(
        self, organization: str, options: GCPOIDCConfigurationCreateOptions
    ) -> GCPOIDCConfiguration:
        """Create a GCP OIDC configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The GCP configuration attributes, as a
                :class:`GCPOIDCConfigurationCreateOptions`.

        Returns:
            The created :class:`GCPOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import GCPOIDCConfigurationCreateOptions
            >>> config = client.gcp_oidc_configurations.create(
            ...     "my-org",
            ...     GCPOIDCConfigurationCreateOptions(
            ...         service_account_email="tfc@project.iam.gserviceaccount.com",
            ...         project_number="123456789012",
            ...         workload_provider_name="projects/123/locations/global",
            ...     ),
            ... )
        """
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> GCPOIDCConfiguration:
        """Read a GCP OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            The :class:`GCPOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.gcp_oidc_configurations.read("oidc-gcp-1")
            >>> print(config.id)
        """
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: GCPOIDCConfigurationUpdateOptions,
    ) -> GCPOIDCConfiguration:
        """Update a GCP OIDC configuration.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).
            options: The changed GCP attributes, as a
                :class:`GCPOIDCConfigurationUpdateOptions`.

        Returns:
            The updated :class:`GCPOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import GCPOIDCConfigurationUpdateOptions
            >>> config = client.gcp_oidc_configurations.update(
            ...     "oidc-gcp-1",
            ...     GCPOIDCConfigurationUpdateOptions(
            ...         service_account_email="new@project.iam.gserviceaccount.com"
            ...     ),
            ... )
        """
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
        """Delete a GCP OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.gcp_oidc_configurations.delete("oidc-gcp-1")
        """
        self._delete(oidc_configuration_id)


class VaultOIDCConfigurations(_OIDCConfigurationsBase[VaultOIDCConfiguration]):
    """Manage Vault OIDC configurations.

    Stores the Vault address, JWT auth path, and role HCP Terraform
    authenticates against. Does not create the Vault-side JWT auth method,
    role, or policies.
    """

    _type = _VAULT_TYPE
    _response_model = VaultOIDCConfiguration

    def create(
        self, organization: str, options: VaultOIDCConfigurationCreateOptions
    ) -> VaultOIDCConfiguration:
        """Create a Vault OIDC configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The Vault configuration attributes, as a
                :class:`VaultOIDCConfigurationCreateOptions`.

        Returns:
            The created :class:`VaultOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VaultOIDCConfigurationCreateOptions
            >>> config = client.vault_oidc_configurations.create(
            ...     "my-org",
            ...     VaultOIDCConfigurationCreateOptions(
            ...         address="https://vault.example.com", role_name="tfc"
            ...     ),
            ... )
        """
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> VaultOIDCConfiguration:
        """Read a Vault OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            The :class:`VaultOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.vault_oidc_configurations.read("oidc-vault-1")
            >>> print(config.id)
        """
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: VaultOIDCConfigurationUpdateOptions,
    ) -> VaultOIDCConfiguration:
        """Update a Vault OIDC configuration.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).
            options: The changed Vault attributes, as a
                :class:`VaultOIDCConfigurationUpdateOptions`.

        Returns:
            The updated :class:`VaultOIDCConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import VaultOIDCConfigurationUpdateOptions
            >>> config = client.vault_oidc_configurations.update(
            ...     "oidc-vault-1",
            ...     VaultOIDCConfigurationUpdateOptions(role_name="tfc-updated"),
            ... )
        """
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
        """Delete a Vault OIDC configuration by its ID.

        Args:
            oidc_configuration_id: The OIDC configuration ID
                (e.g. ``"oidc-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.vault_oidc_configurations.delete("oidc-vault-1")
        """
        self._delete(oidc_configuration_id)
