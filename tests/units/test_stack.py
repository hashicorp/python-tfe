# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the stack module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.models.agent import AgentPool
from pytfe.models.project import Project
from pytfe.models.stack import (
    Stack,
    StackCreateOptions,
    StackListOptions,
    StackSortColumn,
    StackUpdateOptions,
    StackVcsRepoOptions,
)
from pytfe.resources.stack import Stacks


class TestStacks:
    """Test the Stacks service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def stacks_service(self, mock_transport):
        """Create a Stacks service with mocked transport."""
        return Stacks(mock_transport)

    @pytest.fixture
    def stack_response_data(self):
        """Return sample API response data for a stack."""
        return {
            "id": "st-123",
            "attributes": {
                "name": "demo-stack",
                "description": "Stack description",
                "speculation-enabled": True,
                "vcs-repo": {
                    "identifier": "hashicorp/terraform",
                    "branch": "main",
                    "oauth-token-id": "ot-123",
                },
            },
            "relationships": {
                "project": {"data": {"id": "prj-123", "type": "projects"}},
                "agent-pool": {"data": {"id": "apool-123", "type": "agent-pools"}},
            },
        }

    def test_list_stacks_success(self, stacks_service, stack_response_data):
        """Test successful list operation."""
        stacks_service._list = Mock(return_value=[stack_response_data])

        options = StackListOptions(
            page_size=10,
            project_id="prj-123",
            sort=StackSortColumn.STACK_SORT_BY_NAME,
            search_by_name="demo",
        )

        result_iter = stacks_service.list("org-123", options)
        items = list(result_iter)

        stacks_service._list.assert_called_once_with(
            "/api/v2/organizations/org-123/stacks",
            params={
                "page[size]": 10,
                "filter[project][id]": "prj-123",
                "sort": "name",
                "search[name]": "demo",
            },
        )

        assert len(items) == 1
        assert isinstance(items[0], Stack)
        assert items[0].id == "st-123"
        assert items[0].name == "demo-stack"

    def test_create_stack_success(
        self, stacks_service, mock_transport, stack_response_data
    ):
        """Test successful create operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_response_data}
        mock_transport.request.return_value = mock_response

        options = StackCreateOptions(
            name="demo-stack",
            description="Stack description",
            speculation_enabled=True,
            vcs_repo=StackVcsRepoOptions(
                identifier="hashicorp/terraform",
                branch="main",
                oauth_token_id="ot-123",
            ),
            project=Project(id="prj-123"),
            agent_pool=AgentPool(id="apool-123"),
        )

        result = stacks_service.create(options)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="/api/v2/stacks",
            json_body={
                "data": {
                    "attributes": {
                        "name": "demo-stack",
                        "description": "Stack description",
                        "speculation-enabled": True,
                        "vcs-repo": {
                            "identifier": "hashicorp/terraform",
                            "branch": "main",
                            "oauth-token-id": "ot-123",
                        },
                    },
                    "type": "stacks",
                    "relationships": {
                        "project": {"data": {"id": "prj-123", "type": "projects"}},
                        "agent-pool": {
                            "data": {"id": "apool-123", "type": "agent-pools"}
                        },
                    },
                }
            },
        )

        assert isinstance(result, Stack)
        assert result.id == "st-123"
        assert result.project.id == "prj-123"
        assert result.agent_pool.id == "apool-123"

    def test_update_stack_success(
        self, stacks_service, mock_transport, stack_response_data
    ):
        """Test successful update operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_response_data}
        mock_transport.request.return_value = mock_response

        options = StackUpdateOptions(
            description="Updated description",
            vcs_repo=StackVcsRepoOptions(
                identifier="hashicorp/terraform",
                branch="main",
            ),
            project=Project(id="prj-123"),
            agent_pool=AgentPool(id="apool-123"),
        )

        result = stacks_service.update("st-123", options)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            path="/api/v2/stacks/st-123",
            json_body={
                "data": {
                    "attributes": {
                        "description": "Updated description",
                        "vcs-repo": {
                            "identifier": "hashicorp/terraform",
                            "branch": "main",
                        },
                    },
                    "type": "stacks",
                    "relationships": {
                        "project": {"data": {"id": "prj-123", "type": "projects"}},
                        "agent-pool": {
                            "data": {"id": "apool-123", "type": "agent-pools"}
                        },
                    },
                }
            },
        )

        assert isinstance(result, Stack)
        assert result.id == "st-123"

    def test_read_stack_success(
        self, stacks_service, mock_transport, stack_response_data
    ):
        """Test successful read operation."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": stack_response_data}
        mock_transport.request.return_value = mock_response

        result = stacks_service.read("st-123")

        mock_transport.request.assert_called_once_with(
            "GET",
            path="/api/v2/stacks/st-123",
        )

        assert isinstance(result, Stack)
        assert result.id == "st-123"
        assert result.name == "demo-stack"

    def test_delete_stack_success(self, stacks_service, mock_transport):
        """Test successful delete operation."""
        result = stacks_service.delete("st-123")

        mock_transport.request.assert_called_once_with(
            "DELETE",
            path="/api/v2/stacks/st-123",
        )
        assert result is None

    def test_force_delete_stack_success(self, stacks_service, mock_transport):
        """Test successful force-delete operation."""
        result = stacks_service.force_delete("st-123")

        mock_transport.request.assert_called_once_with(
            "DELETE",
            path="/api/v2/stacks/st-123?force=true",
        )
        assert result is None

    def test_stack_from_handles_null_vcs_repo(self, stacks_service):
        """Test parsing stack data when vcs-repo is null."""
        data = {
            "id": "st-456",
            "attributes": {
                "name": "no-vcs-stack",
                "vcs-repo": None,
            },
            "relationships": {
                "project": {"data": {"id": "prj-999", "type": "projects"}},
            },
        }

        result = stacks_service._stack_from(data)

        assert isinstance(result, Stack)
        assert result.id == "st-456"
        assert result.vcs_repo is None
        assert result.project is not None
        assert result.project.id == "prj-999"
        assert result.agent_pool is None

    def test_stack_from_handles_missing_relationships(self, stacks_service):
        """Test parsing stack data when relationship data is missing."""
        data = {
            "id": "st-789",
            "attributes": {
                "name": "minimal-stack",
                "vcs-repo": None,
            },
            "relationships": {
                "project": {"data": None},
                "agent-pool": {"data": None},
            },
        }

        result = stacks_service._stack_from(data)

        assert isinstance(result, Stack)
        assert result.id == "st-789"
        assert result.project is None
        assert result.agent_pool is None
