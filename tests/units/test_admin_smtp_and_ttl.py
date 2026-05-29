# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for SMTP admin settings, organisation default settings, and
organisation token-TTL policies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pydantic
import pytest

from pytfe.errors import RequiredFieldMissing
from pytfe.models.admin_identity import (
    AdminSMTPSettingsUpdateOptions,
    SMTPAuthType,
)
from pytfe.models.org_token_ttl_policy import (
    DEFAULT_MAX_TTL_MS,
    OrgTokenTTLPolicyUpdateOptions,
    TokenPolicyType,
    parse_ttl_to_ms,
)
from pytfe.models.organization import (
    OrganizationDefaultSettingsUpdateOptions,
)
from pytfe.resources.admin import _AdminSMTPSettings
from pytfe.resources.org_token_ttl_policy import OrganizationTokenTTLPolicies
from pytfe.resources.organizations import Organizations


def _resp(body: Any) -> Mock:
    r = Mock()
    r.json.return_value = body
    return r


# ---------------------------------------------------------------------------
# SMTP
# ---------------------------------------------------------------------------


def _smtp_envelope(**overrides: Any) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "enabled": True,
        "host": "smtp.example.com",
        "port": 587,
        "sender": "noreply@example.com",
        "auth": "login",
        "username": "smtp-bot",
    }
    attrs.update(overrides)
    return {"data": {"id": "smtp", "type": "smtp-settings", "attributes": attrs}}


class TestAdminSMTP:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = _AdminSMTPSettings(self.transport)

    def test_read_parses_returned_fields(self) -> None:
        self.transport.request.return_value = _resp(_smtp_envelope())
        result = self.service.read()
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/admin/smtp-settings"
        assert result.enabled is True
        assert result.host == "smtp.example.com"
        assert result.port == 587
        assert result.auth == SMTPAuthType.LOGIN
        # The read model deliberately doesn't surface password or
        # test-email-address — those are write-only on the wire.
        assert not hasattr(result, "password")
        assert not hasattr(result, "test_email_address")

    def test_update_emits_only_supplied_fields(self) -> None:
        self.transport.request.return_value = _resp(_smtp_envelope())
        self.service.update(
            AdminSMTPSettingsUpdateOptions(
                enabled=True,
                host="smtp.example.com",
                port=587,
                auth=SMTPAuthType.PLAIN,
                username="bot",
                password="hunter2",
                test_email_address="ops@example.com",
            )
        )
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/admin/smtp-settings"
        assert body["data"]["type"] == "smtp-settings"
        assert body["data"]["attributes"] == {
            "enabled": True,
            "host": "smtp.example.com",
            "port": 587,
            "auth": "plain",
            "username": "bot",
            "password": "hunter2",
            "test-email-address": "ops@example.com",
        }

    def test_update_omits_password_when_not_set(self) -> None:
        # Verify password/test-email-address are NOT sent unless the
        # caller actually supplied them.
        self.transport.request.return_value = _resp(_smtp_envelope())
        self.service.update(AdminSMTPSettingsUpdateOptions(host="smtp.new.example.com"))
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"host": "smtp.new.example.com"}
        assert "password" not in body["data"]["attributes"]
        assert "test-email-address" not in body["data"]["attributes"]

    def test_invalid_auth_at_construction(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            AdminSMTPSettingsUpdateOptions(auth="oauth2")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Organization default settings
# ---------------------------------------------------------------------------


def _org_envelope(
    *,
    org_id: str = "my-org",
    default_execution_mode: str | None = "remote",
    default_agent_pool_id: str | None = None,
) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "name": org_id,
        "default-execution-mode": default_execution_mode,
        "max-ttl-enabled": False,
    }
    relationships: dict[str, Any] = {}
    if default_agent_pool_id is not None:
        relationships["default-agent-pool"] = {
            "data": {"type": "agent-pools", "id": default_agent_pool_id}
        }
    else:
        # API returns the relationship key with data=null when unset.
        relationships["default-agent-pool"] = {"data": None}
    return {
        "data": {
            "id": org_id,
            "type": "organizations",
            "attributes": attrs,
            "relationships": relationships,
        }
    }


