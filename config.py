"""
Configuration management for the PyTFE SDK.

This module provides configuration options for connecting to Terraform Enterprise
or Terraform Cloud APIs, including authentication and connection settings.
"""

import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class Config:
    """Configuration class for PyTFE client."""
    
    def __init__(
        self,
        address: Optional[str] = None,
        token: Optional[str] = None,
        hostname: Optional[str] = None,
        retry_server_errors: bool = True,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.3,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize configuration.
        
        Args:
            address: Full URL of the Terraform Enterprise/Cloud instance.
                   Falls back to TFE_ADDRESS environment variable.
            token: API token for authentication.
                  Falls back to TFE_TOKEN environment variable.
            hostname: Hostname of the TFE instance (alternative to address).
                     Falls back to TFE_HOSTNAME environment variable.
            retry_server_errors: Whether to retry on server errors (5xx).
            max_retries: Maximum number of retries for failed requests.
            retry_backoff_factor: Backoff factor for retries.
            timeout: Request timeout in seconds.
            headers: Additional headers to include in requests.
        """
        self.address = self._resolve_address(address, hostname)
        self.token = token or os.getenv("TFE_TOKEN")
        self.retry_server_errors = retry_server_errors
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.timeout = timeout
        self.headers = headers or {}
        print(self.address, self.token, self.retry_server_errors, self.max_retries, self.retry_backoff_factor, self.timeout, self.headers)
        
        self._validate_config()
    
    def _resolve_address(self, address: Optional[str], hostname: Optional[str]) -> str:
        """Resolve the API address from various sources."""
        # Priority: address parameter -> TFE_ADDRESS env -> hostname parameter -> TFE_HOSTNAME env
        if address:
            return self._normalize_address(address)
        
        env_address = os.getenv("TFE_ADDRESS")
        if env_address:
            return self._normalize_address(env_address)
        
        if hostname:
            return f"https://{hostname}"
        
        env_hostname = os.getenv("TFE_HOSTNAME")
        if env_hostname:
            return f"https://{env_hostname}"
        
        # Default to Terraform Cloud
        return "https://app.terraform.io"
    
    def _normalize_address(self, address: str) -> str:
        """Normalize the address to ensure it's a valid URL."""
        if not address.startswith(("http://", "https://")):
            address = f"https://{address}"
        
        # Remove trailing slash
        return address.rstrip("/")
    
    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not self.token:
            raise ValueError(
                "API token is required. Set TFE_TOKEN environment variable "
                "or provide token parameter."
            )
        
        # Validate URL format
        try:
            parsed = urlparse(self.address)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid address format: {self.address}")
        except Exception as e:
            raise ValueError(f"Invalid address format: {self.address}") from e
    
    @property
    def api_url(self) -> str:
        """Get the base API URL."""
        return f"{self.address}/api/v2"
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json",
        }
        headers.update(self.headers)
        return headers
    
    def __repr__(self) -> str:
        """String representation of config (without sensitive data)."""
        return (
            f"Config(address='{self.address}', "
            f"token='***', "
            f"retry_server_errors={self.retry_server_errors}, "
            f"max_retries={self.max_retries})"
        )
