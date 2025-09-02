"""
Base service class for Terraform Enterprise/Cloud API services.

This module provides an abstract base class that all TFE API services
should inherit from. It provides common functionality for HTTP requests
and defines the interface that all service implementations must follow.
"""

import json
import logging
from typing import Any, NoReturn

from requests import Session, exceptions
from requests.models import Response as RequestResponse

from tfe.exception import (
    TFEConnectionException,
    TFEEndpointException,
    TFEForbiddenException,
    TFENotFoundException,
    TFEServerException,
    TFETimeoutException,
    TFEUnauthorizedException,
    TFEValidationException,
)

logger = logging.getLogger(__name__)


class Endpoint:
    """Base class for all TFE API services."""

    def __init__(self, client: Session) -> None:
        self._http_client = client

    def _handle_connection_error(
        self, method: str, path: str, error: Exception
    ) -> NoReturn:
        """Handle connection-related errors."""
        logger.error(
            "Connection error while making %s request to %s: %s", method, path, error
        )
        raise TFEConnectionException(
            message="Failed to connect to TFE API",
            method=method,
            path=path,
            cause=error,
        )

    def _handle_timeout_error(
        self, method: str, path: str, error: Exception
    ) -> NoReturn:
        """Handle timeout errors."""
        logger.error(
            "Timeout error while making %s request to %s: %s", method, path, error
        )
        raise TFETimeoutException(
            message="Request timed out", method=method, path=path, cause=error
        )

    def _handle_http_error(
        self, method: str, path: str, error: exceptions.HTTPError
    ) -> NoReturn:
        """Handle HTTP errors with specific status codes."""
        status_code = error.response.status_code if error.response else None
        error_data = self._extract_error_data(error.response)

        logger.error(
            "HTTP error while making %s request to %s: %s (Status: %s)",
            method,
            path,
            error,
            status_code,
        )

        # Map status code to specific exception
        STATUS_CODE_MAPPING: dict[int, tuple[type[TFEEndpointException], str]] = {
            401: (
                TFEUnauthorizedException,
                "Authentication failed - invalid or missing token",
            ),
            403: (TFEForbiddenException, "Access forbidden - insufficient permissions"),
            404: (TFENotFoundException, "Resource not found"),
            422: (TFEValidationException, "Validation failed"),
        }

        # Handle 5xx server errors
        if status_code and 500 <= status_code < 600:
            exception_class: type[TFEEndpointException] = TFEServerException
            message = "TFE server error"
        else:
            # Get exception class and message from mapping, or use default
            if status_code is not None:
                exception_class, message = STATUS_CODE_MAPPING.get(
                    status_code, (TFEEndpointException, "HTTP error occurred")
                )
            else:
                exception_class, message = TFEEndpointException, "HTTP error occurred"

        # Special handling for validation errors (422)
        if status_code == 422:
            parsed_errors = (
                self.parse_tfe_error_response(error_data) if error_data else {}
            )
            message = parsed_errors.get("message", message)

        raise exception_class(
            message=message,
            status_code=status_code,
            error_data=error_data,
            method=method,
            path=path,
            cause=error,
        )

    def _handle_request_error(
        self, method: str, path: str, error: Exception
    ) -> NoReturn:
        """Handle general request errors."""
        logger.error(
            "Request error while making %s request to %s: %s", method, path, error
        )
        raise TFEEndpointException(
            message=f"Request failed: {str(error)}",
            method=method,
            path=path,
            cause=error,
        )

    def _handle_unexpected_error(
        self, method: str, path: str, error: Exception
    ) -> NoReturn:
        """Handle unexpected errors."""
        logger.error(
            "Unexpected error while making %s request to %s: %s", method, path, error
        )
        raise TFEEndpointException(
            message=f"Unexpected error occurred during {method} request",
            method=method,
            path=path,
            cause=error,
        )

    def _extract_error_data(
        self, response: RequestResponse | None
    ) -> dict[str, Any] | None:
        """Extract error data from HTTP response."""
        if not response:
            return None

        try:
            result = response.json()
            return result if isinstance(result, dict) else {"text": str(result)}
        except (ValueError, json.JSONDecodeError):
            return {"text": response.text}

    def parse_tfe_error_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse TFE API error response and extract meaningful error information.

        Args:
            response_data: The JSON response from the TFE API

        Returns:
            Dictionary containing parsed error information
        """
        error_info: dict[str, Any] = {
            "message": "Unknown API error",
            "errors": [],
            "error_code": None,
        }

        try:
            # Handle JSON:API error format
            if "errors" in response_data:
                errors = response_data["errors"]
                if isinstance(errors, list) and errors:
                    # Extract error details
                    error_details = []
                    for error in errors:
                        if isinstance(error, dict):
                            detail = error.get(
                                "detail", error.get("title", "Unknown error")
                            )
                            error_details.append(detail)

                            # Extract error code if available
                            if "code" in error and not error_info["error_code"]:
                                error_info["error_code"] = error["code"]

                    error_info["errors"] = error_details
                    error_info["message"] = "; ".join(
                        str(detail) for detail in error_details
                    )

            # Handle simple error message format
            elif "message" in response_data:
                error_info["message"] = response_data["message"]

            # Handle error field
            elif "error" in response_data:
                error_info["message"] = response_data["error"]

        except (KeyError, TypeError, AttributeError) as e:
            logger.warning("Failed to parse error response: %s", e)
            error_info["message"] = f"Failed to parse error response: {response_data}"

        return error_info

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
            self._handle_connection_error(method, path, e)
        except exceptions.Timeout as e:
            self._handle_timeout_error(method, path, e)
        except exceptions.HTTPError as e:
            self._handle_http_error(method, path, e)
        except exceptions.RequestException as e:
            self._handle_request_error(method, path, e)
        except Exception as e:
            self._handle_unexpected_error(method, path, e)

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
