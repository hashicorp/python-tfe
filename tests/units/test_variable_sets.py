"""Unit tests for Variable Set resources."""

from unittest.mock import Mock

import pytest

from tfe.resources.variable_sets import VariableSets, VariableSetVariables
from tfe.types import (
    CategoryType,
    Parent,
    Project,
    VariableSet,
    VariableSetApplyToProjectsOptions,
    VariableSetApplyToWorkspacesOptions,
    VariableSetCreateOptions,
    VariableSetIncludeOpt,
    VariableSetListOptions,
    VariableSetReadOptions,
    VariableSetRemoveFromProjectsOptions,
    VariableSetRemoveFromWorkspacesOptions,
    VariableSetUpdateOptions,
    VariableSetUpdateWorkspacesOptions,
    VariableSetVariable,
    VariableSetVariableCreateOptions,
    VariableSetVariableUpdateOptions,
    Workspace,
)


class TestVariableSets:
    """Test cases for Variable Sets resource."""

    def setup_method(self):
        """Setup method that runs before each test."""
        self.mock_transport = Mock()
        self.variable_sets_service = VariableSets(self.mock_transport)
        self.org_name = "test-org"
        self.variable_set_id = "varset-test123"
        self.workspace_id = "ws-test123"
        self.project_id = "prj-test123"

    def test_variable_sets_service_init(self):
        """Test Variable Sets service initialization."""
        assert self.variable_sets_service.t == self.mock_transport

    def test_list_variable_sets_success(self):
        """Test successful listing of variable sets."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "varset-123",
                    "type": "varsets",
                    "attributes": {
                        "name": "test-varset",
                        "description": "Test variable set",
                        "global": False,
                        "priority": True,
                        "created-at": "2023-01-01T00:00:00.000Z",
                        "updated-at": "2023-01-01T00:00:00.000Z",
                    },
                    "relationships": {
                        "workspaces": {
                            "data": [{"id": "ws-123", "type": "workspaces"}]
                        },
                        "projects": {"data": [{"id": "prj-123", "type": "projects"}]},
                    },
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.list(self.org_name)

        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], VariableSet)
        assert result[0].id == "varset-123"
        assert result[0].name == "test-varset"
        assert result[0].description == "Test variable set"
        assert result[0].global_ is False
        assert result[0].priority is True

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/organizations/{self.org_name}/varsets", params={}
        )

    def test_list_variable_sets_with_options(self):
        """Test listing variable sets with options."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        self.mock_transport.request.return_value = mock_response

        # Create options
        options = VariableSetListOptions(
            page_number=2,
            page_size=50,
            query="test",
            include=[VariableSetIncludeOpt.WORKSPACES, VariableSetIncludeOpt.PROJECTS],
        )

        # Call the method
        result = self.variable_sets_service.list(self.org_name, options)

        # Verify the result
        assert isinstance(result, list)

        # Verify API call with parameters
        expected_params = {
            "page[number]": "2",
            "page[size]": "50",
            "q": "test",
            "include": "workspaces,projects",
        }
        self.mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/organizations/{self.org_name}/varsets",
            params=expected_params,
        )

    def test_list_variable_sets_invalid_organization(self):
        """Test listing variable sets with invalid organization."""
        with pytest.raises(ValueError, match="Organization name is required"):
            self.variable_sets_service.list("")

        with pytest.raises(ValueError, match="Organization name is required"):
            self.variable_sets_service.list(None)

    def test_list_for_workspace_success(self):
        """Test successful listing of variable sets for workspace."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "varset-123",
                    "type": "varsets",
                    "attributes": {
                        "name": "workspace-varset",
                        "description": "Workspace variable set",
                        "global": False,
                        "priority": False,
                    },
                    "relationships": {},
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.list_for_workspace(self.workspace_id)

        # Assertions
        assert len(result) == 1
        assert result[0].name == "workspace-varset"

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/workspaces/{self.workspace_id}/varsets", params={}
        )

    def test_list_for_workspace_invalid_id(self):
        """Test listing for workspace with invalid workspace ID."""
        with pytest.raises(ValueError, match="Workspace ID is required"):
            self.variable_sets_service.list_for_workspace("")

    def test_list_for_project_success(self):
        """Test successful listing of variable sets for project."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "varset-123",
                    "type": "varsets",
                    "attributes": {
                        "name": "project-varset",
                        "description": "Project variable set",
                        "global": False,
                        "priority": False,
                    },
                    "relationships": {},
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.list_for_project(self.project_id)

        # Assertions
        assert len(result) == 1
        assert result[0].name == "project-varset"

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/projects/{self.project_id}/varsets", params={}
        )

    def test_list_for_project_invalid_id(self):
        """Test listing for project with invalid project ID."""
        with pytest.raises(ValueError, match="Project ID is required"):
            self.variable_sets_service.list_for_project("")

    def test_create_variable_set_success(self):
        """Test successful variable set creation."""
        # Prepare test data - using model_validate with alias
        options = VariableSetCreateOptions.model_validate(
            {
                "name": "new-varset",
                "description": "New variable set",
                "global": False,  # Use alias name
                "priority": True,
            }
        )

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "varset-new123",
                "type": "varsets",
                "attributes": {
                    "name": "new-varset",
                    "description": "New variable set",
                    "global": False,
                    "priority": True,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.create(self.org_name, options)

        # Assertions
        assert isinstance(result, VariableSet)
        assert result.id == "varset-new123"
        assert result.name == "new-varset"
        assert result.description == "New variable set"
        assert result.global_ is False
        assert result.priority is True

        # Verify API call payload
        expected_payload = {
            "data": {
                "type": "varsets",
                "attributes": {
                    "name": "new-varset",
                    "description": "New variable set",
                    "global": False,
                    "priority": True,
                },
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/organizations/{self.org_name}/varsets",
            json_body=expected_payload,
        )

    def test_create_variable_set_with_parent_project(self):
        """Test creating variable set with parent project."""
        # Prepare test data
        project = Project(id="prj-parent123")
        parent = Parent(project=project)
        options = VariableSetCreateOptions.model_validate(
            {
                "name": "project-varset",
                "description": "Project scoped variable set",
                "global": False,  # Use alias name
                "parent": parent.model_dump(),
            }
        )

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "varset-project123",
                "type": "varsets",
                "attributes": {
                    "name": "project-varset",
                    "description": "Project scoped variable set",
                    "global": False,
                },
                "relationships": {
                    "parent": {"data": {"type": "projects", "id": "prj-parent123"}}
                },
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.create(self.org_name, options)

        # Assertions
        assert result.name == "project-varset"

        # Verify API call payload includes parent relationship
        expected_payload = {
            "data": {
                "type": "varsets",
                "attributes": {
                    "name": "project-varset",
                    "description": "Project scoped variable set",
                    "global": False,
                },
                "relationships": {
                    "parent": {
                        "data": {
                            "type": "projects",
                            "id": "prj-parent123",
                        }
                    }
                },
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/organizations/{self.org_name}/varsets",
            json_body=expected_payload,
        )

    def test_create_variable_set_invalid_params(self):
        """Test variable set creation with invalid parameters."""
        # Invalid organization
        with pytest.raises(ValueError, match="Organization name is required"):
            options = VariableSetCreateOptions.model_validate(
                {"name": "test", "global": False}
            )
            self.variable_sets_service.create("", options)

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variable_sets_service.create(self.org_name, None)

        # Missing name
        with pytest.raises(ValueError, match="Variable set name is required"):
            options = VariableSetCreateOptions.model_validate(
                {"name": "", "global": False}
            )
            self.variable_sets_service.create(self.org_name, options)

    def test_read_variable_set_success(self):
        """Test successful variable set read."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_set_id,
                "type": "varsets",
                "attributes": {
                    "name": "read-varset",
                    "description": "Variable set for reading",
                    "global": True,
                    "priority": False,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.read(self.variable_set_id)

        # Assertions
        assert isinstance(result, VariableSet)
        assert result.id == self.variable_set_id
        assert result.name == "read-varset"
        assert result.global_ is True

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/varsets/{self.variable_set_id}", params={}
        )

    def test_read_variable_set_with_include(self):
        """Test reading variable set with include options."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_set_id,
                "type": "varsets",
                "attributes": {"name": "test", "global": False},
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Create options
        options = VariableSetReadOptions(
            include=[VariableSetIncludeOpt.WORKSPACES, VariableSetIncludeOpt.VARS]
        )

        # Call the method
        self.variable_sets_service.read(self.variable_set_id, options)

        # Verify API call with include parameters
        expected_params = {"include": "workspaces,vars"}
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/varsets/{self.variable_set_id}", params=expected_params
        )

    def test_read_variable_set_invalid_id(self):
        """Test reading variable set with invalid ID."""
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variable_sets_service.read("")

    def test_update_variable_set_success(self):
        """Test successful variable set update."""
        # Prepare test data
        options = VariableSetUpdateOptions.model_validate(
            {
                "name": "updated-varset",
                "description": "Updated variable set",
                "global": True,  # Use alias
                "priority": False,
            }
        )

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_set_id,
                "type": "varsets",
                "attributes": {
                    "name": "updated-varset",
                    "description": "Updated variable set",
                    "global": True,
                    "priority": False,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.update(self.variable_set_id, options)

        # Assertions
        assert result.name == "updated-varset"
        assert result.description == "Updated variable set"
        assert result.global_ is True

        # Verify API call payload
        expected_payload = {
            "data": {
                "type": "varsets",
                "id": self.variable_set_id,
                "attributes": {
                    "name": "updated-varset",
                    "description": "Updated variable set",
                    "global": True,
                    "priority": False,
                },
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/varsets/{self.variable_set_id}",
            json_body=expected_payload,
        )

    def test_update_variable_set_invalid_params(self):
        """Test variable set update with invalid parameters."""
        options = VariableSetUpdateOptions(name="test")

        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variable_sets_service.update("", options)

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variable_sets_service.update(self.variable_set_id, None)

    def test_delete_variable_set_success(self):
        """Test successful variable set deletion."""
        # Call the method
        self.variable_sets_service.delete(self.variable_set_id)

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "DELETE", f"/api/v2/varsets/{self.variable_set_id}"
        )

    def test_delete_variable_set_invalid_id(self):
        """Test variable set deletion with invalid ID."""
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variable_sets_service.delete("")

    def test_apply_to_workspaces_success(self):
        """Test successful application to workspaces."""
        # Prepare test data
        workspaces = [Workspace(id="ws-1"), Workspace(id="ws-2")]
        options = VariableSetApplyToWorkspacesOptions(workspaces=workspaces)

        # Call the method
        self.variable_sets_service.apply_to_workspaces(self.variable_set_id, options)

        # Verify API call payload
        expected_payload = {
            "data": [
                {"type": "workspaces", "id": "ws-1"},
                {"type": "workspaces", "id": "ws-2"},
            ]
        }
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/workspaces",
            json_body=expected_payload,
        )

    def test_apply_to_workspaces_invalid_params(self):
        """Test applying to workspaces with invalid parameters."""
        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variable_sets_service.apply_to_workspaces(
                "", VariableSetApplyToWorkspacesOptions()
            )

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variable_sets_service.apply_to_workspaces(self.variable_set_id, None)

        # Empty workspaces list
        with pytest.raises(ValueError, match="At least one workspace is required"):
            self.variable_sets_service.apply_to_workspaces(
                self.variable_set_id, VariableSetApplyToWorkspacesOptions(workspaces=[])
            )

        # Workspace without ID
        workspaces = [Workspace(id="")]
        options = VariableSetApplyToWorkspacesOptions(workspaces=workspaces)
        with pytest.raises(ValueError, match="All workspaces must have valid IDs"):
            self.variable_sets_service.apply_to_workspaces(
                self.variable_set_id, options
            )

    def test_remove_from_workspaces_success(self):
        """Test successful removal from workspaces."""
        # Prepare test data
        workspaces = [Workspace(id="ws-1")]
        options = VariableSetRemoveFromWorkspacesOptions(workspaces=workspaces)

        # Call the method
        self.variable_sets_service.remove_from_workspaces(self.variable_set_id, options)

        # Verify API call payload
        expected_payload = {"data": [{"type": "workspaces", "id": "ws-1"}]}
        self.mock_transport.request.assert_called_once_with(
            "DELETE",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/workspaces",
            json_body=expected_payload,
        )

    def test_apply_to_projects_success(self):
        """Test successful application to projects."""
        # Prepare test data
        projects = [Project(id="prj-1"), Project(id="prj-2")]
        options = VariableSetApplyToProjectsOptions(projects=projects)

        # Call the method
        self.variable_sets_service.apply_to_projects(self.variable_set_id, options)

        # Verify API call payload
        expected_payload = {
            "data": [
                {"type": "projects", "id": "prj-1"},
                {"type": "projects", "id": "prj-2"},
            ]
        }
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/projects",
            json_body=expected_payload,
        )

    def test_apply_to_projects_invalid_params(self):
        """Test applying to projects with invalid parameters."""
        # Empty projects list
        with pytest.raises(ValueError, match="At least one project is required"):
            self.variable_sets_service.apply_to_projects(
                self.variable_set_id, VariableSetApplyToProjectsOptions(projects=[])
            )

        # Project without ID
        projects = [Project(id="")]
        options = VariableSetApplyToProjectsOptions(projects=projects)
        with pytest.raises(ValueError, match="All projects must have valid IDs"):
            self.variable_sets_service.apply_to_projects(self.variable_set_id, options)

    def test_remove_from_projects_success(self):
        """Test successful removal from projects."""
        # Prepare test data
        projects = [Project(id="prj-1")]
        options = VariableSetRemoveFromProjectsOptions(projects=projects)

        # Call the method
        self.variable_sets_service.remove_from_projects(self.variable_set_id, options)

        # Verify API call payload
        expected_payload = {"data": [{"type": "projects", "id": "prj-1"}]}
        self.mock_transport.request.assert_called_once_with(
            "DELETE",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/projects",
            json_body=expected_payload,
        )

    def test_update_workspaces_success(self):
        """Test successful workspace update."""
        # Prepare test data
        workspaces = [Workspace(id="ws-1"), Workspace(id="ws-2")]
        options = VariableSetUpdateWorkspacesOptions(workspaces=workspaces)

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_set_id,
                "type": "varsets",
                "attributes": {
                    "name": "test-varset",
                    "global": False,
                },
                "relationships": {
                    "workspaces": {
                        "data": [
                            {"type": "workspaces", "id": "ws-1"},
                            {"type": "workspaces", "id": "ws-2"},
                        ]
                    }
                },
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variable_sets_service.update_workspaces(
            self.variable_set_id, options
        )

        # Assertions
        assert isinstance(result, VariableSet)
        assert len(result.workspaces) == 2

        # Verify API call payload
        expected_payload = {
            "data": {
                "type": "varsets",
                "id": self.variable_set_id,
                "attributes": {"global": False},
                "relationships": {
                    "workspaces": {
                        "data": [
                            {"type": "workspaces", "id": "ws-1"},
                            {"type": "workspaces", "id": "ws-2"},
                        ]
                    }
                },
            }
        }
        expected_params = {"include": "workspaces"}
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/varsets/{self.variable_set_id}",
            json_body=expected_payload,
            params=expected_params,
        )

    def test_update_workspaces_invalid_params(self):
        """Test updating workspaces with invalid parameters."""
        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variable_sets_service.update_workspaces(
                "", VariableSetUpdateWorkspacesOptions()
            )

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variable_sets_service.update_workspaces(self.variable_set_id, None)


