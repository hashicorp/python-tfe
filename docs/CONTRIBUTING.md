# Contributing to python-tfe

If you find an issue with this package, please create an issue in GitHub. If you'd like, we welcome any contributions. Fork this repository and submit a pull request.

## Adding New Functionality or Fixing Bugs

If you are making relevant changes worth communicating to our users, please include a note about it in our `CHANGELOG.md`. You can include it as part of the PR where you are submitting your changes.

`CHANGELOG.md` should have the next minor version listed as `# v0.X.0 (Unreleased)` and any changes can go under there. But if you feel that your changes are better suited for a patch version (like a critical bug fix), you may list a new section for this version. You should repeat the same formatting style introduced by previous versions.

### Scoping Pull Requests That Add New Resources

There are instances where several new resources being added (i.e., Workspace Run Tasks and Organization Run Tasks) are coalesced into one PR. In order to keep the review process as efficient and least error-prone as possible, we ask that you please scope each PR to an individual resource even if the multiple resources you're adding share similarities. If joining multiple related PRs into one single PR makes more sense logistically, we'd ask that you organize your commit history by resource. A general convention for this repository is one commit for the implementation of the resource's methods, one for tests, and one for cleanup and housekeeping (e.g., modifying the changelog/docs, updating examples, etc.).

**Note HashiCorp Employees Only:** When submitting a new set of endpoints please ensure that one of your respective team members approves the changes as well before merging.

## Linting

After opening a PR, our CI system will perform a series of code checks, one of which is linting. Linting is not strictly required for a change to be merged, but it helps smooth the review process and catch common mistakes early. If you'd like to run the linters manually, follow these steps:

1. Install development dependencies: `make dev-install`
2. Format your code: `make fmt`
3. Run lint checks: `make lint`

