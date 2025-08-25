"""
Simple tests for the client.
"""

from python_tfe.client import TerraformEnterpriseClient


def test_foo():
    """Test foo returns foo."""
    client = TerraformEnterpriseClient("token")
    assert client.foo() == "foo"


def test_bar():
    """Test bar returns bar."""
    client = TerraformEnterpriseClient("token")
    assert client.bar() == "bar"
