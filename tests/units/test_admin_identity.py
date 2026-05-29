# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the TFE admin identity resources (SAML, SCIM settings,
SCIM tokens) and the GitHub App installation discovery resource.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest

from pytfe.errors import (
    InvalidGitHubAppInstallationIDError,
    InvalidSCIMTokenIDError,
    RequiredSCIMTokenDescriptionError,
)
from pytfe.models.admin_identity import (
    AdminSAMLSettingsUpdateOptions,
    AdminSCIMSettingsUpdateOptions,
    AdminSCIMTokenCreateOptions,
    SAMLProviderType,
    SAMLSignatureMethod,
)
from pytfe.models.github_app_installation import (
    GitHubAppInstallationListOptions,
)
from pytfe.resources.admin import (
    AdminClient,
    _AdminSAMLSettings,
    _AdminSCIMSettings,
    _AdminSCIMTokens,
)
from pytfe.resources.github_app_installation import GitHubAppInstallations


def _resp(body: Any) -> Mock:
    r = Mock()
    r.json.return_value = body
    return r


# ---------------------------------------------------------------------------
# SAML settings
# ---------------------------------------------------------------------------


def _saml_envelope(**overrides: Any) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "enabled": True,
        "debug": False,
        "idp-cert": "cert-blob",
        "old-idp-cert": None,
        "slo-endpoint-url": "https://idp.example.com/slo",
        "sso-endpoint-url": "https://idp.example.com/sso",
        "attr-username": "Username",
        "attr-groups": "MemberOf",
        "attr-site-admin": "SiteAdmin",
        "site-admin-role": "site-admins",
        "sso-api-token-session-timeout": 1209600,
        "acs-consumer-url": "https://tfe.example.com/users/saml/auth",
        "metadata-url": "https://tfe.example.com/users/saml/metadata",
        "authn-requests-signed": False,
        "want-assertions-signed": False,
        "team-management-enabled": False,
        "signature-signing-method": "SHA256",
        "signature-digest-method": "SHA256",
        "provider-type": "saml",
        "certificate": None,
    }
    attrs.update(overrides)
    return {
        "data": {"id": "saml-settings", "type": "saml-settings", "attributes": attrs}
    }


class TestSAMLSettings:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = _AdminSAMLSettings(self.transport)

    def test_read(self) -> None:
        self.transport.request.return_value = _resp(_saml_envelope())
        result = self.service.read()
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/admin/saml-settings"
        assert result.enabled is True
        assert result.idp_cert == "cert-blob"
        assert result.sso_api_token_session_timeout == 1209600
        assert result.provider_type == SAMLProviderType.SAML
        assert result.signature_signing_method == SAMLSignatureMethod.SHA256

    def test_update_emits_only_supplied_fields_with_wire_aliases(self) -> None:
        self.transport.request.return_value = _resp(_saml_envelope())
        self.service.update(
            AdminSAMLSettingsUpdateOptions(
                enabled=True,
                idp_cert="new-cert",
                provider_type=SAMLProviderType.OKTA,
                authn_requests_signed=True,
                signature_signing_method=SAMLSignatureMethod.SHA256,
            )
        )
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/admin/saml-settings"
        assert body["data"]["type"] == "saml-settings"
        assert body["data"]["attributes"] == {
            "enabled": True,
            "idp-cert": "new-cert",
            "provider-type": "okta",
            "authn-requests-signed": True,
            "signature-signing-method": "SHA256",
        }

    def test_update_omits_unset_fields(self) -> None:
        self.transport.request.return_value = _resp(_saml_envelope())
        self.service.update(AdminSAMLSettingsUpdateOptions(debug=True))
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"debug": True}

    def test_update_with_private_key(self) -> None:
        # Private key is sensitive but must still be sent on the wire when
        # the caller supplies it. The redaction is at the LOG layer, not
        # the request-body layer.
        self.transport.request.return_value = _resp(_saml_envelope())
        self.service.update(
            AdminSAMLSettingsUpdateOptions(private_key="-----BEGIN PRIVATE-----")
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"private-key": "-----BEGIN PRIVATE-----"}

    def test_revoke_idp_cert(self) -> None:
        self.transport.request.return_value = _resp(
            _saml_envelope(**{"old-idp-cert": None})
        )
        self.service.revoke_idp_cert()
        method, path = self.transport.request.call_args.args
        assert method == "POST"
        assert path == "/api/v2/admin/saml-settings/actions/revoke-old-certificate"

    def test_invalid_provider_type_at_construction(self) -> None:
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            AdminSAMLSettingsUpdateOptions(provider_type="garbage")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SCIM settings
# ---------------------------------------------------------------------------