We use [ruff](https://docs.astral.sh/ruff/) for both formatting and linting, and [mypy](https://mypy.readthedocs.io/) for type checking.

## Writing Tests

The test suite contains unit tests with mocked API responses. You can read more about running the tests in [TESTS.md](TESTS.md). Our CI system (GitHub Actions) will not test your fork until a one-time approval takes place.

To run tests:
```bash
make test
```

## Adding New Endpoints

### Guidelines for Adding New Endpoints

* A resource class should cover one RESTful resource, which sometimes involves two or more endpoints.
* Each resource class must be registered in the `TFEClient` class in `client.py`.
* You'll need to add unit tests that cover each method of the resource class with mocked responses.
* Each API resource implementation must have a corresponding example file added to the `examples/` directory demonstrating its usage.
* Option classes serve as a proxy for either passing query params or request bodies:
    - `ListOptions` and `ReadOptions` are values passed as query parameters.
    - `CreateOptions` and `UpdateOptions` represent the request body.
* URL parameters should be defined as method parameters.
* Any resource-specific errors must be defined in `errors.py`.

Here is a comprehensive example of what a resource looks like when implemented:

#### 1. Create the Model (`src/pytfe/models/example.py`)

```python
"""Models for example resources."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExampleStatus(str, Enum):
    """Status of an example."""
    
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class Example(BaseModel):
    """Represents an example resource."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="The unique identifier")
    name: str | None = Field(None, description="The name of the example")
    status: ExampleStatus | None = Field(None, description="The current status")
    url: str | None = Field(None, description="The URL")
    optional_value: str | None = Field(
        None, alias="optional-value", description="An optional value"
    )
    created_at: datetime | None = Field(
        None, alias="created-at", description="When this was created"
    )
    
    # Relationships
    organization_name: str | None = Field(
        None, description="The organization this belongs to"
    )


class ExampleListOptions(BaseModel):
    """Options for listing examples."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    page_number: int | None = Field(
        None, alias="page[number]", description="Page number", ge=1
    )
    page_size: int | None = Field(
        None, alias="page[size]", description="Items per page", ge=1, le=100
    )


class ExampleCreateOptions(BaseModel):
    """Options for creating an example."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., description="The name of the example")
    url: str = Field(..., description="The URL")
    optional_value: str | None = Field(
        None, alias="optional-value", description="An optional value"
    )


class ExampleUpdateOptions(BaseModel):
    """Options for updating an example."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: str | None = Field(None, description="The name")
    url: str | None = Field(None, description="The URL")
    optional_value: str | None = Field(
        None, alias="optional-value", description="An optional value"
    )
```

#### 2. Create the Resource Class (`src/pytfe/resources/example.py`)

```python
"""Example API resource."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidExampleIDError, InvalidOrgError
from ..models.example import (
    Example,
    ExampleCreateOptions,
    ExampleListOptions,
    ExampleUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class Examples(_Service):
    """Example API for Terraform Enterprise."""

    def list(
        self, organization: str, options: ExampleListOptions | None = None
    ) -> Iterator[Example]:
        """Iterate through all examples in an organization.

        This method automatically handles pagination.

        Args:
            organization: The name of the organization
            options: Optional list options (page_size, page_number)

        Yields:
            Example objects one at a time
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params: dict[str, Any] = {}
        if options:
            params = options.model_dump(by_alias=True, exclude_none=True)

        path = f"/api/v2/organizations/{organization}/examples"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            
            # Extract relationships if needed
            relationships = item.get("relationships", {})
            org_rel = relationships.get("organization", {})
            org_data = org_rel.get("data", {})
            if org_data and isinstance(org_data, dict):
                attrs["organization_name"] = org_data.get("id")

            yield Example.model_validate(attrs)

    def create(
        self, organization: str, options: ExampleCreateOptions
    ) -> Example:
        """Create a new example.

        Args:
            organization: The name of the organization
            options: Options for creating the example

        Returns:
            The created Example object
        """
        if not valid_string_id(organization):
            raise InvalidOrgError()

        path = f"/api/v2/organizations/{organization}/examples"
        body = {
            "data": {
                "type": "examples",
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
            }
        }

        response = self.t.request("POST", path, json_body=body)
        data = response.json()["data"]
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return Example.model_validate(attrs)

    def read(self, example_id: str) -> Example:
        """Read an example by ID.

        Args:
            example_id: The ID of the example

        Returns:
            The Example object
        """
        if not valid_string_id(example_id):
            raise InvalidExampleIDError()

        path = f"/api/v2/examples/{example_id}"
        response = self.t.request("GET", path)
        data = response.json()["data"]
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return Example.model_validate(attrs)

    def update(
        self, example_id: str, options: ExampleUpdateOptions
    ) -> Example:
        """Update an example.

        Args:
            example_id: The ID of the example
            options: Options for updating the example

        Returns:
            The updated Example object
        """
        if not valid_string_id(example_id):
            raise InvalidExampleIDError()

        path = f"/api/v2/examples/{example_id}"
        body = {
            "data": {
                "type": "examples",
                "id": example_id,
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
            }
        }

        response = self.t.request("PATCH", path, json_body=body)
        data = response.json()["data"]
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        return Example.model_validate(attrs)

    def delete(self, example_id: str) -> None:
        """Delete an example.

        Args:
            example_id: The ID of the example

        Returns:
            None (204 No Content on success)
        """
        if not valid_string_id(example_id):
            raise InvalidExampleIDError()

        path = f"/api/v2/examples/{example_id}"
        self.t.request("DELETE", path)
```

#### 3. Add Custom Errors (`src/pytfe/errors.py`)

```python
class InvalidExampleIDError(InvalidValues):
    """Raised when an invalid example ID is provided."""

    def __init__(self, message: str = "invalid value for example ID") -> None:
        super().__init__(message)
```

#### 4. Register in Client (`src/pytfe/client.py`)

```python
from .resources.example import Examples

class TFEClient:
    def __init__(self, config: TFEConfig | None = None):
        # ... existing code ...
        self.examples = Examples(self._transport)
```

#### 5. Export Models (`src/pytfe/models/__init__.py`)

```python
from .example import (
    Example,
    ExampleCreateOptions,
    ExampleList,
    ExampleListOptions,
    ExampleStatus,
    ExampleUpdateOptions,
)

__all__ = [
    # ... existing exports ...
    "Example",
    "ExampleCreateOptions",
    "ExampleListOptions",
    "ExampleStatus",
    "ExampleUpdateOptions",
]
```

#### 6. Create Tests (`tests/units/test_example.py`)

```python
from unittest.mock import MagicMock, Mock

import pytest

from pytfe import TFEClient, TFEConfig
from pytfe.errors import InvalidExampleIDError, InvalidOrgError
from pytfe.models.example import (
    Example,
    ExampleCreateOptions,
    ExampleListOptions,
    ExampleStatus,
    ExampleUpdateOptions,
)


class TestExampleModels:
    """Test example models and validation."""

    def test_example_model_basic(self):
        """Test basic Example model creation."""
        example = Example(
            id="ex-123",
            name="test-example",
            status=ExampleStatus.ACTIVE,
        )
        assert example.id == "ex-123"
        assert example.name == "test-example"
        assert example.status == ExampleStatus.ACTIVE


class TestExampleOperations:
    """Test example operations."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        config = TFEConfig(address="https://test.terraform.io", token="test-token")
        return TFEClient(config)

    @pytest.fixture
    def mock_list_response(self):
        """Create a mock list response."""
        mock = Mock()
        mock.json.return_value = {
            "data": [
                {
                    "id": "ex-123",
                    "type": "examples",
                    "attributes": {
                        "name": "example1",
                        "status": "active",
                        "url": "https://example.com",
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

    def test_list_examples(self, client, mock_list_response):
        """Test listing examples."""
        client._transport.request = MagicMock(return_value=mock_list_response)

        examples = list(client.examples.list("test-org"))

        assert len(examples) == 1
        assert examples[0].id == "ex-123"
        assert examples[0].name == "example1"

        client._transport.request.assert_called_once_with(
            "GET",
            "/api/v2/organizations/test-org/examples",
            params={"page[number]": 1, "page[size]": 100},
        )

    def test_list_examples_invalid_org(self, client):
        """Test listing examples with invalid organization."""
        with pytest.raises(InvalidOrgError):
            list(client.examples.list(""))

    def test_create_example(self, client):
        """Test creating an example."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "id": "ex-new",
                "type": "examples",
                "attributes": {
                    "name": "new-example",
                    "url": "https://new.example.com",
                },
            }
        }
        client._transport.request = MagicMock(return_value=mock_response)

        options = ExampleCreateOptions(
            name="new-example", url="https://new.example.com"
        )
        example = client.examples.create("test-org", options)

        assert example.id == "ex-new"
        assert example.name == "new-example"

    def test_read_example_invalid_id(self, client):
        """Test reading example with invalid ID."""
        with pytest.raises(InvalidExampleIDError):
            client.examples.read("")
```

#### 7. Create Example File (`examples/example.py`)

```python
#!/usr/bin/env python3
"""
Example Resource Management

This example demonstrates all available example operations in the Python TFE SDK.
"""

import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import ExampleCreateOptions, ExampleListOptions


def main():
    """Main function to demonstrate example operations."""
    print("\n" + "=" * 70)
    print("Example Resource Management")
    print("=" * 70)

    # Initialize client
    token = os.getenv("TFE_TOKEN")
    if not token:
        print("\nError: TFE_TOKEN environment variable not set")
        return

    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    config = TFEConfig(address=address, token=token)
    client = TFEClient(config)

    organization_name = os.getenv("TFE_ORGANIZATION", "your-org-name")
    print(f"\nOrganization: {organization_name}")
    print(f"API Address: {address}")
    print("-" * 70)

    # List examples
    print("\n1. Listing Examples:")
    try:
        examples = list(client.examples.list(organization_name))
        print(f"   Found {len(examples)} examples")
        for example in examples[:5]:
            print(f"     - {example.name} (ID: {example.id})")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 70)
    print("Example Resource Management Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
```

### Key Conventions

1. **Models**: Use Pydantic with `Field` for validation and JSON:API alias mapping
2. **Resources**: Inherit from `_Service`, use `self.t.request()` for HTTP calls
3. **Validation**: Use `valid_string_id()` utility and raise appropriate errors
4. **Iterator Pattern**: For list operations, use `self._list()` for auto-pagination
5. **JSON:API Format**: Request/response bodies use `{"data": {"type": "...", "attributes": {...}}}`
6. **Tests**: Mock `client._transport.request`, test all methods and error conditions
7. **Documentation**: Add docstrings with Args/Returns/Yields sections

## Adding API Changes That Are Not Generally Available

In general, beta features should not be merged/released until generally available (GA). However, the maintainers recognize almost any reason to release beta features on a case-by-case basis. These could include: partial customer availability, software dependency, or any reason short of feature completeness.

Beta features, if released, should be clearly documented:

```python
class Example(BaseModel):
    """Represents an example resource."""
    
    # Note: This field is still in BETA and subject to change.
    example_new_field: bool | None = Field(
        None, alias="example-new-field", description="Beta feature"
    )
```

When adding test cases, you can temporarily skip beta features to omit them from running in CI:

```python
@pytest.mark.skip(reason="Beta feature - skip until GA")
def test_beta_feature(self, client):
    """Test beta feature."""
    # test logic here
```

**Note**: After your PR has been merged, and the feature either reaches general availability, you should remove the skip decorator.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use type hints throughout (enforced by mypy)
- Use descriptive variable names
- Keep functions focused and single-purpose
- Add docstrings to all public classes and methods
- Use f-strings for string formatting
- Prefer list comprehensions over map/filter when readable

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code is formatted (`make fmt`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] All tests pass (`make test`)
- [ ] New functionality has unit tests
- [ ] CHANGELOG.md is updated
- [ ] Example file is added/updated (if adding resource)
- [ ] Docstrings are added to new classes/methods

## Questions?

Feel free to open an issue for questions about contributing, or reach out to the maintainers for guidance on larger changes.
