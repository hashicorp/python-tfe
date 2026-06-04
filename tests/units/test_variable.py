# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the workspace Variables resource.

The headline cases here are regression tests for hashicorp/python-tfe#181:
``variables.list()`` infinite-looping on workspaces with >= 100 variables
because the ``/vars`` (and ``/all-vars``) endpoints are not paginated.
"""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import ERR_INVALID_WORKSPACE_ID
from pytfe.models.variable import Variable
from pytfe.resources._base import _Service
from pytfe.resources.variable import Variables


def _vars_payload(count: int) -> dict:
    """A /vars-style response: full set in one page, no meta.pagination."""
    return {
        "data": [
            {
                "id": f"var-{i}",
                "type": "vars",
                "attributes": {"key": f"key-{i}", "value": f"value-{i}"},
            }
            for i in range(count)
        ]
    }


class TestVariablesList:
    """Tests for Variables.list / list_all."""

    def setup_method(self):
        self.mock_transport = Mock(spec=HTTPTransport)
        self.variables = Variables(self.mock_transport)
        self.workspace_id = "ws-test123"

    def test_list_validations(self):
        with pytest.raises(ValueError, match=ERR_INVALID_WORKSPACE_ID):
            list(self.variables.list(""))
        with pytest.raises(ValueError, match=ERR_INVALID_WORKSPACE_ID):
            list(self.variables.list(None))

    def test_list_all_validations(self):
        with pytest.raises(ValueError, match=ERR_INVALID_WORKSPACE_ID):
            list(self.variables.list_all(""))
        with pytest.raises(ValueError, match=ERR_INVALID_WORKSPACE_ID):
            list(self.variables.list_all(None))

    def test_list_does_not_paginate_with_100_plus_variables(self):
        """Regression for #181: a workspace with >= 100 vars must not loop.

        The endpoint ignores page params and re-returns the full set, so the
        old pagination heuristic looped forever. We now issue exactly one
        request and return each variable once.
        """
        response = Mock()
        response.json.return_value = _vars_payload(150)
        self.mock_transport.request.return_value = response

        result = list(self.variables.list(self.workspace_id))

        # Exactly one request — no follow-up page fetches.
        self.mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/workspaces/{self.workspace_id}/vars",
            params={},
        )
        # All 150 variables, no duplication.
        assert len(result) == 150
        assert all(isinstance(v, Variable) for v in result)
        assert [v.id for v in result] == [f"var-{i}" for i in range(150)]

    def test_list_all_does_not_paginate_with_100_plus_variables(self):
        response = Mock()
        response.json.return_value = _vars_payload(120)
        self.mock_transport.request.return_value = response

        result = list(self.variables.list_all(self.workspace_id))

        self.mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/workspaces/{self.workspace_id}/all-vars",
            params={},
        )
        assert len(result) == 120
        assert [v.id for v in result] == [f"var-{i}" for i in range(120)]

    def test_list_exactly_100_variables(self):
        """The exactly-page-size boundary also looped under the old logic."""
        response = Mock()
        response.json.return_value = _vars_payload(100)
        self.mock_transport.request.return_value = response

        result = list(self.variables.list(self.workspace_id))

        self.mock_transport.request.assert_called_once()
        assert len(result) == 100

    def test_list_empty(self):
        response = Mock()
        response.json.return_value = {"data": []}
        self.mock_transport.request.return_value = response

        result = list(self.variables.list(self.workspace_id))

        self.mock_transport.request.assert_called_once()
        assert result == []


class TestListSafetyNet:
    """The generic _list safety net protects any non-paginated endpoint."""

    def test_full_page_without_metadata_is_treated_as_single_page(self):
        """A paginated (paginated=True) call that gets a full page with no
        meta.pagination must stop after one request rather than loop."""
        transport = Mock(spec=HTTPTransport)
        response = Mock()
        response.json.return_value = _vars_payload(100)  # full page, no meta
        transport.request.return_value = response

        service = _Service(transport)
        result = list(service._list("/api/v2/some/unpaginated", params={}))

        transport.request.assert_called_once()
        assert len(result) == 100
