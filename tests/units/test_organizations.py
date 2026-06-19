# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.models import (
    Organization,
    OrganizationIncludeOpt,
    OrganizationReadOptions,
)
from pytfe.resources.organizations import Organizations


class TestOrganizationsRead:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Organizations(mock_transport)

    @staticmethod
    def _org_data(name: str = "acme") -> dict:
        return {
            "id": name,
            "type": "organizations",
            "attributes": {"name": name, "email": "owner@acme.test"},
            "relationships": {
                "subscription": {"data": {"id": "sub-1", "type": "subscriptions"}}
            },
        }

    def test_read_no_options_unchanged(self, service, mock_transport):
        """read() without options sends empty params and captures no included."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": self._org_data()}
        mock_transport.request.return_value = mock_response

        org = service.read("acme")

        assert mock_transport.request.call_args[1]["params"] == {}
        assert isinstance(org, Organization)
        assert org.has_included is False
        assert org.included == []

    def test_read_with_include_subscription_captures_included(
        self, service, mock_transport
    ):
        """read(include=[subscription]) sends the param and captures the raw
        included body on the escape hatch (subscription is not a typed field)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": self._org_data(),
            "included": [
                {
                    "id": "sub-1",
                    "type": "subscriptions",
                    "attributes": {"plan": "plus"},
                }
            ],
        }
        mock_transport.request.return_value = mock_response

        org = service.read(
            "acme",
            OrganizationReadOptions(
                include=[OrganizationIncludeOpt.ORGANIZATION_SUBSCRIPTION]
            ),
        )

        assert mock_transport.request.call_args[1]["params"] == {
            "include": "subscription"
        }
        assert org.has_included is True
        sub = org.related("subscription")
        assert sub[0]["attributes"]["plan"] == "plus"
        # non-breaking: escape hatch never leaks into model_dump()
        assert "included" not in org.model_dump()


class TestOrganizationsEntitlements:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Organizations(mock_transport)

    def test_read_entitlements_surfaces_all_flags(self, service, mock_transport):
        """Entitlements parsing keeps every flag — modelled fields stay typed and
        anything else (e.g. the integer ``*-limit`` flags) is retained in
        ``model_extra`` instead of being silently dropped."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "entset-1",
                "type": "entitlement-sets",
                "attributes": {
                    # existing modelled flags (hyphenated on the wire)
                    "agents": True,
                    "audit-logging": False,
                    "cost-estimation": True,
                    # newly modelled flags
                    "hyok": True,
                    "stacks": True,
                    "terraform-actions": True,
                    "change-requests": False,
                    # unmodelled flags -> must be retained in model_extra
                    "self-serve-billing": True,
                    "policy-limit": 5,
                    "user-limit": None,
                },
            }
        }
        mock_transport.request.return_value = mock_response

        ent = service.read_entitlements("acme")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/organizations/acme/entitlement-set"
        )
        # existing typed fields (hyphen -> underscore) unchanged
        assert ent.agents is True
        assert ent.audit_logging is False
        assert ent.cost_estimation is True
        # newly typed fields
        assert ent.hyok is True
        assert ent.stacks is True
        assert ent.terraform_actions is True
        assert ent.change_requests is False
        # previously-dropped flags now retained in model_extra
        extra = ent.model_extra or {}
        assert extra.get("self_serve_billing") is True
        assert extra.get("policy_limit") == 5
        assert "user_limit" in extra
        # and they survive a round-trip dump
        dumped = ent.model_dump()
        assert dumped["hyok"] is True
        assert dumped["policy_limit"] == 5

    def test_read_entitlements_invalid_org(self, service):
        with pytest.raises(ValueError):
            service.read_entitlements("bad org!")
