# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the subscriptions resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidOrgError, InvalidSubscriptionIDError
from pytfe.models.subscription import Subscription
from pytfe.resources.subscription import Subscriptions


class TestSubscriptions:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Subscriptions(mock_transport)

    @pytest.fixture
    def api_payload(self):
        return {
            "data": {
                "id": "sub-kyjptCZYXQ6amEVu",
                "type": "subscriptions",
                "attributes": {
                    "is-active": True,
                    "start-at": "2021-01-20T07:03:53.492Z",
                    "end-at": None,
                    "runs-ceiling": 1,
                    "agents-ceiling": 0,
                    "is-public-free-tier": True,
                    "policy-limit": None,
                },
                "relationships": {
                    "organization": {
                        "data": {"id": "hashicorp", "type": "organizations"}
                    },
                    "feature-set": {"data": {"id": "fs-1", "type": "feature-sets"}},
                    "billing-account": {"data": None},
                },
            },
            "included": [
                {"id": "fs-1", "type": "feature-sets", "attributes": {"name": "Free"}}
            ],
        }

    def test_read_for_organization(self, service, mock_transport, api_payload):
        mock_response = Mock()
        mock_response.json.return_value = api_payload
        mock_transport.request.return_value = mock_response

        sub = service.read_for_organization("hashicorp")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/organizations/hashicorp/subscription"
        )
        assert isinstance(sub, Subscription)
        assert sub.id == "sub-kyjptCZYXQ6amEVu"
        assert sub.is_active is True
        assert sub.runs_ceiling == 1
        assert sub.organization_id == "hashicorp"
        assert sub.feature_set_id == "fs-1"
        assert sub.billing_account_id is None
        # feature set is hydrated from `included`
        assert sub.related("feature-set")[0]["attributes"]["name"] == "Free"

    def test_read_for_organization_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            service.read_for_organization("bad org!")

    def test_read_by_id(self, service, mock_transport, api_payload):
        mock_response = Mock()
        mock_response.json.return_value = api_payload
        mock_transport.request.return_value = mock_response

        sub = service.read("sub-kyjptCZYXQ6amEVu")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/subscriptions/sub-kyjptCZYXQ6amEVu"
        )
        assert sub.id == "sub-kyjptCZYXQ6amEVu"

    def test_read_invalid_id(self, service):
        with pytest.raises(InvalidSubscriptionIDError):
            service.read("not valid!")
