"""
Base service class for Terraform Enterprise/Cloud API services.

This module provides an abstract base class that all TFE API services
should inherit from. It provides common functionality for HTTP requests
and defines the interface that all service implementations must follow.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from requests import Session
from requests.models import Response as RequestResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Response")


class Response(ABC):
    @classmethod
    @abstractmethod
    def from_http_response(cls: type[T], response: RequestResponse) -> T:
        """Create an instance of the endpoint specific response class from an HTTP response."""
        pass


class Endpoint:
    """Base class for all TFE API services."""

    def __init__(self, client: Session) -> None:
        self._http_client = client

    def _make_request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> RequestResponse:
        """
        Make an HTTP request using the client's HTTP client.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path
            json: JSON payload for POST, PUT, PATCH requests
        Returns:
            The HTTP response from requests library
        """
        method = method.upper()

        # Make the request
        match method:
            case "GET":
                return self._http_client.get(path)
            case "POST":
                return self._http_client.post(path, json=json)
            case "PUT":
                return self._http_client.put(path, json=json)
            case "PATCH":
                return self._http_client.patch(path, json=json)
            case "DELETE":
                return self._http_client.delete(path)
            case _:
                raise ValueError(f"Unsupported HTTP method: {method}")

    def _get(self, path: str) -> RequestResponse:
        return self._make_request("GET", path)

    def _post(self, path: str, data: dict) -> RequestResponse:
        return self._make_request("POST", path, json=data)

    def _put(self, path: str, data: dict) -> RequestResponse:
        return self._make_request("PUT", path, json=data)

    def _patch(self, path: str, data: dict) -> RequestResponse:
        return self._make_request("PATCH", path, json=data)

    def _delete(self, path: str) -> RequestResponse:
        return self._make_request("DELETE", path)