class TestSCIMSettings:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = _AdminSCIMSettings(self.transport)

    def _envelope(self, **overrides: Any) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "enabled": True,
            "paused": False,
            "site-admin-group-scim-id": "scim-group-1",
            "site-admin-group-display-name": "Site Admins",
        }
        attrs.update(overrides)
        return {
            "data": {
                "id": "scim-settings",
                "type": "scim-settings",
                "attributes": attrs,
            }
        }

    def test_read(self) -> None:
        self.transport.request.return_value = _resp(self._envelope())
        result = self.service.read()
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/admin/scim-settings"
        assert result.enabled is True
        assert result.site_admin_group_scim_id == "scim-group-1"
        assert result.site_admin_group_display_name == "Site Admins"

    def test_update_paused_only(self) -> None:
        self.transport.request.return_value = _resp(self._envelope())
        self.service.update(AdminSCIMSettingsUpdateOptions(paused=True))
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/admin/scim-settings"
        assert body["data"]["type"] == "scim-settings"
        assert body["data"]["attributes"] == {"paused": True}

    def test_update_omits_unset_site_admin_group(self) -> None:
        # Unset field MUST NOT appear in the payload — that's how the
        # caller signals "leave the server value untouched".
        self.transport.request.return_value = _resp(self._envelope())
        self.service.update(AdminSCIMSettingsUpdateOptions(paused=False))
        body = self.transport.request.call_args.kwargs["json_body"]
        assert "site-admin-group-scim-id" not in body["data"]["attributes"]
        assert body["data"]["attributes"] == {"paused": False}

    def test_update_explicit_null_site_admin_group(self) -> None:
        # Explicitly passing None MUST emit JSON null on the wire — that's
        # how the caller signals "unlink the SCIM group from site-admin".
        # This is the crucial difference vs the omission case above.
        self.transport.request.return_value = _resp(self._envelope())
        self.service.update(
            AdminSCIMSettingsUpdateOptions(site_admin_group_scim_id=None)
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"site-admin-group-scim-id": None}

    def test_update_set_site_admin_group_to_value(self) -> None:
        self.transport.request.return_value = _resp(self._envelope())
        self.service.update(
            AdminSCIMSettingsUpdateOptions(
                paused=True, site_admin_group_scim_id="new-group-id"
            )
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {
            "paused": True,
            "site-admin-group-scim-id": "new-group-id",
        }

    def test_delete(self) -> None:
        self.transport.request.return_value = _resp({})
        self.service.delete()
        method, path = self.transport.request.call_args.args
        assert method == "DELETE"
        assert path == "/api/v2/admin/scim-settings"


# ---------------------------------------------------------------------------
# SCIM tokens
# ---------------------------------------------------------------------------


def _token_envelope(
    *,
    token_id: str = "at-1",
    description: str = "automation",
    token: str | None = None,
) -> dict[str, Any]:
    return {
        "data": {
            "id": token_id,
            "type": "authentication-tokens",
            "attributes": {
                "description": description,
                "token": token,
                "created-at": "2026-05-29T00:00:00Z",
                "expired-at": None,
                "last-used-at": None,
            },
        }
    }


class TestSCIMTokens:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = _AdminSCIMTokens(self.transport)

    def test_list_without_pagination(self) -> None:
        # The endpoint isn't documented as paginated, so the resource
        # MUST NOT inject ``page[...]`` query params; a single GET is
        # all that's required.
        self.transport.request.return_value = _resp(
            {
                "data": [
                    _token_envelope()["data"],
                    _token_envelope(token_id="at-2")["data"],
                ]
            }
        )
        result = list(self.service.list())
        method, path = self.transport.request.call_args.args
        kwargs = self.transport.request.call_args.kwargs
        assert method == "GET"
        assert path == "/api/v2/admin/scim-tokens"
        assert "params" not in kwargs or not kwargs.get("params")
        assert [t.id for t in result] == ["at-1", "at-2"]
        # token field is always None on list (per the API contract).
        assert all(t.token is None for t in result)

    def test_create_returns_token_value(self) -> None:
        self.transport.request.return_value = _resp(
            _token_envelope(token="PLAINTEXT-ONLY-RETURNED-NOW")
        )
        result = self.service.create(AdminSCIMTokenCreateOptions(description="ci-bot"))
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "POST"
        assert path == "/api/v2/admin/scim-tokens"
        assert body["data"]["type"] == "authentication-tokens"
        assert body["data"]["attributes"] == {"description": "ci-bot"}
        assert result.token == "PLAINTEXT-ONLY-RETURNED-NOW"

    def test_create_requires_non_empty_description(self) -> None:
        # Pydantic rejects construction with an empty string via the
        # Field(...) requirement? Actually Field(...) only enforces
        # presence; empty string passes. The resource layer enforces
        # non-empty via valid_string and raises a typed error.
        with pytest.raises(RequiredSCIMTokenDescriptionError):
            self.service.create(AdminSCIMTokenCreateOptions(description=""))

    def test_read_uses_admin_path(self) -> None:
        self.transport.request.return_value = _resp(_token_envelope())
        self.service.read("at-1")
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/admin/scim-tokens/at-1"

    def test_delete_uses_admin_path(self) -> None:
        # Crucial wire-shape test: the upstream docs specify
        # /api/v2/admin/scim-tokens/{id} for DELETE, NOT the generic
        # /api/v2/authentication-tokens/{id} path. Regression-protect that.
        self.transport.request.return_value = _resp({})
        self.service.delete("at-1")
        method, path = self.transport.request.call_args.args
        assert method == "DELETE"
        assert path == "/api/v2/admin/scim-tokens/at-1"

    def test_invalid_token_id_on_read(self) -> None:
        with pytest.raises(InvalidSCIMTokenIDError):
            self.service.read("")

    def test_invalid_token_id_on_delete(self) -> None:
        with pytest.raises(InvalidSCIMTokenIDError):
            self.service.delete("")


# ---------------------------------------------------------------------------
# AdminClient namespace facade
# ---------------------------------------------------------------------------


class TestAdminClient:
    def test_exposes_three_nested_services(self) -> None:
        admin = AdminClient(Mock())
        assert isinstance(admin.saml_settings, _AdminSAMLSettings)
        assert isinstance(admin.scim_settings, _AdminSCIMSettings)
        assert isinstance(admin.scim_tokens, _AdminSCIMTokens)


# ---------------------------------------------------------------------------
# GitHub App installations
# ---------------------------------------------------------------------------


def _installation_envelope(
    *,
    install_id: str = "ghain-1",
    name: str = "my-org",
    installation_id: int = 54810170,
) -> dict[str, Any]:
    return {
        "data": {
            "id": install_id,
            "type": "github-app-installations",
            "attributes": {
                "name": name,
                "installation-id": installation_id,
                "icon-url": "https://github.com/icon.png",
                "installation-type": "Organization",
                "installation-url": f"https://github.com/{name}",
            },
        }
    }


class TestGitHubAppInstallations:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = GitHubAppInstallations(self.transport)

    def test_list_no_filters(self) -> None:
        self.transport.request.return_value = _resp(
            {
                "data": [
                    _installation_envelope()["data"],
                    _installation_envelope(install_id="ghain-2", name="other-org")[
                        "data"
                    ],
                ]
            }
        )
        result = list(self.service.list())
        method, path = self.transport.request.call_args.args
        kwargs = self.transport.request.call_args.kwargs
        assert method == "GET"
        assert path == "/api/v2/github-app/installations"
        # No filter params when none supplied.
        assert kwargs.get("params") is None
        assert [i.id for i in result] == ["ghain-1", "ghain-2"]
        assert result[0].installation_id == 54810170
        assert result[0].installation_type == "Organization"

    def test_list_with_name_filter(self) -> None:
        self.transport.request.return_value = _resp({"data": []})
        list(self.service.list(GitHubAppInstallationListOptions(name="my-org")))
        params = self.transport.request.call_args.kwargs["params"]
        assert params == {"filter[name]": "my-org"}

    def test_list_with_installation_id_filter(self) -> None:
        self.transport.request.return_value = _resp({"data": []})
        list(
            self.service.list(
                GitHubAppInstallationListOptions(installation_id=54810170)
            )
        )
        params = self.transport.request.call_args.kwargs["params"]
        assert params == {"filter[installation_id]": 54810170}

    def test_read_uses_singular_path_segment(self) -> None:
        # Singular `installation` (NOT plural `installations`) — this is
        # the documented path shape. Regression-protect it.
        self.transport.request.return_value = _resp(_installation_envelope())
        self.service.read("ghain-1")
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/github-app/installation/ghain-1"

    def test_read_parses_all_attributes(self) -> None:
        self.transport.request.return_value = _resp(_installation_envelope())
        result = self.service.read("ghain-1")
        assert result.id == "ghain-1"
        assert result.name == "my-org"
        assert result.installation_id == 54810170
        assert result.icon_url == "https://github.com/icon.png"
        assert result.installation_type == "Organization"
        assert result.installation_url == "https://github.com/my-org"

    def test_invalid_id_on_read(self) -> None:
        with pytest.raises(InvalidGitHubAppInstallationIDError):
            self.service.read("")


# ---------------------------------------------------------------------------
# Logging redaction covers SAML private-key
# ---------------------------------------------------------------------------


class TestSAMLPrivateKeyRedaction:
    def test_private_key_key_is_in_sensitive_set(self) -> None:
        # Direct membership check guards against the wire-format key
        # ("private-key" with hyphen) silently dropping out of the set.
        from pytfe._logging import _SENSITIVE_JSON_KEYS

        assert "private-key" in _SENSITIVE_JSON_KEYS
        assert "private_key" in _SENSITIVE_JSON_KEYS

    def test_certificate_fields_are_not_redacted(self) -> None:
        # X.509 certs are public material by design; redacting them hurts
        # debugging without protecting anything. This pins that decision.
        from pytfe._logging import _SENSITIVE_JSON_KEYS

        assert "idp-cert" not in _SENSITIVE_JSON_KEYS
        assert "certificate" not in _SENSITIVE_JSON_KEYS
        assert "old-idp-cert" not in _SENSITIVE_JSON_KEYS
