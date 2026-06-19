# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the invoices resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidOrgError
from pytfe.models.invoice import Invoice
from pytfe.resources.invoice import Invoices


class TestInvoices:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Invoices(mock_transport)

    @staticmethod
    def _invoice(iid: str):
        return {
            "id": iid,
            "type": "billing-invoices",
            "attributes": {
                "created-at": "2021-01-01T19:00:38Z",
                "external-link": "https://pay.stripe.com/invoice/x/pdf",
                "number": "2F8CA1AE-0006",
                "paid": True,
                "status": "paid",
                "total": 21000,
            },
        }

    def test_list_cursor_paginates(self, service, mock_transport):
        page1 = Mock()
        page1.json.return_value = {
            "data": [self._invoice("in_1"), self._invoice("in_2")],
            "meta": {"continuation": "in_3"},
        }
        page2 = Mock()
        page2.json.return_value = {
            "data": [self._invoice("in_3")],
            "meta": {"continuation": None},
        }
        mock_transport.request.side_effect = [page1, page2]

        result = list(service.list("hashicorp"))

        assert [i.id for i in result] == ["in_1", "in_2", "in_3"]
        assert all(isinstance(i, Invoice) for i in result)
        assert mock_transport.request.call_count == 2
        first, second = mock_transport.request.call_args_list
        assert first.args == ("GET", "/api/v2/organizations/hashicorp/invoices")
        assert first.kwargs["params"] == {}
        # second page sends the continuation cursor
        assert second.kwargs["params"] == {"cursor": "in_3"}

    def test_list_single_page(self, service, mock_transport):
        resp = Mock()
        resp.json.return_value = {"data": [self._invoice("in_1")], "meta": {}}
        mock_transport.request.return_value = resp

        result = list(service.list("hashicorp"))

        assert [i.id for i in result] == ["in_1"]
        assert mock_transport.request.call_count == 1

    def test_list_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            list(service.list("bad org!"))

    def test_read_next(self, service, mock_transport):
        resp = Mock()
        resp.json.return_value = {
            "data": {
                "id": "in_upcoming_510DEB1F-0002",
                "type": "billing-invoices",
                "attributes": {
                    "number": "510DEB1F-0002",
                    "paid": False,
                    "status": "draft",
                    "total": 21000,
                },
            }
        }
        mock_transport.request.return_value = resp

        inv = service.read_next("hashicorp")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/organizations/hashicorp/invoices/next"
        )
        assert inv.id == "in_upcoming_510DEB1F-0002"
        assert inv.paid is False
        assert inv.status == "draft"
        assert inv.total == 21000

    def test_read_next_invalid_org(self, service):
        with pytest.raises(InvalidOrgError):
            service.read_next("bad org!")

    def test_read_next_no_upcoming_invoice(self, service, mock_transport):
        """A 200 with a null body (no upcoming invoice) returns None."""
        resp = Mock()
        resp.json.return_value = None
        mock_transport.request.return_value = resp
        assert service.read_next("hashicorp") is None

    def test_read_next_null_data(self, service, mock_transport):
        resp = Mock()
        resp.json.return_value = {"data": None}
        mock_transport.request.return_value = resp
        assert service.read_next("hashicorp") is None
