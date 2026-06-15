# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ..._http import HTTPTransport
from ._organizations import _AdminOrganizations
from ._runs import _AdminRuns
from ._saml import _AdminSAMLSettings
from ._scim import _AdminSCIMSettings, _AdminSCIMTokens
from ._smtp import _AdminSMTPSettings
from ._users import _AdminUsers
from ._versions import (
    _AdminOpaVersions,
    _AdminSentinelVersions,
    _AdminTerraformVersions,
)
from ._workspaces import _AdminWorkspaces


class AdminClient:
    def __init__(self, transport: HTTPTransport) -> None:
        self.saml_settings = _AdminSAMLSettings(transport)
        self.scim_settings = _AdminSCIMSettings(transport)
        self.scim_tokens = _AdminSCIMTokens(transport)
        self.smtp_settings = _AdminSMTPSettings(transport)
        self.terraform_versions = _AdminTerraformVersions(transport)
        self.opa_versions = _AdminOpaVersions(transport)
        self.sentinel_versions = _AdminSentinelVersions(transport)
        self.runs = _AdminRuns(transport)
        self.organizations = _AdminOrganizations(transport)
        self.users = _AdminUsers(transport)
        self.workspaces = _AdminWorkspaces(transport)
