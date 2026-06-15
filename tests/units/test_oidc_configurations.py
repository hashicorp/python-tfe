# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for HYOK OIDC configuration resources.

All four provider services share the same internal CRUD plumbing, so tests
focus on what's distinct per provider: payload `data.type`, the
hyphen-aliased attribute set, and the polymorphic URL that's the same for
every provider.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest

from pytfe.errors import InvalidOIDCConfigurationIDError, InvalidOrgError
from pytfe.models.oidc_configuration import (
    AWSOIDCConfigurationCreateOptions,
    AWSOIDCConfigurationUpdateOptions,
    AzureOIDCConfigurationCreateOptions,
    AzureOIDCConfigurationUpdateOptions,
    GCPOIDCConfigurationCreateOptions,
    VaultOIDCConfigurationCreateOptions,
    VaultOIDCConfigurationUpdateOptions,
)
from pytfe.resources.oidc_configurations import (
    AWSOIDCConfigurations,
    AzureOIDCConfigurations,
    GCPOIDCConfigurations,
    VaultOIDCConfigurations,
)


def _resp(body: Any) -> Mock:
    r = Mock()
    r.json.return_value = body
    return r


def _envelope(
    *,
    oidc_id: str,
    type_str: str,
    attributes: dict[str, Any],
    org_id: str = "my-org",
) -> dict[str, Any]:
    return {
        "data": {
            "id": oidc_id,
            "type": type_str,
            "attributes": attributes,
            "relationships": {
                "organization": {
                    "data": {"type": "organizations", "id": org_id},
                },
            },
        }
    }


# ---------------------------------------------------------------------------
# AWS
# ---------------------------------------------------------------------------


class TestAWSOIDCConfigurations:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = AWSOIDCConfigurations(self.transport)

    def test_create_payload_and_url(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-aws-1",
                type_str="aws-oidc-configurations",
                attributes={"role-arn": "arn:aws:iam::111:role/tfc"},
            )
        )

        result = self.service.create(
            "my-org",
            AWSOIDCConfigurationCreateOptions(role_arn="arn:aws:iam::111:role/tfc"),
        )

        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "POST"
        assert path == "/api/v2/organizations/my-org/oidc-configurations"
        assert body == {
            "data": {
                "type": "aws-oidc-configurations",
                "attributes": {"role-arn": "arn:aws:iam::111:role/tfc"},
            }
        }
        assert result.id == "oidc-aws-1"
        assert result.role_arn == "arn:aws:iam::111:role/tfc"
        assert result.organization is not None
        assert result.organization.id == "my-org"

    def test_read_url_and_parse(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-aws-1",
                type_str="aws-oidc-configurations",
                attributes={"role-arn": "arn:aws:iam::111:role/tfc"},
            )
        )
        result = self.service.read("oidc-aws-1")
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/oidc-configurations/oidc-aws-1"
        assert result.role_arn == "arn:aws:iam::111:role/tfc"

    def test_update_omits_none_fields(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-aws-1",
                type_str="aws-oidc-configurations",
                attributes={"role-arn": "arn:aws:iam::111:role/new"},
            )
        )
        self.service.update(
            "oidc-aws-1",
            AWSOIDCConfigurationUpdateOptions(role_arn="arn:aws:iam::111:role/new"),
        )
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/oidc-configurations/oidc-aws-1"
        assert body["data"]["type"] == "aws-oidc-configurations"
        assert body["data"]["attributes"] == {"role-arn": "arn:aws:iam::111:role/new"}

    def test_update_requires_role_arn(self) -> None:
        # AWS update has exactly one updatable field; constructing the
        # options without a role_arn is a local error
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            AWSOIDCConfigurationUpdateOptions()  # type: ignore[call-arg]

    def test_update_rejects_empty_role_arn(self) -> None:
        # Pydantic-level non-empty validator; defends against
        # AWSOIDCConfigurationUpdateOptions(role_arn="") sneaking through
        # to the server.
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            AWSOIDCConfigurationUpdateOptions(role_arn="")

    def test_create_rejects_empty_role_arn(self) -> None:
        # Same validator is shared between create and update options.
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            AWSOIDCConfigurationCreateOptions(role_arn="")

    def test_delete_url(self) -> None:
        self.transport.request.return_value = _resp({})
        self.service.delete("oidc-aws-1")
        method, path = self.transport.request.call_args.args
        assert method == "DELETE"
        assert path == "/api/v2/oidc-configurations/oidc-aws-1"

    def test_invalid_org_on_create(self) -> None:
        with pytest.raises(InvalidOrgError):
            self.service.create(
                "",
                AWSOIDCConfigurationCreateOptions(role_arn="arn:aws:iam::111:role/x"),
            )

    def test_invalid_id_on_read(self) -> None:
        with pytest.raises(InvalidOIDCConfigurationIDError):
            self.service.read("")

    def test_invalid_id_on_update(self) -> None:
        with pytest.raises(InvalidOIDCConfigurationIDError):
            self.service.update(
                "",
                AWSOIDCConfigurationUpdateOptions(role_arn="arn:aws:iam::111:role/x"),
            )

    def test_invalid_id_on_delete(self) -> None:
        with pytest.raises(InvalidOIDCConfigurationIDError):
            self.service.delete("")


