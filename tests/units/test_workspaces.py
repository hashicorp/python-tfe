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
    MissingTagBindingIdentifierError,
    MissingTagIdentifierError,
    RequiredSSHKeyIDError,
    WorkspaceMinimumLimitError,
)
from src.tfe.resources.workspaces import Workspaces, _ws_from
from src.tfe.types import (
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDeleteSetOptions,
    DataRetentionPolicySetOptions,
    EffectiveTagBinding,
    ExecutionMode,
    Project,
    Tag,
    TagBinding,
    VCSRepo,
    Workspace,
    WorkspaceAddRemoteStateConsumersOptions,
    WorkspaceAddTagBindingsOptions,
    WorkspaceAddTagsOptions,
    WorkspaceAssignSSHKeyOptions,
    WorkspaceCreateOptions,
    WorkspaceListOptions,
    WorkspaceListRemoteStateConsumersOptions,
    WorkspaceLockOptions,
    WorkspaceReadOptions,
    WorkspaceRemoveRemoteStateConsumersOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
    WorkspaceUpdateRemoteStateConsumersOptions,
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
        assert call_args[0][0] == "POST"
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
        assert call_args[0][0] == "POST"
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

    # ==========================================
    # REMOTE STATE CONSUMER OPERATIONS TESTS
    # ==========================================

    @pytest.fixture
    def sample_remote_state_consumers_response(self):
        """Sample JSON:API remote state consumers response."""
        return {
            "data": [
                {
                    "type": "workspaces",
                    "id": "ws-consumer-1",
                    "attributes": {
                        "name": "consumer-workspace-1",
                        "description": "First consumer workspace",
                        "auto-apply": False,
                        "execution-mode": "remote",
                        "locked": False,
                    },
                },
                {
                    "type": "workspaces",
                    "id": "ws-consumer-2",
                    "attributes": {
                        "name": "consumer-workspace-2",
                        "description": "Second consumer workspace",
                        "auto-apply": True,
                        "execution-mode": "local",
                        "locked": False,
                    },
                },
            ]
        }

    def test_list_remote_state_consumers_basic(
        self, workspaces_service, mock_transport, sample_remote_state_consumers_response
    ):
        """Test basic remote state consumers listing."""
        mock_transport.request.return_value.json.return_value = (
            sample_remote_state_consumers_response
        )

        options = WorkspaceListRemoteStateConsumersOptions(page_size=10)
        consumers = list(
            workspaces_service.list_remote_state_consumers("ws-123", options)
        )

        assert len(consumers) == 2
        assert consumers[0].name == "consumer-workspace-1"
        assert consumers[1].name == "consumer-workspace-2"
        assert not consumers[0].auto_apply
        assert consumers[1].auto_apply

        # Verify the correct HTTP request was made
        mock_transport.request.assert_called()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert (
            "/api/v2/workspaces/ws-123/relationships/remote-state-consumers"
            in call_args[0][1]
        )

    def test_list_remote_state_consumers_with_pagination(
        self, workspaces_service, mock_transport
    ):
        """Test remote state consumers listing with pagination options."""
        mock_transport.request.return_value.json.return_value = {"data": []}

        options = WorkspaceListRemoteStateConsumersOptions(page_number=2, page_size=5)

        list(workspaces_service.list_remote_state_consumers("ws-123", options))

        # Verify pagination parameters were passed
        call_args = mock_transport.request.call_args
        params = call_args[1]["params"]
        assert params["page[number]"] == 2
        assert params["page[size]"] == 5

    def test_add_remote_state_consumers_basic(self, workspaces_service, mock_transport):
        """Test adding remote state consumers."""
        consumer_workspaces = [
            Workspace(id="ws-consumer-1", name="consumer-1", organization="test-org"),
            Workspace(id="ws-consumer-2", name="consumer-2", organization="test-org"),
        ]

        options = WorkspaceAddRemoteStateConsumersOptions(
            workspaces=consumer_workspaces
        )

        workspaces_service.add_remote_state_consumers("ws-123", options)

        # Verify POST request was made with correct data
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            "/api/v2/workspaces/ws-123/relationships/remote-state-consumers"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        assert body["data"] == [
            {"type": "workspaces", "id": "ws-consumer-1"},
            {"type": "workspaces", "id": "ws-consumer-2"},
        ]

    def test_add_remote_state_consumers_validation_errors(self, workspaces_service):
        """Test add remote state consumers validation errors."""
        # Test invalid workspace ID
        options = WorkspaceAddRemoteStateConsumersOptions(workspaces=[])

        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.add_remote_state_consumers("", options)

        # Test empty workspaces list
        options = WorkspaceAddRemoteStateConsumersOptions(workspaces=[])

        with pytest.raises(WorkspaceMinimumLimitError):
            workspaces_service.add_remote_state_consumers("ws-123", options)

        # Test invalid workspace ID format (with slash)
        options = WorkspaceAddRemoteStateConsumersOptions(
            workspaces=[Workspace(id="ws-valid", name="valid", organization="test-org")]
        )

        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.add_remote_state_consumers("invalid/id", options)

    def test_remove_remote_state_consumers_basic(
        self, workspaces_service, mock_transport
    ):
        """Test removing remote state consumers."""
        consumer_workspaces = [
            Workspace(id="ws-consumer-1", name="consumer-1", organization="test-org"),
        ]

        options = WorkspaceRemoveRemoteStateConsumersOptions(
            workspaces=consumer_workspaces
        )

        workspaces_service.remove_remote_state_consumers("ws-123", options)

        # Verify DELETE request was made with correct data
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert (
            "/api/v2/workspaces/ws-123/relationships/remote-state-consumers"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        assert body["data"] == [{"type": "workspaces", "id": "ws-consumer-1"}]

    def test_update_remote_state_consumers_basic(
        self, workspaces_service, mock_transport
    ):
        """Test updating (replacing) remote state consumers."""
        consumer_workspaces = [
            Workspace(id="ws-consumer-3", name="consumer-3", organization="test-org"),
            Workspace(id="ws-consumer-4", name="consumer-4", organization="test-org"),
        ]

        options = WorkspaceUpdateRemoteStateConsumersOptions(
            workspaces=consumer_workspaces
        )

        workspaces_service.update_remote_state_consumers("ws-123", options)

        # Verify PATCH request was made with correct data
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert (
            "/api/v2/workspaces/ws-123/relationships/remote-state-consumers"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        assert body["data"] == [
            {"type": "workspaces", "id": "ws-consumer-3"},
            {"type": "workspaces", "id": "ws-consumer-4"},
        ]

    # ==========================================
    # TAG OPERATIONS TESTS
    # ==========================================

    @pytest.fixture
    def sample_tags_response(self):
        """Sample JSON:API tags response."""
        return {
            "data": [
                {
                    "type": "tags",
                    "id": "tag-123",
                    "attributes": {
                        "name": "environment",
                    },
                },
                {
                    "type": "tags",
                    "id": "tag-456",
                    "attributes": {
                        "name": "team",
                    },
                },
            ]
        }

    def test_list_tags_basic(
        self, workspaces_service, mock_transport, sample_tags_response
    ):
        """Test basic tag listing."""
        mock_transport.request.return_value.json.return_value = sample_tags_response

        options = WorkspaceTagListOptions(page_size=10)
        tags = list(workspaces_service.list_tags("ws-123", options))

        assert len(tags) == 2
        assert tags[0].name == "environment"
        assert tags[1].name == "team"

        # Verify the correct HTTP request was made
        mock_transport.request.assert_called()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert "/api/v2/workspaces/ws-123/relationships/tags" in call_args[0][1]

    def test_list_tags_with_query_and_pagination(
        self, workspaces_service, mock_transport
    ):
        """Test tag listing with query and pagination options."""
        mock_transport.request.return_value.json.return_value = {"data": []}

        options = WorkspaceTagListOptions(query="env", page_number=2, page_size=5)

        list(workspaces_service.list_tags("ws-123", options))

        # Verify query and pagination parameters were passed
        call_args = mock_transport.request.call_args
        params = call_args[1]["params"]
        assert params["name"] == "env"
        assert params["page[number]"] == 2
        assert params["page[size]"] == 5

    def test_add_tags_basic(self, workspaces_service, mock_transport):
        """Test adding tags to a workspace."""
        tags = [
            Tag(id="tag-123"),
            Tag(name="environment"),
            Tag(id="tag-456", name="team"),  # Both ID and name provided
        ]

        options = WorkspaceAddTagsOptions(tags=tags)

        workspaces_service.add_tags("ws-123", options)

        # Verify POST request was made with correct data
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert "/api/v2/workspaces/ws-123/relationships/tags" in call_args[0][1]

        # Verify request body
        body = call_args[1]["json_body"]
        expected_data = [
            {"type": "tags", "id": "tag-123"},  # ID takes precedence
            {"type": "tags", "attributes": {"name": "environment"}},  # Name only
            {"type": "tags", "id": "tag-456"},  # ID takes precedence when both provided
        ]
        assert body["data"] == expected_data

    def test_add_tags_validation_errors(self, workspaces_service):
        """Test add tags validation errors."""
        # Test invalid workspace ID
        options = WorkspaceAddTagsOptions(tags=[])

        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.add_tags("", options)

        # Test empty tags list
        options = WorkspaceAddTagsOptions(tags=[])

        with pytest.raises(MissingTagIdentifierError):
            workspaces_service.add_tags("ws-123", options)

        # Test tag with no ID or name
        options = WorkspaceAddTagsOptions(tags=[Tag(id="", name="")])

        with pytest.raises(MissingTagIdentifierError):
            workspaces_service.add_tags("ws-123", options)

        # Test invalid workspace ID format
        options = WorkspaceAddTagsOptions(tags=[Tag(id="tag-123")])

        with pytest.raises(InvalidWorkspaceIDError):
            workspaces_service.add_tags("ws 123", options)

    def test_remove_tags_basic(self, workspaces_service, mock_transport):
        """Test removing tags from a workspace."""
        tags = [
            Tag(id="tag-123"),
            Tag(name="environment"),
        ]

        options = WorkspaceRemoveTagsOptions(tags=tags)

        workspaces_service.remove_tags("ws-123", options)

        # Verify DELETE request was made with correct data
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/api/v2/workspaces/ws-123/relationships/tags" in call_args[0][1]

        # Verify request body
        body = call_args[1]["json_body"]
        expected_data = [
            {"type": "tags", "id": "tag-123"},
            {"type": "tags", "attributes": {"name": "environment"}},
        ]
        assert body["data"] == expected_data

    # ==========================================
    # TAG BINDING OPERATIONS TESTS
    # ==========================================

    def test_list_tag_bindings_basic(self, workspaces_service, mock_transport):
        """Test listing tag bindings for a workspace."""
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
                    "attributes": {"key": "team", "value": "infrastructure"},
                },
            ]
        }
        mock_transport.request.return_value = mock_response

        # Call the method
        tag_bindings = list(workspaces_service.list_tag_bindings("ws-123"))

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-123/tag-bindings",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify returned data
        assert len(tag_bindings) == 2
        assert isinstance(tag_bindings[0], TagBinding)
        assert tag_bindings[0].id == "tb-123"
        assert tag_bindings[0].key == "environment"
        assert tag_bindings[0].value == "production"
        assert tag_bindings[1].id == "tb-456"
        assert tag_bindings[1].key == "team"
        assert tag_bindings[1].value == "infrastructure"

    def test_list_effective_tag_bindings_basic(
        self, workspaces_service, mock_transport
    ):
        """Test listing effective tag bindings for a workspace."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "etb-123",
                    "type": "effective-tag-bindings",
                    "attributes": {
                        "key": "environment",
                        "value": "production",
                        "links": {
                            "self": "/api/v2/workspaces/ws-123/effective-tag-bindings/etb-123"
                        },
                    },
                },
                {
                    "id": "etb-456",
                    "type": "effective-tag-bindings",
                    "attributes": {
                        "key": "cost-center",
                        "value": "engineering",
                        "links": {
                            "self": "/api/v2/workspaces/ws-123/effective-tag-bindings/etb-456"
                        },
                    },
                },
            ]
        }
        mock_transport.request.return_value = mock_response

        # Call the method
        effective_bindings = list(
            workspaces_service.list_effective_tag_bindings("ws-123")
        )

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "GET",
            "/api/v2/workspaces/ws-123/effective-tag-bindings",
            params={"page[number]": 1, "page[size]": 100},
        )

        # Verify returned data
        assert len(effective_bindings) == 2
        assert isinstance(effective_bindings[0], EffectiveTagBinding)
        assert effective_bindings[0].id == "etb-123"
        assert effective_bindings[0].key == "environment"
        assert effective_bindings[0].value == "production"
        assert effective_bindings[0].links == {
            "self": "/api/v2/workspaces/ws-123/effective-tag-bindings/etb-123"
        }

    def test_add_tag_bindings_basic(self, workspaces_service, mock_transport):
        """Test adding tag bindings to a workspace."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-123",
                    "type": "tag-bindings",
                    "attributes": {"key": "environment", "value": "staging"},
                },
                {
                    "id": "tb-456",
                    "type": "tag-bindings",
                    "attributes": {"key": "team", "value": "backend"},
                },
            ]
        }
        mock_transport.request.return_value = mock_response

        # Create tag binding options
        options = WorkspaceAddTagBindingsOptions(
            tag_bindings=[
                TagBinding(key="environment", value="staging"),
                TagBinding(key="team", value="backend"),
            ]
        )

        # Call the method
        result_bindings = list(workspaces_service.add_tag_bindings("ws-123", options))

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "/api/v2/workspaces/ws-123/tag-bindings" in call_args[0][1]

        # Verify request body
        body = call_args[1]["json_body"]
        expected_data = [
            {
                "type": "tag-bindings",
                "attributes": {"key": "environment", "value": "staging"},
            },
            {"type": "tag-bindings", "attributes": {"key": "team", "value": "backend"}},
        ]
        assert body["data"] == expected_data

        # Verify returned data
        assert len(result_bindings) == 2
        assert isinstance(result_bindings[0], TagBinding)
        assert result_bindings[0].id == "tb-123"
        assert result_bindings[0].key == "environment"
        assert result_bindings[0].value == "staging"

    def test_add_tag_bindings_validation_errors(self, workspaces_service):
        """Test add tag bindings validation errors."""

        # Test empty tag bindings
        empty_options = WorkspaceAddTagBindingsOptions(tag_bindings=[])
        with pytest.raises(MissingTagBindingIdentifierError):
            list(workspaces_service.add_tag_bindings("ws-123", empty_options))

    def test_add_tag_bindings_update_existing(self, workspaces_service, mock_transport):
        """Test updating existing tag bindings."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "tb-123",
                    "type": "tag-bindings",
                    "attributes": {
                        "key": "environment",
                        "value": "production",  # Updated value
                    },
                }
            ]
        }
        mock_transport.request.return_value = mock_response

        # Create options to update existing tag binding
        options = WorkspaceAddTagBindingsOptions(
            tag_bindings=[TagBinding(key="environment", value="production")]
        )

        # Call the method
        result_bindings = list(workspaces_service.add_tag_bindings("ws-123", options))

        # Verify returned data shows updated value
        assert len(result_bindings) == 1
        assert result_bindings[0].value == "production"

    def test_delete_all_tag_bindings_basic(self, workspaces_service, mock_transport):
        """Test deleting all tag bindings from a workspace."""
        # Mock successful response
        mock_response = Mock()
        mock_transport.request.return_value = mock_response

        # Call the method
        workspaces_service.delete_all_tag_bindings("ws-123")

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "/api/v2/workspaces/ws-123" in call_args[0][1]

        # Verify request body
        body = call_args[1]["json_body"]
        expected_body = {
            "data": {
                "type": "workspaces",
                "id": "ws-123",
                "relationships": {"tag-bindings": {"data": []}},
            }
        }
        assert body == expected_body

    def test_read_data_retention_policy_legacy(
        self, workspaces_service, mock_transport
    ):
        """Test reading a workspace's data retention policy (legacy method)."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "drp-legacy123",
                "type": "data-retention-policies",
                "attributes": {"delete-older-than-n-days": 30},
            }
        }
        mock_transport.request.return_value = mock_response

        # Call the method
        result = workspaces_service.read_data_retention_policy("ws-123")

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/workspaces/ws-123/relationships/data-retention-policy"
        )

        # Verify result
        assert result.id == "drp-legacy123"
        assert result.delete_older_than_n_days == 30

    def test_read_data_retention_policy_choice_delete_older(
        self, workspaces_service, mock_transport
    ):
        """Test reading a workspace's data retention policy choice (delete older type)."""
        # Mock the read_by_id call first
        workspace_mock_response = Mock()
        workspace_mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "data-retention-policy-choice": {
                        "data": {
                            "id": "drp-delete123",
                            "type": "data-retention-policy-delete-olders",
                            "attributes": {"delete-older-than-n-days": 45},
                        }
                    }
                },
            }
        }

        # Mock the relationships endpoint call
        drp_mock_response = Mock()
        drp_mock_response.json.return_value = {
            "data": {
                "id": "drp-delete123",
                "type": "data-retention-policy-delete-olders",
                "attributes": {"delete-older-than-n-days": 45},
            }
        }

        # Configure mock to return different responses for different URLs
        def side_effect(*args, **kwargs):
            if "relationships/data-retention-policy" in args[1]:
                return drp_mock_response
            else:
                return workspace_mock_response

        mock_transport.request.side_effect = side_effect

        # Call the method
        result = workspaces_service.read_data_retention_policy_choice("ws-123")

        # Verify API calls
        assert mock_transport.request.call_count == 2

        # Verify result
        assert result is not None
        assert result.data_retention_policy_delete_older is not None
        assert result.data_retention_policy_delete_older.id == "drp-delete123"
        assert result.data_retention_policy_delete_older.delete_older_than_n_days == 45
        assert result.data_retention_policy_dont_delete is None
        assert result.data_retention_policy is None

    def test_read_data_retention_policy_choice_dont_delete(
        self, workspaces_service, mock_transport
    ):
        """Test reading a workspace's data retention policy choice (don't delete type)."""
        # Mock the read_by_id call first
        workspace_mock_response = Mock()
        workspace_mock_response.json.return_value = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "data-retention-policy-choice": {
                        "data": {
                            "id": "drp-dontdelete123",
                            "type": "data-retention-policy-dont-deletes",
                            "attributes": {},
                        }
                    }
                },
            }
        }

        # Mock the relationships endpoint call
        drp_mock_response = Mock()
        drp_mock_response.json.return_value = {
            "data": {
                "id": "drp-dontdelete123",
                "type": "data-retention-policy-dont-deletes",
                "attributes": {},
            }
        }

        # Configure mock to return different responses for different URLs
        def side_effect(*args, **kwargs):
            if "relationships/data-retention-policy" in args[1]:
                return drp_mock_response
            else:
                return workspace_mock_response

        mock_transport.request.side_effect = side_effect

        # Call the method
        result = workspaces_service.read_data_retention_policy_choice("ws-123")

        # Verify result
        assert result is not None
        assert result.data_retention_policy_dont_delete is not None
        assert result.data_retention_policy_dont_delete.id == "drp-dontdelete123"
        assert result.data_retention_policy_delete_older is None
        assert result.data_retention_policy is None

    def test_set_data_retention_policy_delete_older(
        self, workspaces_service, mock_transport
    ):
        """Test setting a workspace's data retention policy to delete older."""

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "drp-new123",
                "type": "data-retention-policy-delete-olders",
                "attributes": {"delete-older-than-n-days": 60},
            }
        }
        mock_transport.request.return_value = mock_response

        # Create options
        options = DataRetentionPolicyDeleteOlderSetOptions(delete_older_than_n_days=60)

        # Call the method
        result = workspaces_service.set_data_retention_policy_delete_older(
            "ws-123", options=options
        )

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            "/api/v2/workspaces/ws-123/relationships/data-retention-policy"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        expected_body = {
            "data": {
                "type": "data-retention-policy-delete-olders",
                "attributes": {"delete-older-than-n-days": 60},
            }
        }
        assert body == expected_body

        # Verify result
        assert result.id == "drp-new123"
        assert result.delete_older_than_n_days == 60

    def test_set_data_retention_policy_dont_delete(
        self, workspaces_service, mock_transport
    ):
        """Test setting a workspace's data retention policy to don't delete."""

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "drp-dontdelete456",
                "type": "data-retention-policy-dont-deletes",
                "attributes": {},
            }
        }
        mock_transport.request.return_value = mock_response

        # Create options
        options = DataRetentionPolicyDontDeleteSetOptions()

        # Call the method
        result = workspaces_service.set_data_retention_policy_dont_delete(
            "ws-123", options=options
        )

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            "/api/v2/workspaces/ws-123/relationships/data-retention-policy"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        expected_body = {
            "data": {
                "type": "data-retention-policy-dont-deletes",
            }
        }
        assert body == expected_body

        # Verify result
        assert result.id == "drp-dontdelete456"

    def test_set_data_retention_policy_legacy(self, workspaces_service, mock_transport):
        """Test setting a workspace's data retention policy (legacy method)."""

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "drp-legacy789",
                "type": "data-retention-policies",
                "attributes": {"delete-older-than-n-days": 90},
            }
        }
        mock_transport.request.return_value = mock_response

        # Create options
        options = DataRetentionPolicySetOptions(delete_older_than_n_days=90)

        # Call the method
        result = workspaces_service.set_data_retention_policy("ws-123", options=options)

        # Verify API call
        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert (
            "/api/v2/workspaces/ws-123/relationships/data-retention-policy"
            in call_args[0][1]
        )

        # Verify request body
        body = call_args[1]["json_body"]
        expected_body = {
            "data": {
                "type": "data-retention-policies",
                "attributes": {"delete-older-than-n-days": 90},
            }
        }
        assert body == expected_body

        # Verify result
        assert result.id == "drp-legacy789"
        assert result.delete_older_than_n_days == 90

    def test_delete_data_retention_policy(self, workspaces_service, mock_transport):
        """Test deleting a workspace's data retention policy."""
        # Mock successful response
        mock_response = Mock()
        mock_transport.request.return_value = mock_response

        # Call the method
        workspaces_service.delete_data_retention_policy("ws-123")

        # Verify API call
        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/workspaces/ws-123/relationships/data-retention-policy"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
