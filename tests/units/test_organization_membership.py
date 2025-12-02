"""
Comprehensive unit tests for organization membership operations in the Python TFE SDK.

This test suite covers all organization membership methods including list, create, read,
read with options, and delete operations.
"""

from unittest.mock import Mock

import pytest

from src.pytfe.errors import (
    ERR_INVALID_EMAIL,
    ERR_INVALID_ORG,
    ERR_REQUIRED_EMAIL,
    NotFound,
)
from src.pytfe.models.organization_membership import (
    OrganizationMembershipCreateOptions,
    OrganizationMembershipListOptions,
    OrganizationMembershipReadOptions,
    OrganizationMembershipStatus,
    OrgMembershipIncludeOpt,
)
from src.pytfe.models.team import OrganizationAccess, Team
from src.pytfe.resources.organization_membership import OrganizationMemberships


class TestOrganizationMembershipList:
    """Test suite for organization membership list operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    @pytest.fixture
    def sample_membership_response(self):
        """Sample JSON:API organization membership response."""
        return {
            "data": [
                {
                    "type": "organization-memberships",
                    "id": "ou-abc123def456",
                    "attributes": {"status": "active"},
                    "relationships": {
                        "teams": {
                            "data": [{"type": "teams", "id": "team-yUrEehvfG4pdmSjc"}]
                        },
                        "user": {"data": {"type": "users", "id": "user-123"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "org-test"}
                        },
                    },
                },
                {
                    "type": "organization-memberships",
                    "id": "ou-xyz789ghi012",
                    "attributes": {"status": "invited"},
                    "relationships": {
                        "teams": {
                            "data": [{"type": "teams", "id": "team-yUrEehvfG4pdmSjc"}]
                        },
                        "user": {"data": {"type": "users", "id": "user-456"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "org-test"}
                        },
                    },
                },
            ],
            "meta": {"pagination": {"current-page": 1, "total-count": 2}},
        }

    def test_list_without_options(
        self, membership_service, mock_transport, sample_membership_response
    ):
        """Test listing organization memberships without options."""
        mock_response = Mock()
        mock_response.json.return_value = sample_membership_response
        mock_transport.request.return_value = mock_response

        memberships = list(membership_service.list("test-org"))

        assert len(memberships) == 2
        assert memberships[0].status == OrganizationMembershipStatus.ACTIVE
        assert memberships[0].id == "ou-abc123def456"
        assert memberships[1].status == OrganizationMembershipStatus.INVITED
        assert memberships[1].id == "ou-xyz789ghi012"
        mock_transport.request.assert_called_once()

    def test_list_with_pagination_options(self, membership_service, mock_transport):
        """Test listing with pagination options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [],
            "meta": {"pagination": {"current-page": 999, "total-count": 2}},
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipListOptions(page_number=999, page_size=100)
        memberships = list(membership_service.list("test-org", options))

        assert len(memberships) == 0
        # Verify pagination params are passed
        call_args = mock_transport.request.call_args
        assert call_args is not None

    def test_list_with_include_options(
        self, membership_service, mock_transport, sample_membership_response
    ):
        """Test listing with include options for user and teams."""
        mock_response = Mock()
        mock_response.json.return_value = sample_membership_response
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipListOptions(
            include=[OrgMembershipIncludeOpt.USER, OrgMembershipIncludeOpt.TEAMS]
        )
        memberships = list(membership_service.list("test-org", options))

        assert len(memberships) == 2
        mock_transport.request.assert_called_once()

    def test_list_with_email_filter(self, membership_service, mock_transport):
        """Test listing with email filter option."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "type": "organization-memberships",
                    "id": "ou-abc123",
                    "attributes": {"status": "active"},
                    "relationships": {
                        "teams": {"data": [{"type": "teams", "id": "team-xyz"}]},
                        "user": {"data": {"type": "users", "id": "user-abc"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "test-org"}
                        },
                    },
                }
            ],
            "meta": {"pagination": {"current-page": 1, "total-count": 1}},
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipListOptions(emails=["specific@example.com"])
        memberships = list(membership_service.list("test-org", options))

        assert len(memberships) == 1
        assert memberships[0].status == OrganizationMembershipStatus.ACTIVE

    def test_list_with_status_filter(self, membership_service, mock_transport):
        """Test listing with status filter option."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "type": "organization-memberships",
                    "id": "ou-abc123",
                    "attributes": {"status": "invited"},
                    "relationships": {
                        "teams": {"data": [{"type": "teams", "id": "team-xyz"}]},
                        "user": {"data": {"type": "users", "id": "user-abc"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "test-org"}
                        },
                    },
                }
            ],
            "meta": {"pagination": {"current-page": 1, "total-count": 1}},
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipListOptions(
            status=OrganizationMembershipStatus.INVITED
        )
        memberships = list(membership_service.list("test-org", options))

        assert len(memberships) == 1
        assert memberships[0].status == OrganizationMembershipStatus.INVITED

    def test_list_with_query_string(self, membership_service, mock_transport):
        """Test listing with search query string."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {
                    "type": "organization-memberships",
                    "id": "ou-abc123",
                    "attributes": {"status": "active"},
                    "relationships": {
                        "teams": {"data": [{"type": "teams", "id": "team-xyz"}]},
                        "user": {"data": {"type": "users", "id": "user-abc"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "test-org"}
                        },
                    },
                }
            ],
            "meta": {"pagination": {"current-page": 1, "total-count": 1}},
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipListOptions(query="example.com")
        memberships = list(membership_service.list("test-org", options))

        assert len(memberships) == 1

    def test_list_with_invalid_organization(self, membership_service):
        """Test listing with invalid organization name."""
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            list(membership_service.list(""))


class TestOrganizationMembershipCreate:
    """Test suite for organization membership create operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    @pytest.fixture
    def sample_create_response(self):
        """Sample JSON:API create response."""
        return {
            "data": {
                "type": "organization-memberships",
                "id": "ou-newmember123",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {
                        "data": [{"type": "teams", "id": "team-GeLZkdnK6xAVjA5H"}]
                    },
                    "user": {"data": {"type": "users", "id": "user-J8oxGmRk5eC2WLfX"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "my-organization"}
                    },
                },
            },
            "included": [
                {
                    "id": "user-J8oxGmRk5eC2WLfX",
                    "type": "users",
                    "attributes": {
                        "username": None,
                        "is-service-account": False,
                        "auth-method": "hcp_sso",
                        "avatar-url": "https://www.gravatar.com/avatar/55502f40dc8b7c769880b10874abc9d0?s=100&d=mm",
                        "two-factor": {"enabled": False, "verified": False},
                        "email": "newuser@example.com",
                        "permissions": {
                            "can-create-organizations": True,
                            "can-change-email": True,
                            "can-change-username": True,
                            "can-manage-user-tokens": False,
                        },
                    },
                    "relationships": {
                        "authentication-tokens": {
                            "links": {
                                "related": "/api/v2/users/user-J8oxGmRk5eC2WLfX/authentication-tokens"
                            }
                        }
                    },
                    "links": {"self": "/api/v2/users/user-J8oxGmRk5eC2WLfX"},
                }
            ],
        }

    def test_create_with_valid_options(
        self, membership_service, mock_transport, sample_create_response
    ):
        """Test creating organization membership with valid options."""
        mock_response = Mock()
        mock_response.json.return_value = sample_create_response
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipCreateOptions(email="newuser@example.com")
        membership = membership_service.create("test-org", options)

        assert membership.status == OrganizationMembershipStatus.INVITED
        assert membership.id == "ou-newmember123"
        assert membership.user is not None
        # User is parsed as a User object with id
        assert membership.user.id == "user-J8oxGmRk5eC2WLfX"
        mock_transport.request.assert_called_once()

    def test_create_with_teams(self, membership_service, mock_transport):
        """Test creating organization membership with initial teams."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-withteams123",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {
                        "data": [
                            {"type": "teams", "id": "team-123"},
                            {"type": "teams", "id": "team-456"},
                        ]
                    },
                    "user": {"data": {"type": "users", "id": "user-xyz"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }
        mock_transport.request.return_value = mock_response

        team1 = Team(id="team-123")
        team2 = Team(id="team-456")
        options = OrganizationMembershipCreateOptions(
            email="teamuser@example.com", teams=[team1, team2]
        )
        membership = membership_service.create("test-org", options)

        assert membership.status == OrganizationMembershipStatus.INVITED
        assert membership.teams is not None
        assert len(membership.teams) == 2

    def test_create_with_organization_access(self, membership_service, mock_transport):
        """Test creating membership with team that has organization access."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-orgaccess123",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {"data": [{"type": "teams", "id": "team-123"}]},
                    "user": {"data": {"type": "users", "id": "user-abc"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }
        mock_transport.request.return_value = mock_response

        team = Team(
            id="team-123", organization_access=OrganizationAccess(read_workspaces=True)
        )
        options = OrganizationMembershipCreateOptions(
            email="orgaccess@example.com", teams=[team]
        )
        membership = membership_service.create("test-org", options)

        assert membership.status == OrganizationMembershipStatus.INVITED
        assert membership.id == "ou-orgaccess123"

    def test_create_with_invalid_organization(self, membership_service):
        """Test creating with invalid organization name."""
        options = OrganizationMembershipCreateOptions(email="user@example.com")
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            membership_service.create("", options)

    def test_create_with_missing_email(self, membership_service):
        """Test creating without required email."""
        options = OrganizationMembershipCreateOptions(email="")
        with pytest.raises(ValueError, match=ERR_REQUIRED_EMAIL):
            membership_service.create("test-org", options)

    def test_create_with_invalid_email(self, membership_service):
        """Test creating with invalid email format."""
        options = OrganizationMembershipCreateOptions(email="not-an-email")
        with pytest.raises(ValueError, match=ERR_INVALID_EMAIL):
            membership_service.create("test-org", options)


class TestOrganizationMembershipRead:
    """Test suite for organization membership read operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    @pytest.fixture
    def sample_read_response(self):
        """Sample JSON:API read response."""
        return {
            "data": {
                "type": "organization-memberships",
                "id": "ou-abc123def456",
                "attributes": {"status": "active"},
                "relationships": {
                    "teams": {
                        "data": [{"type": "teams", "id": "team-97LkM7QciNkwb2nh"}]
                    },
                    "user": {"data": {"type": "users", "id": "user-123"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "org-test"}
                    },
                },
            }
        }

    def test_read_when_membership_exists(
        self, membership_service, mock_transport, sample_read_response
    ):
        """Test reading organization membership when it exists."""
        mock_response = Mock()
        mock_response.json.return_value = sample_read_response
        mock_transport.request.return_value = mock_response

        membership = membership_service.read("ou-abc123def456")

        assert membership is not None
        assert membership.id == "ou-abc123def456"
        assert membership.status == OrganizationMembershipStatus.ACTIVE
        mock_transport.request.assert_called_once()

    def test_read_when_membership_not_found(self, membership_service, mock_transport):
        """Test reading when membership does not exist."""
        mock_transport.request.side_effect = NotFound("not found", status=404)

        with pytest.raises(NotFound):
            membership_service.read("ou-nonexisting")

    def test_read_with_invalid_membership_id(self, membership_service):
        """Test reading with invalid membership ID."""
        with pytest.raises(ValueError, match="invalid organization membership ID"):
            membership_service.read("")


class TestOrganizationMembershipReadWithOptions:
    """Test suite for organization membership read with options operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    @pytest.fixture
    def sample_read_with_user_response(self):
        """Sample JSON:API read response with user included."""
        return {
            "data": {
                "type": "organization-memberships",
                "id": "ou-abc123def456",
                "attributes": {"status": "active"},
                "relationships": {
                    "teams": {
                        "data": [{"type": "teams", "id": "team-97LkM7QciNkwb2nh"}]
                    },
                    "user": {"data": {"type": "users", "id": "user-123"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "org-test"}
                    },
                },
            },
            "included": [
                {
                    "type": "users",
                    "id": "user-123",
                    "attributes": {
                        "username": "testuser",
                        "is-service-account": False,
                        "avatar-url": "https://www.gravatar.com/avatar/test?s=100&d=mm",
                        "two-factor": {"enabled": False, "verified": False},
                        "email": "user@example.com",
                        "permissions": {
                            "can-create-organizations": True,
                            "can-change-email": True,
                        },
                    },
                    "relationships": {
                        "authentication-tokens": {
                            "links": {
                                "related": "/api/v2/users/user-123/authentication-tokens"
                            }
                        }
                    },
                    "links": {"self": "/api/v2/users/user-123"},
                }
            ],
        }

    def test_read_with_options_include_user(
        self, membership_service, mock_transport, sample_read_with_user_response
    ):
        """Test reading with include user option."""
        mock_response = Mock()
        mock_response.json.return_value = sample_read_with_user_response
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipReadOptions(
            include=[OrgMembershipIncludeOpt.USER]
        )
        membership = membership_service.read_with_options("ou-abc123def456", options)

        assert membership is not None
        assert membership.id == "ou-abc123def456"
        assert membership.user is not None

    def test_read_with_options_include_teams(self, membership_service, mock_transport):
        """Test reading with include teams option."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-abc123def456",
                "attributes": {"status": "active"},
                "relationships": {
                    "teams": {
                        "data": [
                            {"type": "teams", "id": "team-123"},
                            {"type": "teams", "id": "team-456"},
                        ]
                    },
                    "user": {"data": {"type": "users", "id": "user-123"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "org-test"}
                    },
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipReadOptions(
            include=[OrgMembershipIncludeOpt.TEAMS]
        )
        membership = membership_service.read_with_options("ou-abc123def456", options)

        assert membership is not None
        assert membership.teams is not None
        assert len(membership.teams) == 2

    def test_read_with_options_without_options(
        self, membership_service, mock_transport
    ):
        """Test reading with empty options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-abc123def456",
                "attributes": {"status": "active"},
                "relationships": {
                    "teams": {
                        "data": [{"type": "teams", "id": "team-97LkM7QciNkwb2nh"}]
                    },
                    "user": {"data": {"type": "users", "id": "user-123"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "org-test"}
                    },
                },
            }
        }
        mock_transport.request.return_value = mock_response

        options = OrganizationMembershipReadOptions()
        membership = membership_service.read_with_options("ou-abc123def456", options)

        assert membership is not None
        assert membership.id == "ou-abc123def456"

    def test_read_with_options_not_found(self, membership_service, mock_transport):
        """Test reading with options when membership doesn't exist."""
        mock_transport.request.side_effect = NotFound("not found", status=404)

        options = OrganizationMembershipReadOptions(
            include=[OrgMembershipIncludeOpt.USER]
        )
        with pytest.raises(NotFound):
            membership_service.read_with_options("ou-nonexisting", options)

    def test_read_with_options_invalid_id(self, membership_service):
        """Test reading with options with invalid membership ID."""
        options = OrganizationMembershipReadOptions()
        with pytest.raises(ValueError, match="invalid organization membership ID"):
            membership_service.read_with_options("", options)


