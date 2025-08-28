"""Unit tests for the utility functions."""

from tfe.utils import build_query_params, deserialize_jsonapi, prepare_jsonapi_data


# Mock model class for testing
class MockResource:
    """Mock resource model for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return (
            f"MockResource({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})"
        )


class TestBuildQueryParams:
    """Test the build_query_params function."""

    def test_basic_parameters(self):
        """Test building query parameters with basic values."""
        params = build_query_params(page=1, per_page=10, search="test")

        assert params["page"] == "1"
        assert params["per_page"] == "10"
        assert params["search"] == "test"
        assert len(params) == 3

    def test_none_values_filtered(self):
        """Test that None values are filtered out."""
        params = build_query_params(page=1, per_page=None, search="test", filter=None)

        assert params["page"] == "1"
        assert params["search"] == "test"
        assert "per_page" not in params
        assert "filter" not in params
        assert len(params) == 2

    def test_list_values(self):
        """Test handling of list values."""
        params = build_query_params(include=["users", "teams"], tags=["dev", "prod"])

        assert params["include"] == ["users", "teams"]
        assert params["tags"] == ["dev", "prod"]
        assert len(params) == 2

    def test_tuple_values(self):
        """Test handling of tuple values."""
        params = build_query_params(include=("users", "teams"))

        assert params["include"] == ("users", "teams")
        assert len(params) == 1

    def test_empty_parameters(self):
        """Test with no parameters."""
        params = build_query_params()

        assert params == {}
        assert len(params) == 0

    def test_mixed_types(self):
        """Test with mixed parameter types."""
        params = build_query_params(
            page=1,
            per_page=25,
            search="terraform",
            active=True,
            include=["users"],
            tags=None,
            filter="",
        )

        assert params["page"] == "1"
        assert params["per_page"] == "25"
        assert params["search"] == "terraform"
        assert params["active"] == "True"
        assert params["include"] == ["users"]
        assert params["filter"] == ""
        assert "tags" not in params
        assert len(params) == 6

    def test_zero_values(self):
        """Test that zero values are included."""
        params = build_query_params(page=0, per_page=0, search="")

        assert params["page"] == "0"
        assert params["per_page"] == "0"
        assert params["search"] == ""
        assert len(params) == 3


class TestPrepareJsonapiData:
    """Test the prepare_jsonapi_data function."""

    def test_basic_data(self):
        """Test preparing basic data for JSONAPI format."""
        data = {"name": "test-workspace", "description": "A test workspace"}
        jsonapi_data = prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["type"] == "workspaces"
        assert jsonapi_data["data"]["attributes"]["name"] == "test-workspace"
        assert jsonapi_data["data"]["attributes"]["description"] == "A test workspace"
        assert "id" not in jsonapi_data["data"]

    def test_with_id(self):
        """Test that ID is moved to top level."""
        data = {"id": "ws-123", "name": "test-workspace"}
        jsonapi_data = prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["id"] == "ws-123"
        assert jsonapi_data["data"]["type"] == "workspaces"
        assert jsonapi_data["data"]["attributes"]["name"] == "test-workspace"
        assert "id" not in jsonapi_data["data"]["attributes"]

    def test_empty_data(self):
        """Test with empty data dictionary."""
        data = {}
        jsonapi_data = prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["type"] == "workspaces"
        assert jsonapi_data["data"]["attributes"] == {}
        assert "id" not in jsonapi_data["data"]

    def test_nested_data(self):
        """Test with nested data structures."""
        data = {
            "name": "test-workspace",
            "settings": {"execution_mode": "remote", "auto_apply": True},
            "tags": ["dev", "test"],
        }
        jsonapi_data = prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["type"] == "workspaces"
        assert jsonapi_data["data"]["attributes"]["name"] == "test-workspace"
        assert (
            jsonapi_data["data"]["attributes"]["settings"]["execution_mode"] == "remote"
        )
        assert jsonapi_data["data"]["attributes"]["settings"]["auto_apply"] is True
        assert jsonapi_data["data"]["attributes"]["tags"] == ["dev", "test"]

    def test_complex_resource_type(self):
        """Test with complex resource type names."""
        data = {"name": "test"}
        jsonapi_data = prepare_jsonapi_data(data, "terraform-runs")

        assert jsonapi_data["data"]["type"] == "terraform-runs"
        assert jsonapi_data["data"]["attributes"]["name"] == "test"

    def test_boolean_values(self):
        """Test handling of boolean values."""
        data = {"auto_apply": True, "locked": False}
        jsonapi_data = prepare_jsonapi_data(data, "workspaces")

        assert jsonapi_data["data"]["attributes"]["auto_apply"] is True
        assert jsonapi_data["data"]["attributes"]["locked"] is False


class TestDeserializeJsonapi:
    """Test the deserialize_jsonapi function."""

    def test_single_resource(self):
        """Test deserializing a single resource."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {
                    "name": "test-workspace",
                    "description": "A test workspace",
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert isinstance(result, MockResource)
        assert result.id == "ws-123"
        assert result.name == "test-workspace"
        assert result.description == "A test workspace"

    def test_list_of_resources(self):
        """Test deserializing a list of resources."""
        jsonapi_data = {
            "data": [
                {
                    "id": "ws-1",
                    "type": "workspaces",
                    "attributes": {"name": "workspace-1"},
                },
                {
                    "id": "ws-2",
                    "type": "workspaces",
                    "attributes": {"name": "workspace-2"},
                },
            ]
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert isinstance(result, list)
        assert len(result) == 2

        assert result[0].id == "ws-1"
        assert result[0].name == "workspace-1"
        assert result[1].id == "ws-2"
        assert result[1].name == "workspace-2"

    def test_with_relationships(self):
        """Test deserializing resources with relationships."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "organization": {
                        "data": {"id": "org-456", "type": "organizations"}
                    },
                    "teams": {
                        "data": [
                            {"id": "team-1", "type": "teams"},
                            {"id": "team-2", "type": "teams"},
                        ]
                    },
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.organization_id == "org-456"
        assert result.teams_ids == ["team-1", "team-2"]

    def test_single_relationship(self):
        """Test deserializing with single relationship."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "organization": {"data": {"id": "org-456", "type": "organizations"}}
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.organization_id == "org-456"
        assert not hasattr(result, "teams_ids")

    def test_empty_relationships(self):
        """Test deserializing with empty relationships."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {},
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.id == "ws-123"
        assert result.name == "test-workspace"
        # No relationship attributes should be added

    def test_no_attributes(self):
        """Test deserializing resource without attributes."""
        jsonapi_data = {"data": {"id": "ws-123", "type": "workspaces"}}

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        # Should return the data as-is since no attributes
        assert result == jsonapi_data["data"]

    def test_non_jsonapi_data(self):
        """Test handling of non-JSONAPI data."""
        regular_data = {"name": "test", "id": "123"}
        result = deserialize_jsonapi(regular_data, MockResource)

        # Should return as-is
        assert result == regular_data

    def test_none_data(self):
        """Test handling of None data."""
        result = deserialize_jsonapi(None, MockResource)

        assert result is None

    def test_empty_data(self):
        """Test handling of empty data."""
        empty_data = {}
        result = deserialize_jsonapi(empty_data, MockResource)

        # Should return None for empty data
        assert result is None

    def test_empty_data_list(self):
        """Test handling of empty data list."""
        empty_list_data = {"data": []}
        result = deserialize_jsonapi(empty_list_data, MockResource)

        assert result == []

    def test_malformed_relationships(self):
        """Test handling of malformed relationship data."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "organization": {
                        "data": "invalid-data"  # Should be dict or list
                    }
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        # Should still create the resource, but relationship handling may fail
        assert result.name == "test-workspace"

    def test_relationship_without_id(self):
        """Test relationship data without ID."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {"name": "test-workspace"},
                "relationships": {
                    "organization": {
                        "data": {"type": "organizations"}  # No ID
                    }
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.name == "test-workspace"
        # No organization_id should be set since no ID in relationship data


class TestDeserializeSingleResource:
    """Test the deserialize_single_resource function indirectly through deserialize_jsonapi."""

    def test_resource_without_id(self):
        """Test resource without ID attribute."""
        jsonapi_data = {
            "data": {"type": "workspaces", "attributes": {"name": "test-workspace"}}
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.name == "test-workspace"
        assert not hasattr(result, "id")

    def test_resource_with_extra_attributes(self):
        """Test resource with extra attributes."""
        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {
                    "name": "test-workspace",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-02T00:00:00Z",
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, MockResource)

        assert result.id == "ws-123"
        assert result.name == "test-workspace"
        assert result.created_at == "2023-01-01T00:00:00Z"
        assert result.updated_at == "2023-01-02T00:00:00Z"

    def test_model_creation_failure_fallback(self):
        """Test fallback when model creation fails."""

        # Create a model class that will fail on certain attributes
        class FailingModel:
            def __init__(self, **kwargs):
                if "failing_attr" in kwargs:
                    raise ValueError("Model creation failed")
                for key, value in kwargs.items():
                    setattr(self, key, value)

        jsonapi_data = {
            "data": {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {
                    "name": "test-workspace",
                    "failing_attr": "this will cause failure",
                },
            }
        }

        result = deserialize_jsonapi(jsonapi_data, FailingModel)

        # Should return attributes dict as fallback
        assert isinstance(result, dict)
        assert result["name"] == "test-workspace"
        assert result["failing_attr"] == "this will cause failure"
