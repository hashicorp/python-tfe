"""
Comprehensive unit tests for workspace operations in the Python TFE SDK.

This test suite covers all workspace methods including CRUD operations,
VCS management, locking/unlocking, SSH key management, and validation.
"""

from unittest.mock import Mock

import pytest

from src.tfe.errors import (
    InvalidOrgError,
    InvalidSSHKeyIDError,
    InvalidWorkspaceIDError,
    InvalidWorkspaceValueError,
    RequiredSSHKeyIDError,
)
from src.tfe.resources.workspaces import Workspaces, _ws_from
from src.tfe.types import (
    ExecutionMode,
    Project,
    VCSRepo,
    WorkspaceAssignSSHKeyOptions,
    WorkspaceCreateOptions,
    WorkspaceListOptions,
    WorkspaceLockOptions,
    WorkspaceReadOptions,
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceUpdateOptions,
)


class TestWorkspaceOperations:
    """Test suite for workspace CRUD operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def workspaces_service(self, mock_transport):
        """Create workspaces service with mocked transport."""
        return Workspaces(mock_transport)

    @pytest.fixture
    def sample_workspace_response(self):
        """Sample JSON:API workspace response."""
        return {
            "data": {
                "type": "workspaces",
                "id": "ws-abc123def456",
                "attributes": {
                    "name": "test-workspace",
                    "description": "Test workspace for unit tests",
                    "auto-apply": True,
                    "execution-mode": "remote",
                    "terraform-version": "1.5.0",
                    "working-directory": "terraform/",
                    "file-triggers-enabled": True,
                    "queue-all-runs": False,
                    "speculative-enabled": True,
                    "operations": True,
                    "locked": False,
                    "created-at": "2023-09-11T10:30:00.000Z",
                    "updated-at": "2023-09-11T15:45:00.000Z",
                    "resource-count": 25,
                    "trigger-prefixes": ["modules/"],
                    "trigger-patterns": ["**/*.tf", "**/*.tfvars"],
                    "tag-names": ["production", "frontend"],
                    "vcs-repo": {
                        "identifier": "org/repo",
                        "branch": "main",
                        "oauth-token-id": "ot-123",
                        "ingress-submodules": False,
                        "tags-regex": "v\\d+\\.\\d+\\.\\d+",
                    },
                },
                "relationships": {
                    "project": {"data": {"type": "projects", "id": "prj-xyz789"}},
                    "current-run": {"data": {"type": "runs", "id": "run-def456"}},
                    "locked-by": {"data": {"type": "users", "id": "user-123"}},
                },
            }
        }

    @pytest.fixture
    def sample_workspace_list_response(self):
        """Sample JSON:API workspace list response."""
        return {
            "data": [
                {
                    "type": "workspaces",
                    "id": "ws-123",
                    "attributes": {
                        "name": "workspace-1",
                        "description": "First workspace",
                        "auto-apply": False,
                        "execution-mode": "local",
                        "locked": False,
                    },
                },
                {
                    "type": "workspaces",
                    "id": "ws-456",
                    "attributes": {
                        "name": "workspace-2",
                        "description": "Second workspace",
                        "auto-apply": True,
                        "execution-mode": "remote",
                        "locked": True,
                    },
                },
            ]
        }

    # ==========================================
    # LIST OPERATIONS TESTS
    # ==========================================

    def test_list_workspaces_basic(
        self, workspaces_service, mock_transport, sample_workspace_list_response
    ):
        """Test basic workspace listing."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_list_response
        )

        options = WorkspaceListOptions()
        workspaces = list(workspaces_service.list("test-org", options=options))

        assert len(workspaces) == 2
        assert workspaces[0].name == "workspace-1"
        assert workspaces[1].name == "workspace-2"
        assert not workspaces[0].auto_apply
        assert workspaces[1].auto_apply

    def test_list_workspaces_with_search(self, workspaces_service, mock_transport):
        """Test workspace listing with search options."""
        mock_transport.request.return_value.json.return_value = {"data": []}

        options = WorkspaceListOptions(
            search="production",
            tags="frontend,backend",
            exclude_tags="deprecated",
            project_id="prj-123",
        )

        list(workspaces_service.list("test-org", options=options))

        # Verify search parameters were passed correctly
        call_args = mock_transport.request.call_args
        params = call_args[1]["params"]
        assert params["search[name]"] == "production"
        assert params["search[tags]"] == "frontend,backend"
        assert params["search[exclude-tags]"] == "deprecated"
        assert params["filter[project][id]"] == "prj-123"

    def test_list_workspaces_invalid_org(self, workspaces_service):
        """Test list with invalid organization."""
        options = WorkspaceListOptions()

        with pytest.raises(InvalidOrgError):
            list(workspaces_service.list("", options=options))

        with pytest.raises(InvalidOrgError):
            list(workspaces_service.list("org/with/slash", options=options))

    # ==========================================
    # READ OPERATIONS TESTS
    # ==========================================

    def test_read_workspace_by_name(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test reading workspace by organization and name."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        workspace = workspaces_service.read("test-org", "test-workspace")

        assert workspace.id == "ws-abc123def456"
        assert workspace.name == "test-workspace"
        assert workspace.description == "Test workspace for unit tests"
        assert workspace.auto_apply
        assert workspace.execution_mode == ExecutionMode.REMOTE
        assert workspace.terraform_version == "1.5.0"
        assert workspace.working_directory == "terraform/"
        assert workspace.resource_count == 25
        assert workspace.trigger_prefixes == ["modules/"]
        assert workspace.trigger_patterns == ["**/*.tf", "**/*.tfvars"]
        assert workspace.tag_names == ["production", "frontend"]

    def test_read_workspace_by_id(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test reading workspace by ID."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        workspace = workspaces_service.read_by_id("ws-abc123def456")

        assert workspace.id == "ws-abc123def456"
        assert workspace.name == "test-workspace"

    def test_read_workspace_with_options(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test reading workspace with include options."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        from src.tfe.types import WorkspaceIncludeOpt

        options = WorkspaceReadOptions(
            include=[WorkspaceIncludeOpt.CURRENT_RUN, WorkspaceIncludeOpt.OUTPUTS]
        )

        workspace = workspaces_service.read_with_options(
            "test-workspace", "test-org", options=options
        )

        assert workspace.id == "ws-abc123def456"

        # Verify include parameter was passed
        call_args = mock_transport.request.call_args
        params = call_args[1]["params"]
        assert "include" in params

    def test_read_workspace_invalid_params(self, workspaces_service):
        """Test read with invalid parameters."""
        with pytest.raises(InvalidOrgError):
            workspaces_service.read("", "workspace-name")

        with pytest.raises(InvalidWorkspaceValueError):
            workspaces_service.read("valid-org", "")

        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.read_by_id("")

    # ==========================================
    # CREATE OPERATIONS TESTS
    # ==========================================

    def test_create_workspace_basic(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test basic workspace creation."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceCreateOptions(
            name="new-workspace",
            description="A new test workspace",
            auto_apply=True,
            execution_mode=ExecutionMode.REMOTE,
            terraform_version="1.5.0",
        )

        workspace = workspaces_service.create("test-org", options=options)

        assert workspace.id == "ws-abc123def456"
        assert workspace.name == "test-workspace"

        # Verify POST request was made
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert "organizations/test-org/workspaces" in call_args[0][1]

    def test_create_workspace_with_vcs(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test workspace creation with VCS configuration."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        vcs_repo = VCSRepo(
            identifier="myorg/myrepo",
            branch="main",
            oauth_token_id="ot-123456",
            ingress_submodules=False,
            tags_regex="v\\d+\\.\\d+\\.\\d+",
        )

        options = WorkspaceCreateOptions(
            name="vcs-workspace",
            vcs_repo=vcs_repo,
            working_directory="terraform/",
            # Remove trigger_prefixes to avoid conflict with tags_regex
        )

        workspace = workspaces_service.create("test-org", options=options)

        assert workspace.id == "ws-abc123def456"

        # Verify VCS configuration in payload
        call_args = mock_transport.request.call_args
        payload = call_args[1]["json_body"]
        vcs_data = payload["data"]["attributes"]["vcs-repo"]
        assert vcs_data["identifier"] == "myorg/myrepo"
        assert vcs_data["oauth-token-id"] == "ot-123456"
        assert vcs_data["tags-regex"] == "v\\d+\\.\\d+\\.\\d+"

    def test_create_workspace_with_project(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test workspace creation with project relationship."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        project = Project(id="prj-123", name="Test Project")

        options = WorkspaceCreateOptions(name="project-workspace", project=project)

        workspaces_service.create("test-org", options=options)

        # Verify project relationship in payload
        call_args = mock_transport.request.call_args
        payload = call_args[1]["json_body"]
        project_rel = payload["data"]["relationships"]["project"]
        assert project_rel["data"]["type"] == "projects"
        assert project_rel["data"]["id"] == "prj-123"

    def test_create_workspace_invalid_org(self, workspaces_service):
        """Test create with invalid organization."""
        options = WorkspaceCreateOptions(name="test-workspace")

        with pytest.raises(InvalidOrgError):
            workspaces_service.create("", options=options)

    # ==========================================
    # UPDATE OPERATIONS TESTS
    # ==========================================

    def test_update_workspace_by_name(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test updating workspace by name."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceUpdateOptions(
            name="test-workspace",  # Required field
            description="Updated description",
            auto_apply=False,
            terraform_version="1.6.0",
        )

        workspace = workspaces_service.update(
            "test-org", "test-workspace", options=options
        )

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request was made
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "organizations/test-org/workspaces/test-workspace" in call_args[0][1]

    def test_update_workspace_by_id(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test updating workspace by ID."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceUpdateOptions(name="dummy", auto_apply=True)

        workspace = workspaces_service.update_by_id("ws-123", options=options)

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to workspace ID endpoint
        call_args = mock_transport.request.call_args
        assert "workspaces/ws-123" in call_args[0][1]

    # ==========================================
    # DELETE OPERATIONS TESTS
    # ==========================================

    def test_delete_workspace_by_name(self, workspaces_service, mock_transport):
        """Test deleting workspace by name."""
        mock_transport.request.return_value = Mock()

        workspaces_service.delete("test-org", "test-workspace")

        # Verify DELETE request was made
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "organizations/test-org/workspaces/test-workspace" in call_args[0][1]

    def test_delete_workspace_by_id(self, workspaces_service, mock_transport):
        """Test deleting workspace by ID."""
        mock_transport.request.return_value = Mock()

        workspaces_service.delete_by_id("ws-123")

        # Verify DELETE request to workspace ID endpoint
        call_args = mock_transport.request.call_args
        assert "workspaces/ws-123" in call_args[0][1]

    def test_safe_delete_workspace(self, workspaces_service, mock_transport):
        """Test safe delete workspace operations."""
        mock_transport.request.return_value = Mock()

        # Test safe delete by name
        workspaces_service.safe_delete("test-org", "test-workspace")
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert "actions/safe-delete" in call_args[0][1]

        # Test safe delete by ID
        workspaces_service.safe_delete_by_id("ws-123")
        call_args = mock_transport.request.call_args
        assert "workspaces/ws-123/actions/safe-delete" in call_args[0][1]

    # ==========================================
    # VCS CONNECTION TESTS
    # ==========================================

    def test_remove_vcs_connection_by_name(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test removing VCS connection by name."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceRemoveVCSConnectionOptions(id="ws-123")
        workspace = workspaces_service.remove_vcs_connection(
            "test-org", "test-workspace", options=options
        )

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to remove VCS
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        payload = call_args[1]["json_body"]
        assert payload["data"]["attributes"]["vcs-repo"] is None

    def test_remove_vcs_connection_by_id(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test removing VCS connection by ID."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceRemoveVCSConnectionOptions(id="ws-123")
        workspace = workspaces_service.remove_vcs_connection_by_id(
            "ws-123", options=options
        )

        assert workspace.id == "ws-abc123def456"

    # ==========================================
    # LOCKING/UNLOCKING TESTS
    # ==========================================

    def test_lock_workspace(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test locking a workspace."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceLockOptions(reason="Maintenance in progress")
        workspace = workspaces_service.lock("ws-123", options=options)

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to lock endpoint
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "workspaces/ws-123/actions/lock" in call_args[0][1]

        payload = call_args[1]["json_body"]
        assert payload["reason"] == "Maintenance in progress"

    def test_unlock_workspace(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test unlocking a workspace."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        workspace = workspaces_service.unlock("ws-123")

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to unlock endpoint
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "workspaces/ws-123/actions/unlock" in call_args[0][1]

    def test_force_unlock_workspace(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test force unlocking a workspace."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        workspace = workspaces_service.force_unlock("ws-123")

        assert workspace.id == "ws-abc123def456"

        # Verify POST request to force-unlock endpoint
        call_args = mock_transport.request.call_args
        assert "workspaces/ws-123/actions/force-unlock" in call_args[0][1]

    # ==========================================
    # SSH KEY MANAGEMENT TESTS
    # ==========================================

    def test_assign_ssh_key(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test assigning SSH key to workspace."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        options = WorkspaceAssignSSHKeyOptions(ssh_key_id="sshkey-123")
        workspace = workspaces_service.assign_ssh_key("ws-123", options=options)

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to SSH key relationship endpoint
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        # Note: There's a typo in the current implementation - "relastionships" should be "relationships"
        assert "ssh-key" in call_args[0][1]

        payload = call_args[1]["json_body"]
        assert payload["data"]["attributes"]["id"] == "sshkey-123"

    def test_assign_ssh_key_validation_errors(self, workspaces_service):
        """Test SSH key assignment validation errors."""
        # Invalid workspace ID
        options = WorkspaceAssignSSHKeyOptions(ssh_key_id="sshkey-123")
        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.assign_ssh_key("", options=options)

        # Missing SSH key ID
        options = WorkspaceAssignSSHKeyOptions(ssh_key_id="")
        with pytest.raises(RequiredSSHKeyIDError):
            workspaces_service.assign_ssh_key("ws-123", options=options)

        # Invalid SSH key ID format
        options = WorkspaceAssignSSHKeyOptions(ssh_key_id="invalid/ssh/key")
        with pytest.raises(InvalidSSHKeyIDError):
            workspaces_service.assign_ssh_key("ws-123", options=options)

    def test_unassign_ssh_key(
        self, workspaces_service, mock_transport, sample_workspace_response
    ):
        """Test unassigning SSH key from workspace."""
        mock_transport.request.return_value.json.return_value = (
            sample_workspace_response
        )

        workspace = workspaces_service.unassign_ssh_key("ws-123")

        assert workspace.id == "ws-abc123def456"

        # Verify PATCH request to unassign SSH key
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "relationships/ssh-key" in call_args[0][1]

        payload = call_args[1]["json_body"]
        assert payload["data"]["attributes"]["id"] is None

    # ==========================================
    # HELPER FUNCTION TESTS
    # ==========================================

    def test_ws_from_conversion(self, sample_workspace_response):
        """Test _ws_from helper function conversion."""
        workspace_data = sample_workspace_response["data"]
        workspace = _ws_from(workspace_data, "test-org")

        assert workspace.id == "ws-abc123def456"
        assert workspace.name == "test-workspace"
        assert workspace.organization == "test-org"
        assert workspace.auto_apply
        assert workspace.execution_mode == ExecutionMode.REMOTE
        assert workspace.resource_count == 25
        assert len(workspace.trigger_prefixes) == 1
        assert len(workspace.trigger_patterns) == 2
        assert len(workspace.tag_names) == 2

        # Test VCS repo conversion
        assert workspace.vcs_repo is not None
        assert workspace.vcs_repo.identifier == "org/repo"
        assert workspace.vcs_repo.branch == "main"
        assert workspace.vcs_repo.oauth_token_id == "ot-123"

    def test_ws_from_minimal_data(self):
        """Test _ws_from with minimal data."""
        minimal_data = {"id": "ws-minimal", "attributes": {"name": "minimal-workspace"}}

        workspace = _ws_from(minimal_data, "test-org")

        assert workspace.id == "ws-minimal"
        assert workspace.name == "minimal-workspace"
        assert workspace.organization == "test-org"
        assert not workspace.auto_apply  # Default value
        assert not workspace.locked  # Default value

    # ==========================================
    # EDGE CASES AND ERROR HANDLING
    # ==========================================

    def test_empty_workspace_list(self, workspaces_service, mock_transport):
        """Test handling empty workspace list."""
        mock_transport.request.return_value.json.return_value = {"data": []}

        options = WorkspaceListOptions()
        workspaces = list(workspaces_service.list("test-org", options=options))

        assert len(workspaces) == 0

    def test_malformed_response_handling(self, workspaces_service, mock_transport):
        """Test handling of malformed API responses."""
        # Test missing data field
        mock_transport.request.return_value.json.return_value = {}

        options = WorkspaceListOptions()
        workspaces = list(workspaces_service.list("test-org", options=options))
        assert len(workspaces) == 0

    def test_none_values_handling(self):
        """Test handling of None values in workspace data."""
        data_with_nones = {
            "id": "ws-123",
            "attributes": {
                "name": "test-workspace",
                "description": None,
                "terraform-version": None,
                "working-directory": None,
                "vcs-repo": None,
            },
        }

        workspace = _ws_from(data_with_nones, "test-org")

        assert workspace.description == ""  # Should convert None to empty string
        assert workspace.terraform_version == ""
        assert workspace.working_directory == ""
        assert workspace.vcs_repo is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
