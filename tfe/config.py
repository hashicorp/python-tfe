import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = "https://app.terraform.io"
DEFAULT_BASE_PATH = "/api/v2/"
DEFAULT_REGISTRY_PATH = "/api/registry"


@dataclass
class Config:
    # Address of the Terraform Enterprise API
    address: str = ""

    # Base path for which the API is served
    base_path: str = DEFAULT_BASE_PATH

    # Base path for the Terraform Enterprise Registry API
    registry_base_path: str = DEFAULT_REGISTRY_PATH

    # API token used to access the terraform enterprise API
    token: str | None = field(default_factory=lambda: os.getenv("TFE_TOKEN"))

    # Headers to include in API requests
    # TODO: Do we need headers ? we can pass them directly to http_client, but this will differ from the go-tfe module
    headers: dict[str, str] | None = None

    # Custom request session which needs to be used
    http_client: requests.Session = field(default_factory=requests.Session)

    # Callable to run before any request is retried
    retry_log_hook: Callable[[int, requests.Response], None] | None = None

    # Enable/Disable retry logic
    retry_server_errors: bool = False

    def __post_init__(self) -> None:
        tfe_address = os.getenv("TFE_ADDRESS", "")
        if tfe_address:
            self.address = tfe_address

        if not self.address:
            if os.getenv("TFE_HOST"):
                self.address = f"https://{os.getenv('TFE_HOST')}"
            else:
                self.address = DEFAULT_ADDRESS

        if self.headers is None:
            self.headers = {}

        if (
            "User-Agent" not in self.http_client.headers
            and "User-Agent" not in self.headers
        ):
            self.headers["User-Agent"] = "python-tfe"

        if (
            self.token
            and "Authorization" not in self.http_client.headers
            and "Authorization" not in self.headers
        ):
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.http_client.headers.update(self.headers)
