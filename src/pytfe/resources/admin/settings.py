# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from .._base import _Service


class AdminSettings(_Service):
    def terraform_versions(self) -> Any:
        r = self.t.request("GET", "/api/v2/admin/terraform-versions")
        return r.json()