class TestOrganizationDefaultSettings:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = Organizations(self.transport)

    def test_read_default_settings_parses_attribute_and_relationship(self) -> None:
        self.transport.request.return_value = _resp(
            _org_envelope(
                default_execution_mode="agent",
                default_agent_pool_id="apool-abc123",
            )
        )
        result = self.service.read_default_settings("my-org")
        method, path = self.transport.request.call_args.args
        assert method == "GET"
        assert path == "/api/v2/organizations/my-org"
        assert result.id == "my-org"
        assert result.default_execution_mode == "agent"
        # Crucially the pool id comes from the relationships block, not
        # from attributes.
        assert result.default_agent_pool_id == "apool-abc123"

    def test_read_default_settings_returns_none_when_relationship_data_null(
        self,
    ) -> None:
        self.transport.request.return_value = _resp(_org_envelope())
        result = self.service.read_default_settings("my-org")
        assert result.default_agent_pool_id is None

    def test_update_default_settings_emits_only_set_fields(self) -> None:
        self.transport.request.return_value = _resp(
            _org_envelope(
                default_execution_mode="agent",
                default_agent_pool_id="apool-abc123",
            )
        )
        self.service.update_default_settings(
            "my-org",
            OrganizationDefaultSettingsUpdateOptions(
                default_execution_mode="agent",
                default_agent_pool_id="apool-abc123",
            ),
        )
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/organizations/my-org"
        assert body["data"]["type"] == "organizations"
        assert body["data"]["attributes"] == {
            "default-execution-mode": "agent",
            "default-agent-pool-id": "apool-abc123",
        }

    def test_update_default_settings_explicit_null_agent_pool(self) -> None:
        # Setting agent pool id to None explicitly sends wire null, which
        # clears any previously-configured pool. The validator does NOT
        # block this combination when mode is being reset to "remote".
        self.transport.request.return_value = _resp(_org_envelope())
        self.service.update_default_settings(
            "my-org",
            OrganizationDefaultSettingsUpdateOptions(
                default_execution_mode="remote",
                default_agent_pool_id=None,
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {
            "default-execution-mode": "remote",
            "default-agent-pool-id": None,
        }

    def test_update_default_settings_validation_rejects_pool_with_non_agent_mode(
        self,
    ) -> None:
        # Cross-field validator: setting a pool id while explicitly
        # asking for remote/local mode is a local error, not a server
        # round trip.
        with pytest.raises(pydantic.ValidationError):
            OrganizationDefaultSettingsUpdateOptions(
                default_execution_mode="remote",
                default_agent_pool_id="apool-abc123",
            )

    def test_update_default_settings_partial_only_mode(self) -> None:
        # Updating only the execution mode (no pool) must not pass a
        # default-agent-pool-id key at all — that's how the omit case
        # signals "leave the server value untouched".
        self.transport.request.return_value = _resp(_org_envelope())
        self.service.update_default_settings(
            "my-org",
            OrganizationDefaultSettingsUpdateOptions(
                default_execution_mode="local"
            ),
        )
        body = self.transport.request.call_args.kwargs["json_body"]
        assert body["data"]["attributes"] == {"default-execution-mode": "local"}
        assert "default-agent-pool-id" not in body["data"]["attributes"]

    def test_reset_default_settings(self) -> None:
        self.transport.request.return_value = _resp(_org_envelope())
        self.service.reset_default_settings("my-org")
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/organizations/my-org"
        # Reset clears the pool with explicit null and sets mode to remote.
        assert body["data"]["attributes"] == {
            "default-execution-mode": "remote",
            "default-agent-pool-id": None,
        }


# ---------------------------------------------------------------------------
# Org options alias fix (regression test)
# ---------------------------------------------------------------------------


class TestOrganizationOptionsAliasFix:
    """Regression coverage for the wire-shape fix on the broader
    OrganizationUpdateOptions: the existing snake_case fields had no
    aliases, so PATCH bodies silently dropped keys like
    default_execution_mode on the server side. The fix adds aliases and
    forces ``by_alias=True`` on dump.
    """

    def test_update_emits_hyphenated_keys(self) -> None:
        from pytfe.models import OrganizationUpdateOptions

        transport = Mock()
        transport.request.return_value = _resp(_org_envelope())
        Organizations(transport).update(
            "my-org",
            OrganizationUpdateOptions(
                default_execution_mode="agent",
                default_agent_pool_id="apool-1",
                max_ttl_enabled=True,
            ),
        )
        body = transport.request.call_args.kwargs["json_body"]
        attrs = body["data"]["attributes"]
        # Wire shape MUST be hyphenated; previously these went out as
        # default_execution_mode and the server ignored them.
        assert "default-execution-mode" in attrs
        assert attrs["default-execution-mode"] == "agent"
        assert "default-agent-pool-id" in attrs
        assert attrs["default-agent-pool-id"] == "apool-1"
        assert "max-ttl-enabled" in attrs
        assert attrs["max-ttl-enabled"] is True
        # Snake_case keys MUST NOT appear (regression guard).
        assert "default_execution_mode" not in attrs
        assert "default_agent_pool_id" not in attrs
        assert "max_ttl_enabled" not in attrs


# ---------------------------------------------------------------------------
# Token TTL policy duration parser
# ---------------------------------------------------------------------------


class TestParseTTLToMs:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("500ms", 500),
            ("1s", 1000),
            ("1m", 60_000),
            ("1h", 3_600_000),
            ("1d", 86_400_000),
            ("1w", 604_800_000),
            ("1mo", 2_592_000_000),  # 30 days
            ("1y", 31_536_000_000),  # 365 days
            ("2y", DEFAULT_MAX_TTL_MS),
            ("30d", 30 * 86_400_000),
            ("  6mo  ", 6 * 2_592_000_000),  # whitespace tolerated
        ],
    )
    def test_valid(self, value: str, expected: int) -> None:
        assert parse_ttl_to_ms(value) == expected

    def test_mo_beats_m_in_suffix_match(self) -> None:
        # Critical: "6mo" must parse as months, NOT as "6m" followed by
        # garbage "o". The regex captures the full alphabetic suffix and
        # the longest-first match table picks "mo" over "m".
        assert parse_ttl_to_ms("6mo") == 6 * 2_592_000_000
        assert parse_ttl_to_ms("6m") == 6 * 60_000

    @pytest.mark.parametrize(
        "value",
        ["", "abc", "1", "y", "1xyz", "-1d", "1.5h", "one year"],
    )
    def test_rejects_garbage(self, value: str) -> None:
        with pytest.raises(ValueError):
            parse_ttl_to_ms(value)


