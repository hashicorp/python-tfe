# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from unittest.mock import Mock

import pytest

from pytfe.models.variable import CategoryType, Variable
from pytfe.resources.variable import Variables


class TestVariables:
    def setup_method(self):
        self.mock_transport = Mock()
        self.variables_service = Variables(self.mock_transport)
        self.workspace_id = "ws-test123"

    def _mock_response(self, count: int) -> Mock:
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": f"var-{index}",
                    "type": "vars",
                    "attributes": {
                        "key": f"key_{index}",
                        "value": f"value_{index}",
                        "category": "env",
                        "hcl": False,
                        "sensitive": False,
                    },
                }
                for index in range(count)
            ],
            "meta": None,
        }
        return mock_response

    def test_list_variables_uses_single_unpaginated_request(self):
        self.mock_transport.request.return_value = self._mock_response(101)

        result = list(self.variables_service.list(self.workspace_id))

        assert len(result) == 101
        assert isinstance(result[0], Variable)
        assert result[0].id == "var-0"
        assert result[0].key == "key_0"
        assert result[0].category == CategoryType.ENV
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/workspaces/{self.workspace_id}/vars", params={}
        )

    def test_list_all_variables_uses_single_unpaginated_request(self):
        self.mock_transport.request.return_value = self._mock_response(101)

        result = list(self.variables_service.list_all(self.workspace_id))

        assert len(result) == 101
        assert result[100].id == "var-100"
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/workspaces/{self.workspace_id}/all-vars", params={}
        )

    def test_list_variables_invalid_workspace_id(self):
        with pytest.raises(ValueError, match="invalid workspace ID"):
            list(self.variables_service.list(""))

    def test_list_all_variables_invalid_workspace_id(self):
        with pytest.raises(ValueError, match="invalid workspace ID"):
            list(self.variables_service.list_all(""))
