# Running Tests

python-tfe includes a comprehensive test suite with unit tests that use mocked API responses. The tests are designed to run quickly without requiring a live HCP Terraform or Terraform Enterprise instance.

## Quick Start

```bash
# Install dependencies
make dev-install

# Run all tests
make test

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/units/test_workspaces.py -v

# Run specific test class or function
python -m pytest tests/units/test_workspaces.py::TestWorkspaceOperations::test_create_workspace_basic -v
```

## Test Structure

Tests are organized in the `tests/units/` directory, with one test file per resource:

```
tests/
├── units/
│   ├── test_workspaces.py          # Workspace tests
│   ├── test_runs.py                # Run tests
│   ├── test_variables.py           # Variable tests
│   ├── test_organization_tags.py   # Organization tags tests
│   └── ...
```

Each test file typically contains:
- **Model tests**: Validate Pydantic models and enums
- **Operation tests**: Test CRUD operations with mocked responses
- **Error handling tests**: Validate error conditions
- **Integration tests**: Test complete workflows

## Test Organization

Tests follow a consistent structure using pytest classes:

```python
class TestResourceModels:
    """Test model validation and creation."""
    
    def test_model_basic(self):
        """Test basic model creation."""
        # Test model instantiation and validation
        
class TestResourceOperations:
    """Test resource operations."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock API response."""
        # Return mock response structure
        
    def test_list_resources(self, client, mock_response):
        """Test listing resources."""
        client._transport.request = MagicMock(return_value=mock_response)
        # Test the operation
        
class TestResourceErrorHandling:
    """Test error conditions."""
    
    def test_invalid_id_error(self, client):
        """Test error handling for invalid IDs."""
        with pytest.raises(InvalidResourceIDError):
            client.resources.read("")
```

## Writing Tests

### 1. Create Mock Responses

Mock API responses follow the JSON:API format:

```python
@pytest.fixture
def mock_list_response(self):
    """Create a mock list response."""
    mock = Mock()
    mock.json.return_value = {
        "data": [
            {
                "id": "ws-123",
                "type": "workspaces",
                "attributes": {
                    "name": "my-workspace",
                    "created-at": "2023-01-01T00:00:00Z",
                },
            }
        ],
        "meta": {
            "pagination": {
                "current-page": 1,
                "total-pages": 1,
                "prev-page": None,
                "next-page": None,
                "total-count": 1,
            }
        },
    }
    return mock
```

### 2. Mock the Transport Layer

Use `MagicMock` to mock the HTTP transport:

```python
def test_create_workspace(self, client):
    """Test creating a workspace."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "ws-new",
            "type": "workspaces",
            "attributes": {"name": "new-workspace"},
        }
    }
    
    # Mock the transport request method
    client._transport.request = MagicMock(return_value=mock_response)
    
    # Execute the operation
    options = WorkspaceCreateOptions(name="new-workspace", organization="test-org")
    workspace = client.workspaces.create(options)
    
    # Assertions
    assert workspace.id == "ws-new"
    assert workspace.name == "new-workspace"
    
    # Verify the request was made correctly
    client._transport.request.assert_called_once()
    call_args = client._transport.request.call_args
    assert call_args[0][0] == "POST"  # HTTP method
    assert "/workspaces" in call_args[0][1]  # URL path
```

### 3. Test Error Conditions

Always test validation and error handling:

```python
def test_create_workspace_invalid_org(self, client):
    """Test creating workspace with invalid organization."""
    with pytest.raises(InvalidOrgError):
        options = WorkspaceCreateOptions(name="test", organization="")
        client.workspaces.create(options)

def test_read_workspace_invalid_id(self, client):
    """Test reading workspace with invalid ID."""
    with pytest.raises(InvalidWorkspaceIDError):
        client.workspaces.read(workspace_id="")
```

### 4. Test Pagination

For list operations that use the iterator pattern:

```python
def test_list_with_pagination(self, client):
    """Test listing with pagination."""
    # Setup two pages of responses
    page1 = Mock()
    page1.json.return_value = {
        "data": [{"id": "ws-1", "type": "workspaces", "attributes": {"name": "ws1"}}],
        "meta": {"pagination": {"current-page": 1, "total-pages": 2}},
    }
    
    page2 = Mock()
    page2.json.return_value = {
        "data": [{"id": "ws-2", "type": "workspaces", "attributes": {"name": "ws2"}}],
        "meta": {"pagination": {"current-page": 2, "total-pages": 2}},
    }
    
    client._transport.request = MagicMock(side_effect=[page1, page2])
    
    # List returns an iterator, so convert to list
    workspaces = list(client.workspaces.list("test-org"))
    
    # Should have called request twice (once per page)
    assert len(workspaces) == 2
    assert client._transport.request.call_count == 2
```

## Running Tests

### Run All Tests

```bash
# Using Makefile
make test

# Using pytest directly
python -m pytest

# With verbose output
python -m pytest -v

# With coverage
python -m pytest --cov=src/pytfe --cov-report=html
```

### Run Specific Tests

```bash
# Run specific file
python -m pytest tests/units/test_workspaces.py

# Run specific class
python -m pytest tests/units/test_workspaces.py::TestWorkspaceOperations

# Run specific test
python -m pytest tests/units/test_workspaces.py::TestWorkspaceOperations::test_create_workspace_basic

# Run tests matching pattern
python -m pytest -k "workspace" -v

# Run tests matching multiple patterns
python -m pytest -k "create or update" -v
```

