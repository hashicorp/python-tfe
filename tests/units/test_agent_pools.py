# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for agent pool operations.

These tests mock the TFE API responses and focus on:
1. Agent pool model validation and serialization
2. Agent pool CRUD operations
3. Agent token management
4. Request building and parameter handling
5. Response parsing and error handling
6. Workspace assignment (assign_to_workspaces / remove_from_workspaces bug fix)

Run with:
    pytest tests/units/test_agent_pools.py -v
"""

from unittest.mock import Mock

import pytest

from pytfe.errors import AuthError, NotFound, ValidationError
from pytfe.models.agent import (
    AgentPool,
    AgentPoolAllowedWorkspacePolicy,
    AgentPoolAssignToWorkspacesOptions,
    AgentPoolCreateOptions,
    AgentPoolListOptions,
    AgentPoolRemoveFromWorkspacesOptions,
    AgentPoolUpdateOptions,
    AgentTokenCreateOptions,
)


class TestAgentPoolModels:
    """Test agent pool model validation and serialization"""

    def test_agent_pool_model_basic(self):
        """Test basic AgentPool model creation"""
        agent_pool = AgentPool(
            id="apool-123456789abcdef0",
            name="test-pool",
            created_at="2023-01-01T00:00:00Z",
            organization_scoped=True,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
            agent_count=0,
        )

        assert agent_pool.id == "apool-123456789abcdef0"
        assert agent_pool.name == "test-pool"
        assert agent_pool.organization_scoped is True
        assert (
            agent_pool.allowed_workspace_policy
            == AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES
        )
        assert agent_pool.agent_count == 0

    def test_agent_pool_allowed_workspace_policy_enum(self):
        """Test AgentPoolAllowedWorkspacePolicy enum values"""
        assert AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES == "all-workspaces"
        assert (
            AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES == "specific-workspaces"
        )

        agent_pool = AgentPool(
            id="apool-123456789abcdef0",
            name="test-pool",
            created_at="2023-01-01T00:00:00Z",
            organization_scoped=False,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES,
            agent_count=3,
        )

        assert (
            agent_pool.allowed_workspace_policy
            == AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES
        )

    def test_agent_pool_create_options(self):
        """Test AgentPoolCreateOptions model"""
        options = AgentPoolCreateOptions(
            name="test-pool",
            organization_scoped=True,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES,
        )

        assert options.name == "test-pool"
        assert options.organization_scoped is True
        assert (
            options.allowed_workspace_policy
            == AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES
        )

    def test_agent_pool_create_options_workspace_ids(self):
        """Test AgentPoolCreateOptions with allowed/excluded workspace IDs (bug fix)"""
        options = AgentPoolCreateOptions(
            name="scoped-pool",
            organization_scoped=False,
            allowed_workspace_ids=["ws-aaa", "ws-bbb"],
            excluded_workspace_ids=["ws-ccc"],
        )
        assert options.allowed_workspace_ids == ["ws-aaa", "ws-bbb"]
        assert options.excluded_workspace_ids == ["ws-ccc"]

    def test_agent_pool_update_options_workspace_ids(self):
        """Test AgentPoolUpdateOptions with allowed/excluded workspace IDs (bug fix)"""
        options = AgentPoolUpdateOptions(
            allowed_workspace_ids=["ws-aaa"],
            excluded_workspace_ids=["ws-bbb"],
        )
        assert options.allowed_workspace_ids == ["ws-aaa"]
        assert options.excluded_workspace_ids == ["ws-bbb"]


class TestAgentPoolOperations:
    """Test agent pool CRUD operations"""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def agent_pools_service(self, mock_transport):
        """Create agent pools service with mocked transport."""
        from pytfe.resources.agent_pools import AgentPools

        return AgentPools(mock_transport)

    def test_list_agent_pools(self, agent_pools_service, mock_transport):
        """Test listing agent pools"""
        mock_response = {
            "data": [
                {
                    "id": "apool-123456789abcdef0",
                    "type": "agent-pools",
                    "attributes": {
                        "name": "test-pool-1",
                        "created-at": "2023-01-01T00:00:00Z",
                        "organization-scoped": True,
                        "allowed-workspace-policy": "all-workspaces",
                        "agent-count": 2,
                    },
                }
            ]
        }

        mock_transport.request.return_value.json.return_value = mock_response
        agent_pools = list(agent_pools_service.list("test-org"))

        assert len(agent_pools) == 1
        assert agent_pools[0].name == "test-pool-1"
        assert agent_pools[0].agent_count == 2

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert "organizations/test-org/agent-pools" in call_args[0][1]

    def test_list_agent_pools_with_options(self, agent_pools_service, mock_transport):
        """Test listing agent pools with options"""
        mock_response = {"data": []}
        mock_transport.request.return_value.json.return_value = mock_response

        options = AgentPoolListOptions(
            page_size=10,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
        )

        list(agent_pools_service.list("test-org", options))

        # Verify API call includes query parameters
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        params = call_args[1]["params"]
        assert params["page[number]"] == 1
        assert params["page[size]"] == 10
        assert params["filter[allowed_workspace_policy]"] == "all-workspaces"

    def test_create_agent_pool(self, agent_pools_service, mock_transport):
        """Test creating an agent pool"""
        mock_response = {
            "data": {
                "id": "apool-123456789abcdef0",
                "type": "agent-pools",
                "attributes": {
                    "name": "new-pool",
                    "created-at": "2023-01-01T00:00:00Z",
                    "organization-scoped": True,
                    "allowed-workspace-policy": "all-workspaces",
                    "agent-count": 0,
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response
        options = AgentPoolCreateOptions(
            name="new-pool",
            organization_scoped=True,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
        )

        agent_pool = agent_pools_service.create("test-org", options)

        assert agent_pool.id == "apool-123456789abcdef0"
        assert agent_pool.name == "new-pool"
        assert agent_pool.organization_scoped is True

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert "organizations/test-org/agent-pools" in call_args[0][1]

    def test_read_agent_pool(self, agent_pools_service, mock_transport):
        """Test reading a specific agent pool"""
        mock_response = {
            "data": {
                "id": "apool-123456789abcdef0",
                "type": "agent-pools",
                "attributes": {
                    "name": "existing-pool",
                    "created-at": "2023-01-01T00:00:00Z",
                    "organization-scoped": False,
                    "allowed-workspace-policy": "specific-workspaces",
                    "agent-count": 3,
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response
        agent_pool = agent_pools_service.read("apool-123456789abcdef0")

        assert agent_pool.id == "apool-123456789abcdef0"
        assert agent_pool.name == "existing-pool"
        assert agent_pool.organization_scoped is False
        assert agent_pool.agent_count == 3

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert "agent-pools/apool-123456789abcdef0" in call_args[0][1]

    def test_update_agent_pool(self, agent_pools_service, mock_transport):
        """Test updating an agent pool"""
        mock_response = {
            "data": {
                "id": "apool-123456789abcdef0",
                "type": "agent-pools",
                "attributes": {
                    "name": "updated-pool",
                    "created-at": "2023-01-01T00:00:00Z",
                    "organization-scoped": False,
                    "allowed-workspace-policy": "specific-workspaces",
                    "agent-count": 1,
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response
        options = AgentPoolUpdateOptions(name="updated-pool", organization_scoped=False)
        agent_pool = agent_pools_service.update("apool-123456789abcdef0", options)

        assert agent_pool.id == "apool-123456789abcdef0"
        assert agent_pool.name == "updated-pool"
        assert agent_pool.organization_scoped is False

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "agent-pools/apool-123456789abcdef0" in call_args[0][1]

    def test_delete_agent_pool(self, agent_pools_service, mock_transport):
        """Test deleting an agent pool"""
        agent_pools_service.delete("apool-123456789abcdef0")

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "agent-pools/apool-123456789abcdef0" in call_args[0][1]

    def test_assign_to_workspaces(self, agent_pools_service, mock_transport):
        """assign_to_workspaces must PATCH /agent-pools/:id with relationships.allowed-workspaces.

        Previously (broken): POST /agent-pools/:id/relationships/workspaces -> 404
        Fixed: PATCH /agent-pools/:id with relationships.allowed-workspaces body
        """
        pool_id = "apool-123456789abcdef0"
        ws_id = "ws-aaaaaaaaaaaaaaa1"

        mock_response = {
            "data": {
                "id": pool_id,
                "type": "agent-pools",
                "attributes": {
                    "name": "test-pool",
                    "created-at": "2023-01-01T00:00:00Z",
                    "organization-scoped": True,
                    "allowed-workspace-policy": "all-workspaces",
                    "agent-count": 0,
                },
            }
        }
        mock_transport.request.return_value.json.return_value = mock_response

        agent_pool = agent_pools_service.assign_to_workspaces(
            pool_id,
            AgentPoolAssignToWorkspacesOptions(workspace_ids=[ws_id]),
        )

        assert agent_pool.id == pool_id
        assert agent_pool.name == "test-pool"

        call_args = mock_transport.request.call_args
        # Must be PATCH, not POST
        assert call_args[0][0] == "PATCH"
        # Must target the pool URL, not a /relationships/workspaces sub-resource
        assert call_args[0][1] == f"/api/v2/agent-pools/{pool_id}"
        # Payload must use relationships.allowed-workspaces
        body = call_args[1]["json_body"]["data"]
        assert body["type"] == "agent-pools"
        assert body["id"] == pool_id
        ws_data = body["relationships"]["allowed-workspaces"]["data"]
        assert ws_data[0]["id"] == ws_id
        assert ws_data[0]["type"] == "workspaces"

    def test_remove_from_workspaces(self, agent_pools_service, mock_transport):
        """remove_from_workspaces must PATCH /agent-pools/:id with relationships.excluded-workspaces.

        Previously (broken): DELETE /agent-pools/:id/relationships/workspaces -> 404
        Fixed: PATCH /agent-pools/:id with relationships.excluded-workspaces body
        """
        pool_id = "apool-123456789abcdef0"
        ws_id = "ws-aaaaaaaaaaaaaaa1"

        mock_response = {
            "data": {
                "id": pool_id,
                "type": "agent-pools",
                "attributes": {
                    "name": "test-pool",
                    "created-at": "2023-01-01T00:00:00Z",
                    "organization-scoped": True,
                    "allowed-workspace-policy": "all-workspaces",
                    "agent-count": 0,
                },
            }
        }
        mock_transport.request.return_value.json.return_value = mock_response

        agent_pool = agent_pools_service.remove_from_workspaces(
            pool_id,
            AgentPoolRemoveFromWorkspacesOptions(workspace_ids=[ws_id]),
        )

        assert agent_pool.id == pool_id
        assert agent_pool.name == "test-pool"

        call_args = mock_transport.request.call_args
        # Must be PATCH, not DELETE
        assert call_args[0][0] == "PATCH"
        # Must target the pool URL, not a /relationships/workspaces sub-resource
        assert call_args[0][1] == f"/api/v2/agent-pools/{pool_id}"
        # Payload must use relationships.excluded-workspaces
        body = call_args[1]["json_body"]["data"]
        assert body["type"] == "agent-pools"
        assert body["id"] == pool_id
        ws_data = body["relationships"]["excluded-workspaces"]["data"]
        assert ws_data[0]["id"] == ws_id
        assert ws_data[0]["type"] == "workspaces"


class TestAgentTokenOperations:
    """Test agent token operations"""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def agent_tokens_service(self, mock_transport):
        """Create agent tokens service with mocked transport."""
        from pytfe.resources.agents import AgentTokens

        return AgentTokens(mock_transport)

    def test_list_agent_tokens(self, agent_tokens_service, mock_transport):
        """Test listing agent tokens"""
        mock_response = {
            "data": [
                {
                    "id": "at-123456789abcdef0",
                    "type": "agent-tokens",
                    "attributes": {
                        "description": "Token 1",
                        "created-at": "2023-01-01T00:00:00Z",
                        "last-used-at": "2023-01-02T00:00:00Z",
                    },
                }
            ]
        }

        mock_transport.request.return_value.json.return_value = mock_response
        tokens = list(agent_tokens_service.list("apool-123456789abcdef0"))

        assert len(tokens) == 1
        assert tokens[0].id == "at-123456789abcdef0"
        assert tokens[0].description == "Token 1"

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert (
            "agent-pools/apool-123456789abcdef0/authentication-tokens"
            in call_args[0][1]
        )

    def test_create_agent_token(self, agent_tokens_service, mock_transport):
        """Test creating an agent token"""
        mock_response = {
            "data": {
                "id": "at-123456789abcdef0",
                "type": "agent-tokens",
                "attributes": {
                    "description": "New token",
                    "created-at": "2023-01-01T00:00:00Z",
                    "last-used-at": None,
                    "token": "secret-token-value",
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response
        options = AgentTokenCreateOptions(description="New token")
        token = agent_tokens_service.create("apool-123456789abcdef0", options)

        assert token.id == "at-123456789abcdef0"
        assert token.description == "New token"
        assert token.token == "secret-token-value"
        assert token.last_used_at is None

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            "agent-pools/apool-123456789abcdef0/authentication-tokens"
            in call_args[0][1]
        )

    def test_read_agent_token(self, agent_tokens_service, mock_transport):
        """Test reading an agent token"""
        mock_response = {
            "data": {
                "id": "at-123456789abcdef0",
                "type": "agent-tokens",
                "attributes": {
                    "description": "Existing token",
                    "created-at": "2023-01-01T00:00:00Z",
                    "last-used-at": "2023-01-02T00:00:00Z",
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response
        token = agent_tokens_service.read("at-123456789abcdef0")

        assert token.id == "at-123456789abcdef0"
        assert token.description == "Existing token"

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert "authentication-tokens/at-123456789abcdef0" in call_args[0][1]

    def test_delete_agent_token(self, agent_tokens_service, mock_transport):
        """Test deleting an agent token"""
        agent_tokens_service.delete("at-123456789abcdef0")

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "authentication-tokens/at-123456789abcdef0" in call_args[0][1]


class TestAgentPoolErrorHandling:
    """Test error handling scenarios for agent pools"""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def agent_pools_service(self, mock_transport):
        """Create agent pools service with mocked transport."""
        from pytfe.resources.agent_pools import AgentPools

        return AgentPools(mock_transport)

    def test_not_found_error(self, agent_pools_service, mock_transport):
        """Test handling of NotFound errors"""
        mock_transport.request.side_effect = NotFound("Agent pool not found")

        with pytest.raises(NotFound):
            agent_pools_service.read("nonexistent-pool")

    def test_validation_error(self, agent_pools_service, mock_transport):
        """Test handling of ValidationError errors"""
        mock_transport.request.side_effect = ValidationError("Invalid agent pool name")

        options = AgentPoolCreateOptions(
            name="valid-name"
        )  # Use valid name to avoid ValueError

        with pytest.raises(ValidationError):
            agent_pools_service.create("test-org", options)

    def test_auth_error(self, agent_pools_service, mock_transport):
        """Test handling of AuthError errors"""
        mock_transport.request.side_effect = AuthError("Unauthorized")

        with pytest.raises(AuthError):
            list(agent_pools_service.list("test-org"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
