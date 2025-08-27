import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = "https://app.terraform.io"
DEFAULT_BASE_PATH = "/api/v2/"
DEFAULT_REGISTRY_PATH = "/api/registry"


@dataclass
class Config:
    # Address of the Terraform Enterprise API
    address: str = field(default="")

    # Base path for which the API is served
    base_path: str = DEFAULT_BASE_PATH

    # Base path for the Terraform Enterprise Registry API
    registry_base_path: str = DEFAULT_REGISTRY_PATH

    # API token used to access the terraform enterprise API
    token: str = field(default="")

    # Headers to include in API requests
    # TODO: Do we need headers ? we can pass them directly to http_client, but this will differ from the go-tfe module
    headers: dict[str, str] = field(default_factory=dict)

    # Custom request session which needs to be used
    http_client: requests.Session = field(default_factory=requests.Session)

    # Callable to run before any request is retried
    retry_log_hook: Callable[[int, requests.Response], None] | None = None

    # Enable/Disable retry logic
    retry_server_errors: bool = False

    def _set_address(self) -> None:
        tfe_address = os.getenv("TFE_ADDRESS", "")
        if tfe_address:
            self.address = tfe_address

        if not self.address:
            if os.getenv("TFE_HOST"):
                self.address = f"https://{os.getenv('TFE_HOST')}"
            else:
                self.address = DEFAULT_ADDRESS

    def _set_token(self) -> None:
        if not self.token:
            self.token = os.getenv("TFE_TOKEN", "")

        if (
            self.token
            and "Authorization" not in self.http_client.headers
            and "Authorization" not in self.headers
        ):
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _set_user_agent(self) -> None:
        if (
            "User-Agent" not in self.http_client.headers
            and "User-Agent" not in self.headers
        ):
            self.headers["User-Agent"] = "python-tfe"

    def _validate_config(self) -> None:
        if not self.http_client.headers.get("Authorization"):
            raise ValueError(
                "API token is required, please set the TFE_TOKEN environment variable or the token field in the configuration."
            )
        parsed_url = urlparse(self.address)
        if not parsed_url.scheme:
            raise ValueError("Address must include protocol (http/https)")

    def __post_init__(self) -> None:
        self._set_address()
        self._set_token()
        self._set_user_agent()
        self.http_client.headers.update(self.headers)
        self._validate_config()
