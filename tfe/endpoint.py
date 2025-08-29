"""
Base service class for Terraform Enterprise/Cloud API services.

This module provides an abstract base class that all TFE API services
should inherit from. It provides common functionality for HTTP requests
and defines the interface that all service implementations must follow.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol

from requests import Response

from tfe.client import Client

logger = logging.getLogger(__name__)


class ResourceDataProtocol(Protocol):
    """Protocol defining the structure of a single TFE resource in API response."""

    id: str
    type: str
    attributes: dict[str, Any]


class ResourceResponseProtocol(Protocol):
    """Protocol defining the structure of a TFE API response."""

    data: ResourceDataProtocol | list[ResourceDataProtocol]


class Endpoint(ABC):
    """Abstract base class for all TFE API services."""

    def __init__(self, client: Client) -> None:
        """
        Initialize the endpoint with a TFE client that provides HTTP access."""
        self._http_client = client.config.http_client
        self._base_url = client.base_url

    def _make_request(self, method: str, path: str, **kwargs: Any) -> Response:
        """
        Make an HTTP request using the client's HTTP client.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (will be joined with base_url)
            **kwargs: Additional arguments to pass to the HTTP client

        Returns:
            The HTTP response from requests library
        """
        # Build full URL
        url = self._base_url.rstrip("/") + "/" + path.lstrip("/")

        # Log the request directly here
        logger.debug(f"Making {method.upper()} request to {path}")

        method = method.upper()

        # Make the request
        if method == "GET":
            return self._http_client.get(url, **kwargs)
        elif method == "POST":
            return self._http_client.post(url, **kwargs)
        elif method == "PUT":
            return self._http_client.put(url, **kwargs)
        elif method == "PATCH":
            return self._http_client.patch(url, **kwargs)
        elif method == "DELETE":
            return self._http_client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    @abstractmethod
    def list_resources(
        self,
        page: int | None = None,
        per_page: int | None = None,
        search: str | None = None,
        include: list[str] | None = None,
        filter: dict[str, str] | None = None,
        sort: str | None = None,
        **additional_params: Any,
    ) -> ResourceResponseProtocol:
        """
        List resources instances.

        Args:
            page: Page number for pagination (1-based)
            per_page: Number of items per page
            search: Search query string
            include: List of related resources to include
            filter: Filter criteria for resources
            sort: Sort order for resources
            **additional_params: Additional parameters specific to the endpoint

        Returns:
            API response with list of resources in data field
        """
        pass

    @abstractmethod
    def get_resource(
        self,
        resource_id: str,
        include: list[str] | None = None,
        **additional_params: Any,
    ) -> ResourceResponseProtocol:
        """
        Get a single resource by ID.

        Args:
            resource_id: The unique identifier of the resource
            include: List of related resources to include
            **additional_params: Additional parameters specific to the endpoint

        Returns:
            API response with single resource in data field
        """
        pass

    @abstractmethod
    def create_resource(
        self, data: dict[str, Any], **additional_params: Any
    ) -> ResourceResponseProtocol:
        """
        Create a new resource.

        Args:
            data: Dictionary containing the resource data to create
            **additional_params: Additional parameters specific to the endpoint

        Returns:
            API response with newly created resource in data field
        """
        pass

    @abstractmethod
    def update_resource(
        self, resource_id: str, data: dict[str, Any], **additional_params: Any
    ) -> ResourceResponseProtocol:
        """
        Update an existing resource.

        Args:
            resource_id: The unique identifier of the resource to update
            data: Dictionary containing the updated resource data
            **additional_params: Additional parameters specific to the endpoint

        Returns:
            API response with updated resource in data field
        """
        pass

    @abstractmethod
    def delete_resource(self, resource_id: str, **additional_params: Any) -> bool:
        """
        Delete a resource.

        Args:
            resource_id: The unique identifier of the resource to delete
            **additional_params: Additional parameters specific to the endpoint

        Returns:
            True if deletion was successful, False otherwise
        """
        pass