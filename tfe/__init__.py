"""
Python client library for Terraform Enterprise/Cloud API.

This package provides a Python interface to the Terraform Enterprise
and Terraform Cloud APIs, allowing you to programmatically manage
workspaces, runs, state files, and other TFE/TFC resources.
"""

from tfe.client import Client, TFEClientError
from tfe.config import Config
from tfe.endpoint import Endpoint, ResourceDataProtocol, ResourceResponseProtocol

__all__ = ["Client", "TFEClientError", "Config", "Endpoint", "ResourceDataProtocol", "ResourceResponseProtocol"]
