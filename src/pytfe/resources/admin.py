# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Terraform Enterprise admin namespace.

Three admin-only services live behind ``client.admin``:

- ``client.admin.saml_settings``  -> SAML configuration (``/api/v2/admin/saml-settings``)
- ``client.admin.scim_settings``  -> SCIM enablement + site-admin mapping
- ``client.admin.scim_tokens``    -> SCIM provisioning tokens

All three endpoints are TFE-only. On HCP Terraform (SaaS) they return
404, which the SDK surfaces as :class:`pytfe.errors.NotFound`. The
nested ``admin`` namespace exists to express the trust boundary: these
endpoints require TFE site-admin permission and are not part of the
standard organisation API surface.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, TypeVar

from pydantic import BaseModel

from .._http import HTTPTransport
from ..errors import (
    InvalidSCIMTokenIDError,
    RequiredSCIMTokenDescriptionError,
)
from ..models.admin_identity import (
    AdminSAMLSettings,
    AdminSAMLSettingsUpdateOptions,
    AdminSCIMSettings,
    AdminSCIMSettingsUpdateOptions,
    AdminSCIMToken,
    AdminSCIMTokenCreateOptions,
    AdminSMTPSettings,
    AdminSMTPSettingsUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service

_SAML_TYPE = "saml-settings"
_SCIM_SETTINGS_TYPE = "scim-settings"
# The TFE API uses the generic JSON:API type ``authentication-tokens``
# for SCIM tokens; the endpoint path namespaces them under /admin/scim-tokens
# but the resource type string in the body is the shared one.
_SCIM_TOKEN_TYPE = "authentication-tokens"
_SMTP_TYPE = "smtp-settings"


_M = TypeVar("_M", bound=BaseModel)


def _parse_jsonapi(data: dict[str, Any], model: type[_M]) -> _M:
    """Lift JSON:API ``id`` into the attributes dict and validate against
    the given Pydantic model. Models in this file all use field aliases
    that match the wire hyphenated names, so no further translation is
    needed.
    """
    attrs = data.get("attributes") or {}
    return model.model_validate({"id": data.get("id"), **attrs})


# ---------------------------------------------------------------------------
# SAML settings
# ---------------------------------------------------------------------------


class _AdminSAMLSettings(_Service):
    """Resource for ``/api/v2/admin/saml-settings``.

    Singleton resource: the organisation has exactly one SAML
    configuration. There's no ``list`` or ``create`` — only read, partial
    update, and the action to revoke an old IdP certificate.
    """

    def read(self) -> AdminSAMLSettings:
        r = self.t.request("GET", "/api/v2/admin/saml-settings")
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)

    def update(self, options: AdminSAMLSettingsUpdateOptions) -> AdminSAMLSettings:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SAML_TYPE, "attributes": attrs}}
        r = self.t.request("PATCH", "/api/v2/admin/saml-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)

    def revoke_idp_cert(self) -> AdminSAMLSettings:
        """Promote the new IdP cert over the old one. Use after rolling
        the SAML signing certificate at the IdP. Returns the settings
        snapshot with ``old_idp_cert`` cleared.
        """
        r = self.t.request(
            "POST",
            "/api/v2/admin/saml-settings/actions/revoke-old-certificate",
        )
        return _parse_jsonapi(r.json()["data"], AdminSAMLSettings)


# ---------------------------------------------------------------------------
# SCIM settings
# ---------------------------------------------------------------------------


class _AdminSCIMSettings(_Service):
    """Resource for ``/api/v2/admin/scim-settings``.

    Singleton resource. Notable wire semantics:

    - PATCH ``enabled=False`` is rejected by the server; call
      :meth:`delete` to disable SCIM instead.
    - ``site_admin_group_scim_id`` accepts an explicit ``None`` which is
      sent as JSON ``null`` and unlinks the SCIM group from site-admin.
      :class:`AdminSCIMSettingsUpdateOptions.to_payload` handles the
      omit-vs-null distinction.
    - DELETE disables SCIM but does **not** revoke site-admin access
      already granted to users.
    """

    def read(self) -> AdminSCIMSettings:
        r = self.t.request("GET", "/api/v2/admin/scim-settings")
        return _parse_jsonapi(r.json()["data"], AdminSCIMSettings)

    def update(self, options: AdminSCIMSettingsUpdateOptions) -> AdminSCIMSettings:
        body = {
            "data": {
                "type": _SCIM_SETTINGS_TYPE,
                "attributes": options.to_payload(),
            }
        }
        r = self.t.request("PATCH", "/api/v2/admin/scim-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSCIMSettings)

    def delete(self) -> None:
        self.t.request("DELETE", "/api/v2/admin/scim-settings")


# ---------------------------------------------------------------------------
# SCIM tokens
# ---------------------------------------------------------------------------


class _AdminSCIMTokens(_Service):
    """Resource for ``/api/v2/admin/scim-tokens``.

    The plaintext ``token`` value is only returned on :meth:`create`.
    :meth:`read` and :meth:`list` always return ``None`` for that field —
    treat the create response as the only chance to capture the token.
    """

    def list(self) -> Iterator[AdminSCIMToken]:
        # The upstream endpoint is not documented as paginated, but the
        # response is still a JSON:API list. We use a single GET and
        # iterate the returned ``data`` array rather than the generic
        # ``self._list`` helper which adds ``page[]`` params.
        r = self.t.request("GET", "/api/v2/admin/scim-tokens")
        for item in r.json().get("data") or []:
            yield _parse_jsonapi(item, AdminSCIMToken)

    def create(self, options: AdminSCIMTokenCreateOptions) -> AdminSCIMToken:
        if not valid_string(options.description):
            raise RequiredSCIMTokenDescriptionError()
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SCIM_TOKEN_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/scim-tokens", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSCIMToken)

    def read(self, scim_token_id: str) -> AdminSCIMToken:
        if not valid_string_id(scim_token_id):
            raise InvalidSCIMTokenIDError()
        r = self.t.request("GET", f"/api/v2/admin/scim-tokens/{scim_token_id}")
        return _parse_jsonapi(r.json()["data"], AdminSCIMToken)

    def delete(self, scim_token_id: str) -> None:
        if not valid_string_id(scim_token_id):
            raise InvalidSCIMTokenIDError()
        self.t.request("DELETE", f"/api/v2/admin/scim-tokens/{scim_token_id}")


# ---------------------------------------------------------------------------
# SMTP settings
# ---------------------------------------------------------------------------


class _AdminSMTPSettings(_Service):
    """Resource for ``/api/v2/admin/smtp-settings``.

    Singleton resource. Notable wire semantics:

    - ``password`` is sensitive; the transport logger redacts it before
      it reaches debug output.
    - ``test-email-address`` is write-only — when supplied on update, TFE
      sends a verification email to that address as a side effect of the
      PATCH. The field is never returned on read.
    """

    def read(self) -> AdminSMTPSettings:
        r = self.t.request("GET", "/api/v2/admin/smtp-settings")
        return _parse_jsonapi(r.json()["data"], AdminSMTPSettings)

    def update(self, options: AdminSMTPSettingsUpdateOptions) -> AdminSMTPSettings:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SMTP_TYPE, "attributes": attrs}}
        r = self.t.request("PATCH", "/api/v2/admin/smtp-settings", json_body=body)
        return _parse_jsonapi(r.json()["data"], AdminSMTPSettings)


# ---------------------------------------------------------------------------
# Admin namespace facade
# ---------------------------------------------------------------------------


class AdminClient:
    """Nested namespace for TFE admin-only services.

    Accessed as ``client.admin.<service>``. The wrapper is a thin
    grouping layer with no behaviour of its own; each attribute is a
    standalone service that holds the shared transport.
    """

    def __init__(self, transport: HTTPTransport) -> None:
        self.saml_settings = _AdminSAMLSettings(transport)
        self.scim_settings = _AdminSCIMSettings(transport)
        self.scim_tokens = _AdminSCIMTokens(transport)
        self.smtp_settings = _AdminSMTPSettings(transport)
