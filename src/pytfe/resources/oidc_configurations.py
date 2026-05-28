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
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> AWSOIDCConfiguration:
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: AWSOIDCConfigurationUpdateOptions,
    ) -> AWSOIDCConfiguration:
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
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
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> AzureOIDCConfiguration:
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: AzureOIDCConfigurationUpdateOptions,
    ) -> AzureOIDCConfiguration:
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
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
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> GCPOIDCConfiguration:
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: GCPOIDCConfigurationUpdateOptions,
    ) -> GCPOIDCConfiguration:
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
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
        return self._create(organization, options)

    def read(self, oidc_configuration_id: str) -> VaultOIDCConfiguration:
        return self._read(oidc_configuration_id)

    def update(
        self,
        oidc_configuration_id: str,
        options: VaultOIDCConfigurationUpdateOptions,
    ) -> VaultOIDCConfiguration:
        return self._update(oidc_configuration_id, options)

    def delete(self, oidc_configuration_id: str) -> None:
        self._delete(oidc_configuration_id)