# ---------------------------------------------------------------------------
# Azure
# ---------------------------------------------------------------------------


class TestAzureOIDCConfigurations:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = AzureOIDCConfigurations(self.transport)

    def test_create_payload(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-azure-1",
                type_str="azure-oidc-configurations",
                attributes={
                    "client-id": "client-uuid",
                    "subscription-id": "sub-uuid",
                    "tenant-id": "tenant-uuid",
                },
            )
        )
        result = self.service.create(
            "my-org",
            AzureOIDCConfigurationCreateOptions(
                client_id="client-uuid",
                subscription_id="sub-uuid",
                tenant_id="tenant-uuid",
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body == {
            "data": {
                "type": "azure-oidc-configurations",
                "attributes": {
                    "client-id": "client-uuid",
                    "subscription-id": "sub-uuid",
                    "tenant-id": "tenant-uuid",
                },
            }
        }
        assert result.client_id == "client-uuid"
        assert result.subscription_id == "sub-uuid"
        assert result.tenant_id == "tenant-uuid"

    def test_update_partial_payload(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-azure-1",
                type_str="azure-oidc-configurations",
                attributes={
                    "client-id": "new-client-uuid",
                    "subscription-id": "sub-uuid",
                    "tenant-id": "tenant-uuid",
                },
            )
        )
        self.service.update(
            "oidc-azure-1",
            AzureOIDCConfigurationUpdateOptions(client_id="new-client-uuid"),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        # Only client_id was set; subscription/tenant must be omitted.
        assert body["data"]["attributes"] == {"client-id": "new-client-uuid"}


# ---------------------------------------------------------------------------
# GCP
# ---------------------------------------------------------------------------


class TestGCPOIDCConfigurations:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = GCPOIDCConfigurations(self.transport)

    def test_create_payload(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-gcp-1",
                type_str="gcp-oidc-configurations",
                attributes={
                    "service-account-email": "sa@p.iam.gserviceaccount.com",
                    "project-number": "123456789",
                    "workload-provider-name": "projects/123/locations/global/workloadIdentityPools/p/providers/x",
                },
            )
        )
        result = self.service.create(
            "my-org",
            GCPOIDCConfigurationCreateOptions(
                service_account_email="sa@p.iam.gserviceaccount.com",
                project_number="123456789",
                workload_provider_name="projects/123/locations/global/workloadIdentityPools/p/providers/x",
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["type"] == "gcp-oidc-configurations"
        assert body["data"]["attributes"] == {
            "service-account-email": "sa@p.iam.gserviceaccount.com",
            "project-number": "123456789",
            "workload-provider-name": "projects/123/locations/global/workloadIdentityPools/p/providers/x",
        }
        assert result.service_account_email == "sa@p.iam.gserviceaccount.com"
        assert result.project_number == "123456789"
        assert (
            result.workload_provider_name
            == "projects/123/locations/global/workloadIdentityPools/p/providers/x"
        )


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------


class TestVaultOIDCConfigurations:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = VaultOIDCConfigurations(self.transport)

    def test_create_payload_uses_wire_aliases(self) -> None:
        # Vault has the most non-obvious mappings:
        #   role_name        -> "role"
        #   jwt_auth_path    -> "auth-path"
        #   tls_ca_certificate -> "encoded-cacert"
        # If any of these regress, federation fails silently on the cluster
        # side, so test the exact wire shape.
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-vault-1",
                type_str="vault-oidc-configurations",
                attributes={
                    "address": "https://vault.example.com",
                    "role": "terraform",
                    "namespace": "admin",
                    "auth-path": "jwt",
                    "encoded-cacert": "-----BEGIN CERT-----",
                },
            )
        )
        result = self.service.create(
            "my-org",
            VaultOIDCConfigurationCreateOptions(
                address="https://vault.example.com",
                role_name="terraform",
                namespace="admin",
                jwt_auth_path="jwt",
                tls_ca_certificate="-----BEGIN CERT-----",
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["type"] == "vault-oidc-configurations"
        assert body["data"]["attributes"] == {
            "address": "https://vault.example.com",
            "role": "terraform",
            "namespace": "admin",
            "auth-path": "jwt",
            "encoded-cacert": "-----BEGIN CERT-----",
        }
        # Parsed model uses Python field names.
        assert result.role_name == "terraform"
        assert result.jwt_auth_path == "jwt"
        assert result.tls_ca_certificate == "-----BEGIN CERT-----"

    def test_create_minimum_payload(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-vault-1",
                type_str="vault-oidc-configurations",
                attributes={
                    "address": "https://vault.example.com",
                    "role": "tf",
                },
            )
        )
        self.service.create(
            "my-org",
            VaultOIDCConfigurationCreateOptions(
                address="https://vault.example.com", role_name="tf"
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {
            "address": "https://vault.example.com",
            "role": "tf",
        }
        # namespace/auth-path/encoded-cacert omitted, not sent as null.
        assert "namespace" not in body["data"]["attributes"]
        assert "auth-path" not in body["data"]["attributes"]
        assert "encoded-cacert" not in body["data"]["attributes"]

    def test_update_namespace_only(self) -> None:
        self.transport.request.return_value = _resp(
            _envelope(
                oidc_id="oidc-vault-1",
                type_str="vault-oidc-configurations",
                attributes={
                    "address": "https://vault.example.com",
                    "role": "tf",
                    "namespace": "production",
                },
            )
        )
        self.service.update(
            "oidc-vault-1",
            VaultOIDCConfigurationUpdateOptions(namespace="production"),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"namespace": "production"}


# ---------------------------------------------------------------------------
# Cross-provider: confirm all four hit the same polymorphic URLs
# ---------------------------------------------------------------------------


class TestOIDCPolymorphicURLs:
    """The HCP API uses one URL for create and one URL pattern for
    read/update/delete across all four providers — only `data.type`
    distinguishes them. Regress-protect that all four services agree."""

    @pytest.mark.parametrize(
        "service_cls,options_factory,expected_type",
        [
            (
                AWSOIDCConfigurations,
                lambda: AWSOIDCConfigurationCreateOptions(
                    role_arn="arn:aws:iam::1:role/r"
                ),
                "aws-oidc-configurations",
            ),
            (
                AzureOIDCConfigurations,
                lambda: AzureOIDCConfigurationCreateOptions(
                    client_id="c", subscription_id="s", tenant_id="t"
                ),
                "azure-oidc-configurations",
            ),
            (
                GCPOIDCConfigurations,
                lambda: GCPOIDCConfigurationCreateOptions(
                    service_account_email="sa@p",
                    project_number="1",
                    workload_provider_name="w",
                ),
                "gcp-oidc-configurations",
            ),
            (
                VaultOIDCConfigurations,
                lambda: VaultOIDCConfigurationCreateOptions(
                    address="https://v", role_name="r"
                ),
                "vault-oidc-configurations",
            ),
        ],
    )
    def test_create_url_is_polymorphic(
        self,
        service_cls: type,
        options_factory: Any,
        expected_type: str,
    ) -> None:
        transport = Mock()
        transport.request.return_value = _resp(
            _envelope(
                oidc_id="x", type_str=expected_type, attributes={}, org_id="my-org"
            )
        )
        service = service_cls(transport)
        service.create("my-org", options_factory())

        _, path = transport.request.call_args.args
        body = transport.request.call_args.kwargs["json_body"]
        assert path == "/api/v2/organizations/my-org/oidc-configurations"
        assert body["data"]["type"] == expected_type