# ---------------------------------------------------------------------------
# OrgTokenTTLPolicyUpdateOptions
# ---------------------------------------------------------------------------


class TestOrgTokenTTLPolicyUpdateOptions:
    def test_payload_uses_underscored_audit_trails_spelling(self) -> None:
        # The crucial spelling distinction: the TTL policy API uses
        # ``audit_trails`` (UNDERSCORE), even though other audit-trail
        # token surfaces use ``audit-trails`` (HYPHEN). Pin this in a
        # test so a future "consistency fix" can't silently break it.
        options = OrgTokenTTLPolicyUpdateOptions(audit_trails=DEFAULT_MAX_TTL_MS)
        payload = options.to_payload()
        assert len(payload) == 1
        assert payload[0]["attributes"]["token-type"] == "audit_trails"

    def test_payload_full_four_token_types(self) -> None:
        options = OrgTokenTTLPolicyUpdateOptions(
            organization=DEFAULT_MAX_TTL_MS,
            team=DEFAULT_MAX_TTL_MS,
            user=DEFAULT_MAX_TTL_MS,
            audit_trails=DEFAULT_MAX_TTL_MS,
        )
        payload = options.to_payload()
        token_types = [item["attributes"]["token-type"] for item in payload]
        assert token_types == ["organization", "team", "user", "audit_trails"]
        for item in payload:
            assert item["type"] == "organization-token-ttl-policies"
            assert item["attributes"]["max-ttl-ms"] == DEFAULT_MAX_TTL_MS

    def test_payload_accepts_duration_strings(self) -> None:
        options = OrgTokenTTLPolicyUpdateOptions(
            organization="2y",
            team="30d",
            user="1h",
        )
        payload = options.to_payload()
        ms_by_type = {
            item["attributes"]["token-type"]: item["attributes"]["max-ttl-ms"]
            for item in payload
        }
        assert ms_by_type == {
            "organization": DEFAULT_MAX_TTL_MS,
            "team": 30 * 86_400_000,
            "user": 3_600_000,
        }

    def test_empty_options_raises_typed_error(self) -> None:
        with pytest.raises(RequiredFieldMissing):
            OrgTokenTTLPolicyUpdateOptions().to_payload()

    def test_mixed_int_and_string_values(self) -> None:
        options = OrgTokenTTLPolicyUpdateOptions(
            organization="1y",
            team=3600_000,
        )
        payload = options.to_payload()
        ms_by_type = {
            item["attributes"]["token-type"]: item["attributes"]["max-ttl-ms"]
            for item in payload
        }
        assert ms_by_type["organization"] == 31_536_000_000
        assert ms_by_type["team"] == 3_600_000