class TestVariableSetVariables:
    """Test cases for Variable Set Variables resource."""

    def setup_method(self):
        """Setup method that runs before each test."""
        self.mock_transport = Mock()
        self.variables_service = VariableSetVariables(self.mock_transport)
        self.variable_set_id = "varset-test123"
        self.variable_id = "var-test123"

    def test_variable_set_variables_service_init(self):
        """Test Variable Set Variables service initialization."""
        assert self.variables_service.t == self.mock_transport

    def test_list_variables_success(self):
        """Test successful listing of variables."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "var-123",
                    "type": "vars",
                    "attributes": {
                        "key": "TF_VAR_test",
                        "value": "test-value",
                        "description": "Test variable",
                        "category": "terraform",
                        "hcl": False,
                        "sensitive": False,
                        "version-id": "v1",
                    },
                    "relationships": {
                        "varset": {
                            "data": {"id": self.variable_set_id, "type": "varsets"}
                        }
                    },
                }
            ]
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variables_service.list(self.variable_set_id)

        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], VariableSetVariable)
        assert result[0].id == "var-123"
        assert result[0].key == "TF_VAR_test"
        assert result[0].value == "test-value"
        assert result[0].description == "Test variable"
        assert result[0].category == CategoryType.TERRAFORM
        assert result[0].hcl is False
        assert result[0].sensitive is False

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/vars",
            params={},
        )

    def test_list_variables_invalid_varset_id(self):
        """Test listing variables with invalid variable set ID."""
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variables_service.list("")

    def test_create_variable_success(self):
        """Test successful variable creation."""
        # Prepare test data
        options = VariableSetVariableCreateOptions(
            key="NEW_VAR",
            value="new-value",
            description="New variable",
            category=CategoryType.ENV,
            hcl=False,
            sensitive=True,
        )

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "var-new123",
                "type": "vars",
                "attributes": {
                    "key": "NEW_VAR",
                    "value": "new-value",
                    "description": "New variable",
                    "category": "env",
                    "hcl": False,
                    "sensitive": True,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variables_service.create(self.variable_set_id, options)

        # Assertions
        assert isinstance(result, VariableSetVariable)
        assert result.id == "var-new123"
        assert result.key == "NEW_VAR"
        assert result.value == "new-value"
        assert result.category == CategoryType.ENV
        assert result.sensitive is True

        # Verify API call payload
        expected_payload = {
            "data": {
                "type": "vars",
                "attributes": {
                    "key": "NEW_VAR",
                    "value": "new-value",
                    "description": "New variable",
                    "category": "env",
                    "hcl": False,
                    "sensitive": True,
                },
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/vars",
            json_body=expected_payload,
        )

    def test_create_variable_invalid_params(self):
        """Test variable creation with invalid parameters."""
        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variables_service.create(
                "",
                VariableSetVariableCreateOptions(
                    key="test", category=CategoryType.TERRAFORM
                ),
            )

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variables_service.create(self.variable_set_id, None)

        # Missing key
        with pytest.raises(ValueError, match="Variable key is required"):
            self.variables_service.create(
                self.variable_set_id,
                VariableSetVariableCreateOptions(
                    key="", category=CategoryType.TERRAFORM
                ),
            )

    def test_read_variable_success(self):
        """Test successful variable read."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_id,
                "type": "vars",
                "attributes": {
                    "key": "READ_VAR",
                    "value": "read-value",
                    "description": "Variable for reading",
                    "category": "terraform",
                    "hcl": True,
                    "sensitive": False,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variables_service.read(self.variable_set_id, self.variable_id)

        # Assertions
        assert isinstance(result, VariableSetVariable)
        assert result.id == self.variable_id
        assert result.key == "READ_VAR"
        assert result.hcl is True

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/vars/{self.variable_id}",
        )

    def test_read_variable_invalid_params(self):
        """Test reading variable with invalid parameters."""
        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variables_service.read("", self.variable_id)

        # Invalid variable ID
        with pytest.raises(ValueError, match="Variable ID is required"):
            self.variables_service.read(self.variable_set_id, "")

    def test_update_variable_success(self):
        """Test successful variable update."""
        # Prepare test data
        options = VariableSetVariableUpdateOptions(
            key="UPDATED_VAR",
            value="updated-value",
            description="Updated variable",
            hcl=True,
            sensitive=False,
        )

        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": self.variable_id,
                "type": "vars",
                "attributes": {
                    "key": "UPDATED_VAR",
                    "value": "updated-value",
                    "description": "Updated variable",
                    "category": "terraform",
                    "hcl": True,
                    "sensitive": False,
                },
                "relationships": {},
            }
        }
        self.mock_transport.request.return_value = mock_response

        # Call the method
        result = self.variables_service.update(
            self.variable_set_id, self.variable_id, options
        )

        # Assertions
        assert result.key == "UPDATED_VAR"
        assert result.value == "updated-value"
        assert result.hcl is True

        # Verify API call payload
        expected_payload = {
            "data": {
                "type": "vars",
                "id": self.variable_id,
                "attributes": {
                    "key": "UPDATED_VAR",
                    "value": "updated-value",
                    "description": "Updated variable",
                    "hcl": True,
                    "sensitive": False,
                },
            }
        }
        self.mock_transport.request.assert_called_once_with(
            "PATCH",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/vars/{self.variable_id}",
            json_body=expected_payload,
        )

    def test_update_variable_invalid_params(self):
        """Test variable update with invalid parameters."""
        options = VariableSetVariableUpdateOptions(key="test")

        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variables_service.update("", self.variable_id, options)

        # Invalid variable ID
        with pytest.raises(ValueError, match="Variable ID is required"):
            self.variables_service.update(self.variable_set_id, "", options)

        # Invalid options
        with pytest.raises(ValueError, match="Options are required"):
            self.variables_service.update(self.variable_set_id, self.variable_id, None)

    def test_delete_variable_success(self):
        """Test successful variable deletion."""
        # Call the method
        self.variables_service.delete(self.variable_set_id, self.variable_id)

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "DELETE",
            f"/api/v2/varsets/{self.variable_set_id}/relationships/vars/{self.variable_id}",
        )

    def test_delete_variable_invalid_params(self):
        """Test variable deletion with invalid parameters."""
        # Invalid variable set ID
        with pytest.raises(ValueError, match="Variable set ID is required"):
            self.variables_service.delete("", self.variable_id)

        # Invalid variable ID
        with pytest.raises(ValueError, match="Variable ID is required"):
            self.variables_service.delete(self.variable_set_id, "")
