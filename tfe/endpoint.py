"""
Base service class for Terraform Enterprise/Cloud API services.

This module provides an abstract base class that all TFE API services
should inherit from. It provides common functionality for HTTP requests
and defines the interface that all service implementations must follow.
"""

import logging
from typing import Any

from requests import Session, exceptions
from requests.models import Response as RequestResponse

from tfe.error_utils import handle_http_error
from tfe.exception import (
    TFEConnectionException,
    TFEEndpointException,
    TFETimeoutException,
)

logger = logging.getLogger(__name__)


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
        response: RequestResponse | None = None

        try:
            logger.debug("Making %s request to %s", method, path)

            # Make the request
            match method:
                case "GET":
                    response = self._http_client.get(path)
                case "POST":
                    response = self._http_client.post(path, json=json)
                case "PUT":
                    response = self._http_client.put(path, json=json)
                case "PATCH":
                    response = self._http_client.patch(path, json=json)
                case "DELETE":
                    response = self._http_client.delete(path)
                case _:
                    raise TFEEndpointException(
                        message=f"Unsupported HTTP method: {method}",
                        method=method,
                        path=path,
                    )

            # Check for HTTP errors and raise appropriate TFE exceptions
            response.raise_for_status()
            return response

        except exceptions.ConnectionError as e:
            logger.error(
                "Connection error while making %s request to %s: %s", method, path, e
            )
            raise TFEConnectionException(
                message="Failed to connect to TFE API",
                method=method,
                path=path,
                cause=e,
            ) from e
        except exceptions.Timeout as e:
            logger.error(
                "Timeout error while making %s request to %s: %s", method, path, e
            )
            raise TFETimeoutException(
                message="Request timed out", method=method, path=path, cause=e
            ) from e
        except exceptions.HTTPError as e:
            handle_http_error(method, path, e)
        except exceptions.RequestException as e:
            logger.error(
                "Request error while making %s request to %s: %s", method, path, e
            )
            raise TFEEndpointException(
                message=f"Request failed: {str(e)}",
                method=method,
                path=path,
                cause=e,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error while making %s request to %s: %s", method, path, e
            )
            raise TFEEndpointException(
                message=f"Unexpected error occurred during {method} request",
                method=method,
                path=path,
                cause=e,
            ) from e

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