# ---------------------------------------------------------------------------
# OrganizationTokenTTLPolicies resource
# ---------------------------------------------------------------------------


def _ttl_item(token_type: str, max_ttl_ms: int = DEFAULT_MAX_TTL_MS) -> dict[str, Any]:
    return {
        "id": f"ottp-{token_type}",
        "type": "organization-token-ttl-policies",
        "attributes": {"token-type": token_type, "max-ttl-ms": max_ttl_ms},
    }


class TestOrganizationTokenTTLPoliciesResource:
    def setup_method(self) -> None:
        self.transport = Mock()
        self.service = OrganizationTokenTTLPolicies(self.transport)

    def test_list_url_and_no_pagination(self) -> None:
        self.transport.request.return_value = _resp(
            {
                "data": [
                    _ttl_item("organization"),
                    _ttl_item("team"),
                    _ttl_item("user"),
                    _ttl_item("audit_trails"),
                ]
            }
        )
        result = list(self.service.list("my-org"))
        method, path = self.transport.request.call_args.args
        kwargs = self.transport.request.call_args.kwargs
        assert method == "GET"
        assert path == "/api/v2/organizations/my-org/token-ttl-policies"
        # Endpoint is not paginated — must not inject page[] params.
        assert "params" not in kwargs or not kwargs.get("params")
        assert [p.token_type for p in result] == [
            TokenPolicyType.ORGANIZATION,
            TokenPolicyType.TEAM,
            TokenPolicyType.USER,
            TokenPolicyType.AUDIT_TRAILS,
        ]

    def test_update_url_and_payload(self) -> None:
        self.transport.request.return_value = _resp(
            {"data": [_ttl_item("team", 3_600_000)]}
        )
        self.service.update(
            "my-org",
            OrgTokenTTLPolicyUpdateOptions(team="1h"),
        )
        method, path = self.transport.request.call_args.args
        body = self.transport.request.call_args.kwargs["json_body"]
        assert method == "PATCH"
        assert path == "/api/v2/organizations/my-org/token-ttl-policies"
        assert body == {
            "data": [
                {
                    "type": "organization-token-ttl-policies",
                    "attributes": {"token-type": "team", "max-ttl-ms": 3_600_000},
                }
            ]
        }

    def test_reset_to_defaults_sends_all_four(self) -> None:
        self.transport.request.return_value = _resp(
            {
                "data": [
                    _ttl_item("organization"),
                    _ttl_item("team"),
                    _ttl_item("user"),
                    _ttl_item("audit_trails"),
                ]
            }
        )
        self.service.reset_to_defaults("my-org")
        body = self.transport.request.call_args.kwargs["json_body"]
        token_types = [item["attributes"]["token-type"] for item in body["data"]]
        assert token_types == ["organization", "team", "user", "audit_trails"]
        for item in body["data"]:
            assert item["attributes"]["max-ttl-ms"] == DEFAULT_MAX_TTL_MS

    def test_invalid_org_rejected_locally_on_list(self) -> None:
        with pytest.raises(ValueError):
            list(self.service.list(""))

    def test_invalid_org_rejected_locally_on_update(self) -> None:
        with pytest.raises(ValueError):
            self.service.update(
                "",
                OrgTokenTTLPolicyUpdateOptions(team=3_600_000),
            )

    def test_empty_update_raises_before_request(self) -> None:
        # No HTTP call should happen — the typed error fires at
        # payload-build time.
        self.transport.request.return_value = _resp({"data": []})
        with pytest.raises(RequiredFieldMissing):
            self.service.update("my-org", OrgTokenTTLPolicyUpdateOptions())
        assert self.transport.request.call_count == 0
