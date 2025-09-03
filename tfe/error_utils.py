"""
Utility functions for handling HTTP errors and parsing error responses in TFE API client.
"""

import json
import logging
from typing import Any, NoReturn

from requests import exceptions
from requests.models import Response as RequestResponse

from tfe.exception import (
    TFEEndpointException,
    TFEForbiddenException,
    TFENotFoundException,
    TFEServerException,
    TFEUnauthorizedException,
    TFEValidationException,
)

logger = logging.getLogger(__name__)


def extract_error_data(response: RequestResponse | None) -> dict[str, Any] | None:
    """Extract error data from HTTP response."""
    if not response:
        return None
    try:
        result = response.json()
        return result if isinstance(result, dict) else {"text": str(result)}
    except (ValueError, json.JSONDecodeError):
        return {"text": response.text}


def parse_tfe_error_response(response_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse TFE API error response and extract meaningful error information.
    """
    error_info: dict[str, Any] = {
        "message": "Unknown API error",
        "errors": [],
        "error_code": None,
    }
    try:
        if "errors" in response_data:
            errors = response_data["errors"]
            if isinstance(errors, list) and errors:
                error_details = []
                for error in errors:
                    if isinstance(error, dict):
                        detail = error.get(
                            "detail", error.get("title", "Unknown error")
                        )
                        error_details.append(detail)
                        if "code" in error and not error_info["error_code"]:
                            error_info["error_code"] = error["code"]
                error_info["errors"] = error_details
                error_info["message"] = "; ".join(
                    str(detail) for detail in error_details
                )
        elif "message" in response_data:
            error_info["message"] = response_data["message"]
        elif "error" in response_data:
            error_info["message"] = response_data["error"]
    except (KeyError, TypeError, AttributeError) as e:
        logger.warning("Failed to parse error response: %s", e)
        error_info["message"] = f"Failed to parse error response: {response_data}"
    return error_info


def handle_http_error(method: str, path: str, error: exceptions.HTTPError) -> NoReturn:
    """
    Handle HTTP errors with specific status codes and raise appropriate exceptions.
    """
    status_code = error.response.status_code if error.response else None
    error_data = extract_error_data(error.response)
    logger.error(
        "HTTP error while making %s request to %s: %s (Status: %s)",
        method,
        path,
        error,
        status_code,
    )
    STATUS_CODE_MAPPING: dict[int, tuple[type[TFEEndpointException], str]] = {
        401: (
            TFEUnauthorizedException,
            "Authentication failed - invalid or missing token",
        ),
        403: (TFEForbiddenException, "Access forbidden - insufficient permissions"),
        404: (TFENotFoundException, "Resource not found"),
        422: (TFEValidationException, "Validation failed"),
    }
    exception_class: type[TFEEndpointException]
    if status_code and 500 <= status_code < 600:
        exception_class = TFEServerException
        message = "TFE server error"
    else:
        if status_code is not None:
            exception_class, message = STATUS_CODE_MAPPING.get(
                status_code, (TFEEndpointException, "HTTP error occurred")
            )
        else:
            exception_class, message = TFEEndpointException, "HTTP error occurred"
    if status_code == 422:
        parsed_errors = parse_tfe_error_response(error_data) if error_data else {}
        message = parsed_errors.get("message", message)
    raise exception_class(
        message=message,
        status_code=status_code,
        error_data=error_data,
        method=method,
        path=path,
        cause=error,
    ) from error
