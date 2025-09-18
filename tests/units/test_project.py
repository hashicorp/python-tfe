from unittest.mock import Mock

from tfe.resources.projects import Projects, _safe_str
from tfe.types import Project, ProjectCreateOptions, ProjectUpdateOptions


class TestProjects:
    def setup_method(self):
        """Setup method that runs before each test"""
        self.mock_transport = Mock()
        self.projects_service = Projects(self.mock_transport)

    def test_projects_service_init(self):
        """Test that Projects service initializes correctly"""
        mock_transport = Mock()
        service = Projects(mock_transport)
        assert service.t == mock_transport

    def test_list_projects_success(self):
        """Test successful listing of projects"""
        organization = "test-org"

        # Mock API response data
        mock_api_response = [
            {
                "id": "prj-123",
                "type": "projects",
                "attributes": {"name": "Test Project 1"},
            },
            {
                "id": "prj-456",
                "type": "projects",
                "attributes": {"name": "Test Project 2"},
            },
        ]

        # Mock the _list method to return our test data
        self.projects_service._list = Mock(return_value=mock_api_response)

        # Call the method under test
        result = list(self.projects_service.list(organization))

        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], Project)
        assert isinstance(result[1], Project)

        # Check first project
        assert result[0].id == "prj-123"
        assert result[0].name == "Test Project 1"
        assert result[0].organization == organization

        # Check second project
        assert result[1].id == "prj-456"
        assert result[1].name == "Test Project 2"
        assert result[1].organization == organization

        # Verify the correct API path was used
        expected_path = f"/api/v2/organizations/{organization}/projects"
        self.projects_service._list.assert_called_once_with(expected_path)

    def test_create_project_success(self):
        """Test successful project creation"""
        organization = "test-org"
        project_name = "New Project"
        options = ProjectCreateOptions(name=project_name)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "prj-123",
                "type": "projects",
                "attributes": {"name": project_name},
            }
        }
        self.mock_transport.request.return_value = mock_response

        result = self.projects_service.create(organization, options)

        # Assertions
        assert isinstance(result, Project)
        assert result.id == "prj-123"
        assert result.name == project_name
        assert result.organization == organization

        # Verify API call
        expected_path = f"/api/v2/organizations/{organization}/projects"
        expected_payload = {
            "data": {"type": "projects", "attributes": {"name": project_name}}
        }
        self.mock_transport.request.assert_called_once_with(
            "POST", expected_path, json_body=expected_payload
        )

    def test_read_project_success(self):
        """Test successful project read"""
        project_id = "prj-123"

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": project_id,
                "type": "projects",
                "attributes": {"name": "Test Project"},
                "relationships": {"organization": {"data": {"id": "test-org"}}},
            }
        }
        self.mock_transport.request.return_value = mock_response

        result = self.projects_service.read(project_id)

        # Assertions
        assert isinstance(result, Project)
        assert result.id == project_id
        assert result.name == "Test Project"
        assert result.organization == "test-org"

        # Verify API call
        expected_path = f"/api/v2/projects/{project_id}"
        self.mock_transport.request.assert_called_once_with("GET", expected_path)

    def test_update_project_success(self):
        """Test successful project update"""
        project_id = "prj-123"
        new_name = "Updated Project"
        options = ProjectUpdateOptions(name=new_name)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": project_id,
                "type": "projects",
                "attributes": {"name": new_name},
                "relationships": {"organization": {"data": {"id": "test-org"}}},
            }
        }
        self.mock_transport.request.return_value = mock_response

        result = self.projects_service.update(project_id, options)

        # Assertions
        assert isinstance(result, Project)
        assert result.id == project_id
        assert result.name == new_name
        assert result.organization == "test-org"

        # Verify API call
        expected_path = f"/api/v2/projects/{project_id}"
        expected_payload = {
            "data": {
                "type": "projects",
                "id": project_id,
                "attributes": {"name": new_name},
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH", expected_path, json_body=expected_payload
        )

    def test_delete_project_success(self):
        """Test successful project deletion"""
        project_id = "prj-123"

        result = self.projects_service.delete(project_id)

        # Delete should return None
        assert result is None

        # Verify API call
        expected_path = f"/api/v2/projects/{project_id}"
        self.mock_transport.request.assert_called_once_with("DELETE", expected_path)

    def test_safe_str_function(self):
        """Test _safe_str utility function"""
        # Test with string
        assert _safe_str("test") == "test"

        # Test with None
        assert _safe_str(None) == ""

        # Test with integer
        assert _safe_str(123) == "123"

        # Test with custom default
        assert _safe_str(None, "default") == "default"

        # Test with boolean
        assert _safe_str(True) == "True"
        assert _safe_str(False) == "False"

    def test_list_projects_empty_response(self):
        """Test listing projects when API returns empty response"""
        organization = "empty-org"

        # Mock empty API response
        self.projects_service._list = Mock(return_value=[])

        result = list(self.projects_service.list(organization))

        assert len(result) == 0
        assert isinstance(result, list)

    def test_read_project_missing_organization(self):
        """Test reading project when organization info is missing"""
        project_id = "prj-123"

        # Mock API response without organization relationship
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": project_id,
                "type": "projects",
                "attributes": {"name": "Test Project"},
                # No relationships field
            }
        }
        self.mock_transport.request.return_value = mock_response

        result = self.projects_service.read(project_id)

        assert result.organization == ""  # Should default to empty string