### Run Tests with Options

```bash
# Stop on first failure
python -m pytest -x

# Show local variables in tracebacks
python -m pytest -l

# Run last failed tests
python -m pytest --lf

# Run failed tests first, then others
python -m pytest --ff

# Show test durations
python -m pytest --durations=10

# Parallel execution (requires pytest-xdist)
python -m pytest -n auto
```

## Test Coverage

Check test coverage to ensure new code is tested:

```bash
# Run tests with coverage
python -m pytest --cov=src/pytfe --cov-report=term-missing

# Generate HTML coverage report
python -m pytest --cov=src/pytfe --cov-report=html

# Open the HTML report
open htmlcov/index.html
```

## Debugging Tests

### Using Print Statements

```python
def test_something(self, client):
    """Test something."""
    # Use -s flag to see print output
    print("Debug info:", some_variable)
    assert some_variable == expected
```

Run with: `python -m pytest -s tests/units/test_file.py`

### Using pdb Debugger

```python
def test_something(self, client):
    """Test something."""
    import pdb; pdb.set_trace()  # Debugger will stop here
    result = client.some_operation()
    assert result == expected
```

### Using pytest's Built-in Debugger

```bash
# Drop into debugger on failure
python -m pytest --pdb

# Drop into debugger at start of each test
python -m pytest --trace
```

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Every push to main branches
- Every pull request
- Scheduled daily runs

The CI pipeline:
1. Sets up Python 3.11+ environment
2. Installs dependencies
3. Runs linting (ruff, mypy)
4. Runs full test suite
5. Reports coverage

## Test Best Practices

### DO:
- Mock all HTTP requests - tests should not hit real APIs
- Test both success and error conditions
- Use descriptive test names that explain what is being tested
- Keep tests independent - each test should be able to run alone
- Use fixtures for common setup code
- Test edge cases and boundary conditions
- Verify request parameters (method, URL, body) in assertions
- Follow the existing test patterns in the codebase

### DON'T:
- Don't make real API calls in tests
- Don't depend on test execution order
- Don't share state between tests
- Don't use sleep() or time delays
- Don't test implementation details, test behavior
- Don't write overly complex tests - keep them simple and readable

## Testing Checklist for New Features

When adding a new resource or endpoint, ensure you have:

- [ ] Model tests validating all fields and enums
- [ ] Tests for each CRUD operation (Create, Read, Update, Delete, List)
- [ ] Tests for optional parameters and filtering
- [ ] Tests for pagination (if list operation)
- [ ] Tests for all error conditions (invalid IDs, missing required fields, etc.)
- [ ] Tests verifying correct HTTP methods and URL paths
- [ ] Tests verifying request body structure (for POST/PATCH)
- [ ] Tests verifying query parameters (for GET)
- [ ] All tests passing (`make test`)
- [ ] Code coverage above 80% for new code

## Common Testing Patterns

### Testing Create Operations

```python
def test_create_resource(self, client):
    """Test creating a resource."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "res-123",
            "type": "resources",
            "attributes": {"name": "test-resource"},
        }
    }
    client._transport.request = MagicMock(return_value=mock_response)
    
    options = ResourceCreateOptions(name="test-resource")
    resource = client.resources.create("org-name", options)
    
    assert resource.id == "res-123"
    
    # Verify the request
    call_args = client._transport.request.call_args
    assert call_args[0][0] == "POST"
    assert call_args[1]["json_body"]["data"]["type"] == "resources"
```

### Testing List Operations

```python
def test_list_resources(self, client, mock_list_response):
    """Test listing resources."""
    client._transport.request = MagicMock(return_value=mock_list_response)
    
    resources = list(client.resources.list("org-name"))
    
    assert len(resources) > 0
    assert all(isinstance(r, Resource) for r in resources)
```

### Testing Update Operations

```python
def test_update_resource(self, client):
    """Test updating a resource."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": {
            "id": "res-123",
            "type": "resources",
            "attributes": {"name": "updated-name"},
        }
    }
    client._transport.request = MagicMock(return_value=mock_response)
    
    options = ResourceUpdateOptions(name="updated-name")
    resource = client.resources.update("res-123", options)
    
    assert resource.name == "updated-name"
    
    call_args = client._transport.request.call_args
    assert call_args[0][0] == "PATCH"
```

### Testing Delete Operations

```python
def test_delete_resource(self, client):
    """Test deleting a resource."""
    mock_response = Mock()
    mock_response.status_code = 204
    client._transport.request = MagicMock(return_value=mock_response)
    
    # Should not raise an exception
    client.resources.delete("res-123")
    
    call_args = client._transport.request.call_args
    assert call_args[0][0] == "DELETE"
    assert "res-123" in call_args[0][1]
```

## Troubleshooting

### Tests Pass Locally But Fail in CI

- Ensure you're using the same Python version as CI
- Check for environment-specific issues (file paths, etc.)
- Run `make lint` to catch style issues

### Import Errors

```bash
# Reinstall in development mode
make dev-install

# Or manually
pip install -e ".[dev]"
```

### Fixture Not Found

Ensure fixtures are defined in the same test class or in `conftest.py`:

```python
# In tests/conftest.py for shared fixtures
import pytest
from pytfe import TFEClient, TFEConfig

@pytest.fixture
def client():
    """Create a test client."""
    config = TFEConfig(address="https://test.terraform.io", token="test-token")
    return TFEClient(config)
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)
