# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from . import errors, models
from ._logging import setup_logging
from .client import TFEClient
from .config import TFEConfig

try:
    __version__ = _pkg_version("pytfe")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.0.0+unknown"

__all__ = [
    "TFEConfig",
    "TFEClient",
    "errors",
    "models",
    "setup_logging",
    "__version__",
]