class TestOrganizationMembershipDelete:
    """Test suite for organization membership delete operations."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    def test_delete_with_valid_id(self, membership_service, mock_transport):
        """Test deleting organization membership with valid ID."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_transport.request.return_value = mock_response

        membership_service.delete("ou-abc123def456")

        mock_transport.request.assert_called_once()
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "DELETE"

    def test_delete_with_invalid_id(self, membership_service):
        """Test deleting with invalid membership ID."""
        with pytest.raises(ValueError, match="invalid organization membership ID"):
            membership_service.delete("")

    def test_delete_nonexistent_membership(self, membership_service, mock_transport):
        """Test deleting a membership that doesn't exist."""
        mock_transport.request.side_effect = NotFound("not found", status=404)

        with pytest.raises(NotFound):
            membership_service.delete("ou-nonexisting")


class TestOrganizationMembershipValidation:
    """Test suite for organization membership validation."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    def test_validate_email_format(self, membership_service):
        """Test email validation with invalid formats."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user",
            "",
        ]

        for email in invalid_emails:
            options = OrganizationMembershipCreateOptions(email=email)
            with pytest.raises(ValueError):
                membership_service.create("test-org", options)

    def test_validate_valid_email_format(self, membership_service, mock_transport):
        """Test email validation with valid formats."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-test",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {"data": [{"type": "teams", "id": "team-abc"}]},
                    "user": {"data": {"type": "users", "id": "user-xyz"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }
        mock_transport.request.return_value = mock_response

        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
        ]

        for email in valid_emails:
            options = OrganizationMembershipCreateOptions(email=email)
            membership = membership_service.create("test-org", options)
            assert membership is not None


class TestOrganizationMembershipIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def mock_transport(self):
        """Mock HTTP transport."""
        transport = Mock()
        return transport

    @pytest.fixture
    def membership_service(self, mock_transport):
        """Create organization membership service with mocked transport."""
        return OrganizationMemberships(mock_transport)

    def test_create_read_delete_workflow(self, membership_service, mock_transport):
        """Test complete workflow: create, read, then delete."""
        # Mock create response
        create_response = Mock()
        create_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-workflow123",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {"data": [{"type": "teams", "id": "team-abc"}]},
                    "user": {"data": {"type": "users", "id": "user-xyz"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }

        # Mock read response
        read_response = Mock()
        read_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-workflow123",
                "attributes": {"status": "invited"},
                "relationships": {
                    "teams": {"data": [{"type": "teams", "id": "team-abc"}]},
                    "user": {"data": {"type": "users", "id": "user-xyz"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }

        # Mock delete response
        delete_response = Mock()
        delete_response.status_code = 204

        mock_transport.request.side_effect = [
            create_response,
            read_response,
            delete_response,
        ]

        # Create
        options = OrganizationMembershipCreateOptions(email="workflow@example.com")
        created = membership_service.create("test-org", options)
        assert created.id == "ou-workflow123"

        # Read
        read_membership = membership_service.read("ou-workflow123")
        assert read_membership.id == created.id

        # Delete
        membership_service.delete("ou-workflow123")

        assert mock_transport.request.call_count == 3

    def test_list_filter_and_read_workflow(self, membership_service, mock_transport):
        """Test workflow: list with filters, then read specific member."""
        # Mock list response
        list_response = Mock()
        list_response.json.return_value = {
            "data": [
                {
                    "type": "organization-memberships",
                    "id": "ou-member1",
                    "attributes": {"status": "active"},
                    "relationships": {
                        "teams": {
                            "data": [{"type": "teams", "id": "team-yUrEehvfG4pdmSjc"}]
                        },
                        "user": {"data": {"type": "users", "id": "user-123"}},
                        "organization": {
                            "data": {"type": "organizations", "id": "test-org"}
                        },
                    },
                }
            ],
            "meta": {"pagination": {"current-page": 1, "total-count": 1}},
        }

        # Mock read response
        read_response = Mock()
        read_response.json.return_value = {
            "data": {
                "type": "organization-memberships",
                "id": "ou-member1",
                "attributes": {"status": "active"},
                "relationships": {
                    "teams": {
                        "data": [{"type": "teams", "id": "team-yUrEehvfG4pdmSjc"}]
                    },
                    "user": {"data": {"type": "users", "id": "user-123"}},
                    "organization": {
                        "data": {"type": "organizations", "id": "test-org"}
                    },
                },
            }
        }

        mock_transport.request.side_effect = [list_response, read_response]

        # List with filter
        options = OrganizationMembershipListOptions(
            status=OrganizationMembershipStatus.ACTIVE
        )
        memberships = list(membership_service.list("test-org", options))
        assert len(memberships) == 1
        assert memberships[0].status == OrganizationMembershipStatus.ACTIVE

        # Read specific member with options
        read_options = OrganizationMembershipReadOptions(
            include=[OrgMembershipIncludeOpt.USER]
        )
        member = membership_service.read_with_options(memberships[0].id, read_options)
        assert member.user is not None

        assert mock_transport.request.call_count == 2
