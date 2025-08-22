"""
PyTFE - Python SDK for Terraform Enterprise/Cloud API

This package provides a Python client for interacting with the Terraform Enterprise
and Terraform Cloud APIs, similar to HashiCorp's go-tfe SDK.
"""

__version__ = "0.1.0"
__author__ = "Ansible-Tfe-Development-Team"
__email__ = "sivaselvan.i@hasicorp.com"

from .client import Client
from .config import Config
from .exceptions import (
    PyTFEException,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)

__all__ = [
    "Client",
    "Config",
    "PyTFEException",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]
