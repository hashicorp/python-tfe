"""Unit tests for individual agent operations."""

import pytest

def test_simple_agent_discovery():
    """Simple test to ensure pytest can discover this file."""
    assert True

from unittest.mock import Mock

import pytest

from tfe.errors import NotFound, ValidationError, AuthError
from tfe.models.agent import (
    Agent,
    AgentStatus,
    AgentListOptions,
    AgentReadOptions,
)


def test_simple_agent_discovery():
    """Simple test to ensure pytest can discover this file."""
    assert True


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
            last_ping_at="2023-01-01T00:00:00Z"
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
        
        # Test with each status
        for status in [AgentStatus.IDLE, AgentStatus.BUSY, AgentStatus.UNKNOWN]:
            agent = Agent(
                id="agent-123456789abcdef0",
                name="test-agent",
                status=status,
                ip_address="192.168.1.100",
                last_ping_at="2023-01-01T00:00:00Z"
            )
            assert agent.status == status

    def test_agent_list_options(self):
        """Test AgentListOptions model"""
        # Test with all options
        options = AgentListOptions(
            page_number=2,
            page_size=10,
            status=AgentStatus.IDLE
        )
        
        assert options.page_number == 2
        assert options.page_size == 10
        assert options.status == AgentStatus.IDLE
        
        # Test minimal options
        minimal_options = AgentListOptions()
        assert minimal_options.page_number is None
        assert minimal_options.page_size is None
        assert minimal_options.status is None

    def test_agent_read_options(self):
        """Test AgentReadOptions model"""
        # Test with include parameter
        options = AgentReadOptions(include=["agent-pool"])
        assert options.include == ["agent-pool"]
        
        # Test minimal options
        minimal_options = AgentReadOptions()
        assert minimal_options.include is None


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
                        "last-ping-at": "2023-01-01T00:00:00Z"
                    }
                },
                {
                    "id": "agent-abcdef0123456789",
                    "type": "agents",
                    "attributes": {
                        "name": "test-agent-2",
                        "status": "busy",
                        "version": "1.0.1",
                        "ip-address": "192.168.1.101",
                        "last-ping-at": "2023-01-01T01:00:00Z"
                    }
                }
            ]
        }
        
        mock_transport._list.return_value = mock_response["data"]
        
        agents = list(agents_service.list("apool-123456789abcdef0"))
        
        assert len(agents) == 2
        assert agents[0].name == "test-agent-1"
        assert agents[0].status == AgentStatus.IDLE
        assert agents[1].name == "test-agent-2"
        assert agents[1].status == AgentStatus.BUSY
        
        # Verify API call
        mock_transport._list.assert_called_once()
        call_args = mock_transport._list.call_args
        assert "agent-pools/apool-123456789abcdef0/agents" in call_args[0][0]
    
    def test_list_agents_with_options(self, agents_service, mock_transport):
        """Test listing agents with filtering options"""
        mock_transport._list.return_value = []
        
        options = AgentListOptions(
            page_number=2,
            page_size=10,
            status=AgentStatus.IDLE
        )
        
        list(agents_service.list("apool-123456789abcdef0", options))
        
        # Verify API call includes query parameters
        mock_transport._list.assert_called_once()
        call_args = mock_transport._list.call_args
        params = call_args[1]["params"]
        assert params["page[number]"] == 2
        assert params["page[size]"] == 10
        assert params["filter[status]"] == "idle"
    
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
                    "last-ping-at": "2023-01-01T00:00:00Z"
                }
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
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert "agents/agent-123456789abcdef0" in call_args[0][1]

    def test_read_agent_with_options(self, agents_service, mock_transport):
        """Test reading an agent with include options"""
        mock_response = {
            "data": {
                "id": "agent-123456789abcdef0",
                "type": "agents",
                "attributes": {
                    "name": "existing-agent",
                    "status": "busy",
                    "version": "1.2.0",
                    "ip-address": "192.168.1.200",
                    "last-ping-at": "2023-01-01T00:00:00Z"
                }
            }
        }
        
        mock_transport.request.return_value.json.return_value = mock_response
        
        options = AgentReadOptions(include=["agent-pool"])
        agent = agents_service.read("agent-123456789abcdef0", options)
        
        assert agent.id == "agent-123456789abcdef0"
        assert agent.status == AgentStatus.BUSY
        
        # Verify API call includes query parameters
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        params = call_args[1].get("params", {})
        assert "include" in params
        assert "agent-pool" in params["include"]

    def test_delete_agent(self, agents_service, mock_transport):
        """Test deleting an agent"""
        agents_service.delete("agent-123456789abcdef0")
        
        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "agents/agent-123456789abcdef0" in call_args[0][1]


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
    
    def test_validation_error_invalid_agent_pool_id(self, agents_service, mock_transport):
        """Test handling of ValidationError for invalid agent pool ID"""
        with pytest.raises(ValueError, match="Agent pool ID is required and must be valid"):
            list(agents_service.list(""))
    
    def test_validation_error_invalid_agent_id(self, agents_service, mock_transport):
        """Test handling of ValidationError for invalid agent ID"""
        with pytest.raises(ValueError, match="Agent ID is required and must be valid"):
            agents_service.read("")

    def test_auth_error(self, agents_service, mock_transport):
        """Test handling of AuthError errors"""
        mock_transport.request.side_effect = AuthError("Unauthorized")
        
        with pytest.raises(AuthError):
            agents_service.read("agent-123456789abcdef0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
