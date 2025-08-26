"""
Main client class for Terraform Enterprise/Cloud API.
"""


class TerraformEnterpriseClient:
    """Simple client for Terraform Enterprise/Cloud API."""

    def __init__(self, token: str, base_url: str = "https://app.terraform.io/api/v2/"):
        """Initialize the client with API token and base URL."""
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"

    def get_base_url(self) -> str:
        """Get the base URL."""
        return self.base_url

    def foo(self) -> str:
        """Simple foo method for testing."""
        return "foo"

    def bar(self) -> str:
        """Simple bar method for testing."""
        return "bar"

    def foobar(self) -> str:
        """Combine foo and bar."""
        return f"{self.foo()}{self.bar()}"
