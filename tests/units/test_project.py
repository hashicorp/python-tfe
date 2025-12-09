from unittest.mock import Mock

from pytfe.models import (
    EffectiveTagBinding,
)
from pytfe.models.project import (
    Project,
    ProjectAddTagBindingsOptions,
    ProjectCreateOptions,
    ProjectUpdateOptions,
    TagBinding,
)
from pytfe.resources.projects import Projects, _safe_str


class TestProjects:
    def setup_method(self):
        """Setup method that runs before each test"""
        self.mock_transport = Mock()
        self.projects_service = Projects(self.mock_transport)
        self.project_id = "prj-test123"

    def test_add_tag_bindings_with_none_value(self):
        """Test adding tag bindings with None value"""
        # Prepare test data with None value
        tag_bindings = [TagBinding(key="flag", value=None)]
        options = ProjectAddTagBindingsOptions(tag_bindings=tag_bindings)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-flag123",
                    "type": "tag-bindings",
                    "attributes": {"key": "flag", "value": None},
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        self.projects_service.add_tag_bindings(self.project_id, options)

        # Verify payload doesn't include value for None values
        expected_payload = {
            "data": [
                {
                    "type": "tag-bindings",
                    "attributes": {"key": "flag"},  # No value field
                }
            ]
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/projects/{self.project_id}/tag-bindings",
            json_body=expected_payload,
        )

    def test_projects_service_init(self):
        """Test that Projects service initializes correctly"""
        mock_transport = Mock()
        projects_service = Projects(mock_transport)
        assert projects_service.t == mock_transport

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


class TestProjectTagBindings:
    """Test class for project tag binding operations"""

    def setup_method(self):
        """Setup method that runs before each test"""
        self.mock_transport = Mock()
        self.projects_service = Projects(self.mock_transport)
        self.project_id = "prj-test123"

    def test_list_tag_bindings_success(self):
        """Test successful listing of tag bindings"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-123",
                    "type": "tag-bindings",
                    "attributes": {"key": "environment", "value": "production"},
                },
                {
                    "id": "tb-456",
                    "type": "tag-bindings",
                    "attributes": {"key": "team", "value": "platform"},
                },
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.projects_service.list_tag_bindings(self.project_id)

        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], TagBinding)
        assert isinstance(result[1], TagBinding)

        assert result[0].id == "tb-123"
        assert result[0].key == "environment"
        assert result[0].value == "production"

        assert result[1].id == "tb-456"
        assert result[1].key == "team"
        assert result[1].value == "platform"

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/projects/{self.project_id}/tag-bindings"
        )

    def test_list_tag_bindings_empty_response(self):
        """Test listing tag bindings with empty response"""
        # Mock empty API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        self.mock_transport.request.return_value = mock_response

        result = self.projects_service.list_tag_bindings(self.project_id)

        assert len(result) == 0
        assert isinstance(result, list)

    def test_list_tag_bindings_invalid_project_id(self):
        """Test listing tag bindings with invalid project ID"""
        import pytest

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.list_tag_bindings("")

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.list_tag_bindings(
                "! / nope"
            )  # Contains spaces and slashes

    def test_list_effective_tag_bindings_success(self):
        """Test successful listing of effective tag bindings"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "etb-123",
                    "type": "effective-tag-bindings",
                    "attributes": {"key": "environment", "value": "production"},
                    "links": {
                        "self": "/api/v2/projects/prj-test123/tag-bindings/etb-123"
                    },
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.projects_service.list_effective_tag_bindings(self.project_id)

        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], EffectiveTagBinding)

        assert result[0].id == "etb-123"
        assert result[0].key == "environment"
        assert result[0].value == "production"
        assert "self" in result[0].links

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/projects/{self.project_id}/tag-bindings/effective"
        )

    def test_list_effective_tag_bindings_invalid_project_id(self):
        """Test listing effective tag bindings with invalid project ID"""
        import pytest

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.list_effective_tag_bindings(None)

    def test_add_tag_bindings_success(self):
        """Test successful addition of tag bindings"""
        # Prepare test data
        tag_bindings = [
            TagBinding(key="environment", value="staging"),
            TagBinding(key="team", value="backend"),
        ]
        options = ProjectAddTagBindingsOptions(tag_bindings=tag_bindings)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-new123",
                    "type": "tag-bindings",
                    "attributes": {"key": "environment", "value": "staging"},
                },
                {
                    "id": "tb-new456",
                    "type": "tag-bindings",
                    "attributes": {"key": "team", "value": "backend"},
                },
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.projects_service.add_tag_bindings(self.project_id, options)

        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], TagBinding)
        assert isinstance(result[1], TagBinding)

        assert result[0].id == "tb-new123"
        assert result[0].key == "environment"
        assert result[0].value == "staging"

        assert result[1].id == "tb-new456"
        assert result[1].key == "team"
        assert result[1].value == "backend"

        # Verify API call was made with correct payload
        expected_payload = {
            "data": [
                {
                    "type": "tag-bindings",
                    "attributes": {"key": "environment", "value": "staging"},
                },
                {
                    "type": "tag-bindings",
                    "attributes": {"key": "team", "value": "backend"},
                },
            ]
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/projects/{self.project_id}/tag-bindings",
            json_body=expected_payload,
        )

    def test_add_tag_bindings_with_none_value(self):
        """Test adding tag bindings with None value"""
        # Prepare test data with None value
        tag_bindings = [TagBinding(key="flag", value=None)]
        options = ProjectAddTagBindingsOptions(tag_bindings=tag_bindings)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-flag123",
                    "type": "tag-bindings",
                    "attributes": {"key": "flag", "value": None},
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        self.projects_service.add_tag_bindings(self.project_id, options)

        # Verify payload doesn't include value for None values
        expected_payload = {
            "data": [
                {
                    "type": "tag-bindings",
                    "attributes": {"key": "flag"},  # No value field
                }
            ]
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/projects/{self.project_id}/tag-bindings",
            json_body=expected_payload,
        )

    def test_add_tag_bindings_invalid_project_id(self):
        """Test adding tag bindings with invalid project ID"""
        import pytest

        options = ProjectAddTagBindingsOptions(
            tag_bindings=[TagBinding(key="test", value="value")]
        )

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.add_tag_bindings("", options)

    def test_add_tag_bindings_empty_list(self):
        """Test adding tag bindings with empty tag binding list"""
        import pytest

        options = ProjectAddTagBindingsOptions(tag_bindings=[])

        with pytest.raises(ValueError, match="At least one tag binding is required"):
            self.projects_service.add_tag_bindings(self.project_id, options)

    def test_delete_tag_bindings_success(self):
        """Test successful deletion of tag bindings"""
        # Mock successful delete (no response body expected)
        self.mock_transport.request.return_value = Mock()

        # Call the method
        result = self.projects_service.delete_tag_bindings(self.project_id)

        # Assertions
        assert result is None  # Delete should return None

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "DELETE", f"/api/v2/projects/{self.project_id}/tag-bindings"
        )

    def test_delete_tag_bindings_invalid_project_id(self):
        """Test deleting tag bindings with invalid project ID"""
        import pytest

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.delete_tag_bindings(None)

        with pytest.raises(
            ValueError, match="Project ID is required and must be valid"
        ):
            self.projects_service.delete_tag_bindings(
                "bad/id"
            )  # Contains forward slash
