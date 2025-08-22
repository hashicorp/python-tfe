"""
Main client class for the PyTFE SDK.

This module provides the main Client class that serves as the entry point
for interacting with the Terraform Enterprise/Cloud API.
"""

import time
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from .exceptions import (
    PyTFEException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ServerError,
    RateLimitError,
    ConnectionError as PyTFEConnectionError,
)


class Client:
    """Main client for interacting with Terraform Enterprise/Cloud API."""
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the PyTFE client.
        
        Args:
            config: Configuration object. If None, uses default configuration
                   with environment variables.
        """
        self.config = config or Config()
        self._session = self._create_session()
        
        # Initialize service clients
        from .services.organizations import OrganizationService
        self.organizations = OrganizationService(self)
    
    def _create_session(self) -> requests.Session:
        """Create and configure the HTTP session."""
        session = requests.Session()
        
        # Set default headers
        session.headers.update(self.config.auth_headers)
        
        # Configure retries if enabled
        if self.config.retry_server_errors:
            retry_strategy = Retry(
                total=self.config.max_retries,
                status_forcelist=[500, 502, 503, 504],
                backoff_factor=self.config.retry_backoff_factor,
                allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: API endpoint (relative to base API URL).
            params: Query parameters.
            json_data: JSON data for request body.
            headers: Additional headers.
            **kwargs: Additional arguments passed to requests.
        
        Returns:
            Response object.
            
        Raises:
            PyTFEException: For various API errors.
        """
        url = urljoin(self.config.api_url + "/", endpoint.lstrip("/"))
        print("url", url, self.config.api_url)
        
        # Merge headers
        request_headers = self.config.auth_headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.config.timeout,
                **kwargs,
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    time.sleep(int(retry_after))
                    # Retry once after rate limit
                    response = self._session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json_data,
                        headers=request_headers,
                        timeout=self.config.timeout,
                        **kwargs,
                    )
            
            self._handle_response_errors(response)
            return response
            
        except requests.exceptions.ConnectionError as e:
            raise PyTFEConnectionError(f"Connection error: {e}") from e
        except requests.exceptions.Timeout as e:
            raise PyTFEConnectionError(f"Request timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise PyTFEException(f"Request failed: {e}") from e
    
    def _handle_response_errors(self, response: requests.Response) -> None:
        """
        Handle HTTP response errors by raising appropriate exceptions.
        
        Args:
            response: HTTP response object.
            
        Raises:
            Appropriate PyTFEException subclass based on status code.
        """
        if response.status_code < 400:
            return
        
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text or "Unknown error"}
        
        error_message = self._extract_error_message(error_data)
        
        if response.status_code == 401:
            raise AuthenticationError(
                error_message, response.status_code, error_data
            )
        elif response.status_code == 403:
            raise AuthorizationError(
                error_message, response.status_code, error_data
            )
        elif response.status_code == 404:
            raise NotFoundError(
                error_message, response.status_code, error_data
            )
        elif response.status_code == 409:
            raise ConflictError(
                error_message, response.status_code, error_data
            )
        elif response.status_code == 422:
            raise ValidationError(
                error_message, response.status_code, error_data
            )
        elif response.status_code == 429:
            raise RateLimitError(
                error_message, response.status_code, error_data
            )
        elif response.status_code >= 500:
            raise ServerError(
                error_message, response.status_code, error_data
            )
        else:
            raise PyTFEException(
                error_message, response.status_code, error_data
            )
    
    def _extract_error_message(self, error_data: Dict[str, Any]) -> str:
        """
        Extract error message from API error response.
        
        Args:
            error_data: Error response data.
            
        Returns:
            Formatted error message.
        """
        # Try different possible error message formats
        if isinstance(error_data, dict):
            # JSON API format
            if "errors" in error_data and isinstance(error_data["errors"], list):
                errors = error_data["errors"]
                if errors:
                    first_error = errors[0]
                    if isinstance(first_error, dict):
                        return first_error.get("detail", first_error.get("title", "Unknown error"))
            
            # Simple message format
            if "message" in error_data:
                return str(error_data["message"])
            
            # Error field
            if "error" in error_data:
                return str(error_data["error"])
        
        return "Unknown error"
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Make a GET request."""
        return self._make_request("GET", endpoint, params=params, **kwargs)
    
    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Make a POST request."""
        return self._make_request("POST", endpoint, json_data=json_data, **kwargs)
    
    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Make a PUT request."""
        return self._make_request("PUT", endpoint, json_data=json_data, **kwargs)
    
    def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> requests.Response:
        """Make a PATCH request."""
        return self._make_request("PATCH", endpoint, json_data=json_data, **kwargs)
    
    def delete(
        self,
        endpoint: str,
        **kwargs: Any
    ) -> requests.Response:
        """Make a DELETE request."""
        return self._make_request("DELETE", endpoint, **kwargs)
