# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the HYOK configurations resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidAgentPoolIDError,
    InvalidHYOKConfigurationIDError,
    InvalidOIDCConfigurationIDError,
    InvalidOrgError,
    RequiredKEKIDError,
    RequiredNameError,
)
from pytfe.models.hyok_configuration import (
    HYOKConfiguration,
    HYOKConfigurationCreateOptions,
    HYOKConfigurationStatus,
    HYOKKMSOptions,
    OIDCConfigurationType,
)
from pytfe.resources.hyok_configuration import HYOKConfigurations


class TestHYOKConfigurations:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return HYOKConfigurations(mock_transport)

    @pytest.fixture
    def api_data(self):
        return {
            "id": "hyokc-L4CxAJEEn8vEUEkj",
            "type": "hyok-configurations",
            "attributes": {
                "kek-id": "key1",
                "kms-options": {},
                "name": "my-key-name",
                "primary": False,
                "status": "untested",
                "error": None,
            },
            "relationships": {
                "organization": {
                    "data": {"id": "my-hyok-org", "type": "organizations"}
                },
                "oidc-configuration": {
                    "data": {"id": "voidc-x", "type": "vault-oidc-configurations"}
                },
                "agent-pool": {"data": {"id": "apool-x", "type": "agent-pools"}},
                "hyok-customer-key-versions": {"data": []},
            },
        }

    # ── Options / model ───────────────────────────────────────────────────────

    def test_create_options_validation(self):
        base = {
            "kek_id": "key1",
            "agent_pool_id": "apool-1",
            "oidc_configuration_id": "voidc-1",
            "oidc_configuration_type": OIDCConfigurationType.VAULT,
        }
        with pytest.raises(RequiredNameError):
            HYOKConfigurationCreateOptions(name="", **base)
        with pytest.raises(RequiredKEKIDError):
            HYOKConfigurationCreateOptions(
                name="n",
                kek_id="",
                agent_pool_id="apool-1",
                oidc_configuration_id="voidc-1",
                oidc_configuration_type=OIDCConfigurationType.VAULT,
            )
        with pytest.raises(InvalidAgentPoolIDError):
            HYOKConfigurationCreateOptions(
                name="n",
                kek_id="k",
                agent_pool_id="bad id!",
                oidc_configuration_id="voidc-1",
                oidc_configuration_type=OIDCConfigurationType.VAULT,
            )
        with pytest.raises(InvalidOIDCConfigurationIDError):
            HYOKConfigurationCreateOptions(
                name="n",
                kek_id="k",
                agent_pool_id="apool-1",
                oidc_configuration_id="",
                oidc_configuration_type=OIDCConfigurationType.VAULT,
            )

    def test_model_parses_flat_relationship_ids(self, service, api_data):
        h = service  # noqa: F841 — use the module parser via read below
        from pytfe.resources.hyok_configuration import _hyok_from

        result = _hyok_from(api_data)
        assert isinstance(result, HYOKConfiguration)
        assert result.status == HYOKConfigurationStatus.UNTESTED
        assert result.organization_id == "my-hyok-org"
        assert result.agent_pool_id == "apool-x"
        assert result.oidc_configuration_id == "voidc-x"
        assert result.oidc_configuration_type == "vault-oidc-configurations"
        assert result.related("oidc-configuration") == [
            {"id": "voidc-x", "type": "vault-oidc-configurations"}
        ]

    # ── list ──────────────────────────────────────────────────────────────────

    def test_list_success(self, service, api_data):
        service._list = Mock(return_value=[api_data])

        result = list(service.list("my-hyok-org"))

        service._list.assert_called_once_with(
            "/api/v2/organizations/my-hyok-org/hyok-configurations", params={}
        )
        assert len(result) == 1
        assert result[0].id == "hyokc-L4CxAJEEn8vEUEkj"

    def test_list_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            list(service.list("bad org!"))

    # ── create ────────────────────────────────────────────────────────────────

    def test_create_success(self, service, mock_transport, api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": api_data}
        mock_transport.request.return_value = mock_response

        opts = HYOKConfigurationCreateOptions(
            name="my-key-name",
            kek_id="key1",
            agent_pool_id="apool-x",
            oidc_configuration_id="voidc-x",
            oidc_configuration_type=OIDCConfigurationType.VAULT,
            primary=False,
            kms_options=HYOKKMSOptions(key_region="us-east-1"),
        )
        result = service.create("my-hyok-org", opts)

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/organizations/my-hyok-org/hyok-configurations",
            json_body={
                "data": {
                    "type": "hyok-configurations",
                    "attributes": {
                        "name": "my-key-name",
                        "kek-id": "key1",
                        "primary": False,
                        "kms-options": {"key_region": "us-east-1"},
                    },
                    "relationships": {
                        "organization": {
                            "data": {"type": "organizations", "id": "my-hyok-org"}
                        },
                        "agent-pool": {
                            "data": {"type": "agent-pools", "id": "apool-x"}
                        },
                        "oidc-configuration": {
                            "data": {
                                "type": "vault-oidc-configurations",
                                "id": "voidc-x",
                            }
                        },
                    },
                }
            },
        )
        assert isinstance(result, HYOKConfiguration)
        assert result.id == "hyokc-L4CxAJEEn8vEUEkj"

    def test_create_invalid_org(self, service):
        opts = HYOKConfigurationCreateOptions(
            name="n",
            kek_id="k",
            agent_pool_id="apool-1",
            oidc_configuration_id="voidc-1",
            oidc_configuration_type=OIDCConfigurationType.AWS,
        )
        with pytest.raises(InvalidOrgError):
            service.create("bad org!", opts)

    # ── read / delete / test ──────────────────────────────────────────────────

    def test_read_success(self, service, mock_transport, api_data):
        mock_response = Mock()
        mock_response.json.return_value = {"data": api_data}
        mock_transport.request.return_value = mock_response

        result = service.read("hyokc-L4CxAJEEn8vEUEkj")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/hyok-configurations/hyokc-L4CxAJEEn8vEUEkj"
        )
        assert result.name == "my-key-name"

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidHYOKConfigurationIDError):
            service.read("bad id!")

    def test_delete_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()
        service.delete("hyokc-L4CxAJEEn8vEUEkj")
        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/hyok-configurations/hyokc-L4CxAJEEn8vEUEkj"
        )

    def test_delete_invalid_id(self, service):
        with pytest.raises(InvalidHYOKConfigurationIDError):
            service.delete("")

    def test_test_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()
        service.test("hyokc-L4CxAJEEn8vEUEkj")
        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/hyok-configurations/hyokc-L4CxAJEEn8vEUEkj/actions/test",
            json_body={},
        )

    def test_test_invalid_id(self, service):
        with pytest.raises(InvalidHYOKConfigurationIDError):
            service.test("")

    def test_revoke_success(self, service, mock_transport):
        mock_transport.request.return_value = Mock()
        service.revoke("hyokc-L4CxAJEEn8vEUEkj")
        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/hyok-configurations/hyokc-L4CxAJEEn8vEUEkj/actions/revoke",
            json_body={},
        )

    def test_revoke_invalid_id(self, service):
        with pytest.raises(InvalidHYOKConfigurationIDError):
            service.revoke("")
