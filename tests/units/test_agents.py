"""Unit tests for individual agent operations.

These tests mock the TFE API responses and focus on:
1. Agent model validation and serialization
2. Agent CRUD operations (list, read, delete)
3. Request building and parameter handling
4. Response parsing and error handling

Run with:
    pytest tests/units/test_agents.py -v
"""

from unittest.mock import Mock

import pytest

from tfe.errors import AuthError, NotFound
from tfe.models.agent import (
    Agent,
    AgentStatus,
)


class TestAgentModels:
    """Test agent model validation and serialization"""

    def test_agent_model_basic(self):
        """Test basic Agent model creation"""
        agent = Agent(
            id="agent-123456789abcdef0",
            name="test-agent",
            status=AgentStatus.IDLE,
            version="1.0.0",
            ip_address="192.168.1.100",
            last_ping_at="2023-01-01T00:00:00Z",
        )

        assert agent.id == "agent-123456789abcdef0"
        assert agent.name == "test-agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.version == "1.0.0"
        assert agent.ip_address == "192.168.1.100"
        assert agent.last_ping_at is not None

    def test_agent_model_minimal(self):
        """Test Agent model with minimal required fields"""
        agent = Agent(id="agent-123456789abcdef0")

        assert agent.id == "agent-123456789abcdef0"
        assert agent.name is None
        assert agent.status is None
        assert agent.version is None
        assert agent.ip_address is None
        assert agent.last_ping_at is None

    def test_agent_status_enum(self):
        """Test AgentStatus enum values"""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.BUSY == "busy"
        assert AgentStatus.UNKNOWN == "unknown"


class TestAgentOperations:
    """Test individual agent CRUD operations"""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def agents_service(self, mock_transport):
        """Create agents service with mocked transport."""
        from tfe.resources.agents import Agents

        return Agents(mock_transport)

    def test_list_agents(self, agents_service, mock_transport):
        """Test listing agents in an agent pool"""
        mock_response = {
            "data": [
                {
                    "id": "agent-123456789abcdef0",
                    "type": "agents",
                    "attributes": {
                        "name": "test-agent-1",
                        "status": "idle",
                        "version": "1.0.0",
                        "ip-address": "192.168.1.100",
                        "last-ping-at": "2023-01-01T00:00:00Z",
                    },
                }
            ]
        }

        mock_transport.request.return_value.json.return_value = mock_response

        agents = list(agents_service.list("apool-123456789abcdef0"))

        assert len(agents) == 1
        assert agents[0].name == "test-agent-1"
        assert agents[0].status == AgentStatus.IDLE

        # Verify API call
        mock_transport.request.assert_called()

    def test_read_agent(self, agents_service, mock_transport):
        """Test reading a specific agent"""
        mock_response = {
            "data": {
                "id": "agent-123456789abcdef0",
                "type": "agents",
                "attributes": {
                    "name": "existing-agent",
                    "status": "idle",
                    "version": "1.2.0",
                    "ip-address": "192.168.1.200",
                    "last-ping-at": "2023-01-01T00:00:00Z",
                },
            }
        }

        mock_transport.request.return_value.json.return_value = mock_response

        agent = agents_service.read("agent-123456789abcdef0")

        assert agent.id == "agent-123456789abcdef0"
        assert agent.name == "existing-agent"
        assert agent.status == AgentStatus.IDLE
        assert agent.version == "1.2.0"
        assert agent.ip_address == "192.168.1.200"

        # Verify API call
        mock_transport.request.assert_called_once()

    def test_delete_agent(self, agents_service, mock_transport):
        """Test deleting an agent"""
        agents_service.delete("agent-123456789abcdef0")

        # Verify API call
        mock_transport.request.assert_called_once()


class TestAgentErrorHandling:
    """Test error handling scenarios for agents"""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def agents_service(self, mock_transport):
        """Create agents service with mocked transport."""
        from tfe.resources.agents import Agents

        return Agents(mock_transport)

    def test_not_found_error(self, agents_service, mock_transport):
        """Test handling of NotFound errors"""
        mock_transport.request.side_effect = NotFound("Agent not found")

        with pytest.raises(NotFound):
            agents_service.read("nonexistent-agent")

    def test_auth_error(self, agents_service, mock_transport):
        """Test handling of AuthError errors"""
        mock_transport.request.side_effect = AuthError("Unauthorized")

        with pytest.raises(AuthError):
            agents_service.read("agent-123456789abcdef0")
