"""
Base service class for Terraform Enterprise/Cloud API services.

This module provides an abstract base class that all TFE API services
should inherit from. It provides common functionality for HTTP requests,
response handling, and JSONAPI processing.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from tfe.utils import build_query_params, deserialize_jsonapi, prepare_jsonapi_data

logger = logging.getLogger(__name__)

# Generic type for model classes
T = TypeVar("T")


class BaseService(ABC, Generic[T]):
    """
    Abstract base class for all TFE API services.

    Generic type T represents the model class that this service manages.
    For example, OrganizationsService would be BaseService[Organization].
    """

    def __init__(self, client: Any) -> None:
        """client: The main TFE client instance that provides HTTP access"""
        self.client = client

    def _make_request(self, method: str, path: str, **kwargs: Any) -> Any:
        """
        Make an HTTP request using the client's HTTP client.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (will be joined with base_url)
            **kwargs: Additional arguments to pass to the HTTP client

        Returns:
            The HTTP response
        """
        # Build full URL
        url = self.client.base_url.rstrip("/") + "/" + path.lstrip("/")

        # Get the HTTP client from the config
        http_client = self.client.config.http_client

        # Log the request
        self._log_request(method, path, **kwargs)
        method = method.upper()

        # Make the request
        if method == "GET":
            return http_client.get(url, **kwargs)
        elif method == "POST":
            return http_client.post(url, **kwargs)
        elif method == "PUT":
            return http_client.put(url, **kwargs)
        elif method == "PATCH":
            return http_client.patch(url, **kwargs)
        elif method == "DELETE":
            return http_client.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _handle_response(self, response: Any, model_class: type | None = None) -> Any:
        """
        Handle the API response and optionally deserialize to a model.

        Args:
            response: The HTTP response from the API
            model_class: Optional model class to deserialize the response to

        Returns:
            The deserialized response or raw response data
        """
        if response.status_code == 204:  # No Content
            return None

        try:
            data = response.json()

            if model_class and data:
                # Handle JSONAPI format
                if "data" in data:
                    return deserialize_jsonapi(data, model_class)
                else:
                    # Handle regular JSON response
                    return model_class(**data) if isinstance(data, dict) else data

            return data

        except ValueError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return response.text

    def _prepare_jsonapi_data(
        self, data: dict[str, Any], resource_type: str
    ) -> dict[str, Any]:
        """Prepare data for JSONAPI format."""
        return prepare_jsonapi_data(data, resource_type)

    def _build_query_params(self, **kwargs: Any) -> dict[str, Any]:
        """Build query parameters for API requests."""
        return build_query_params(**kwargs)

    def _log_request(self, method: str, path: str, **kwargs: Any) -> None:
        """Log API request details for debugging."""
        logger.debug(f"Making {method} request to {path}")
        if kwargs:
            logger.debug(f"Request parameters: {kwargs}")

    @abstractmethod
    def list(self, **kwargs: Any) -> list[T]:
        """List resources instances."""
        pass

    @abstractmethod
    def get(self, resource_id: str, **kwargs: Any) -> T | None:
        """Get a single resource by ID."""
        pass

    @abstractmethod
    def create(self, data: dict[str, Any]) -> T:
        """Create a new resource."""
        pass

    @abstractmethod
    def update(self, resource_id: str, data: dict[str, Any]) -> T:
        """Update an existing resource."""
        pass

    @abstractmethod
    def delete(self, resource_id: str) -> bool:
        """Delete a resource."""
        pass
