# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    ERR_INVALID_NAME,
    ERR_INVALID_ORG,
    ERR_REQUIRED_EMAIL,
    ERR_REQUIRED_NAME,
)
from ..models.data_retention_policy import (
    DataRetentionPolicy,
    DataRetentionPolicyChoice,
    DataRetentionPolicyDeleteOlder,
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDelete,
    DataRetentionPolicyDontDeleteSetOptions,
    DataRetentionPolicySetOptions,
)
from ..models.organization import (
    Capacity,
    Entitlements,
    Organization,
    OrganizationCreateOptions,
    OrganizationDefaultSettings,
    OrganizationDefaultSettingsUpdateOptions,
    OrganizationReadOptions,
    OrganizationUpdateOptions,
    ReadRunQueueOptions,
    RunQueue,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def _parse_org(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> Organization:
    """Parse a JSON:API ``data`` block into an :class:`Organization`.

    Handles two things the legacy ``Organization(**attrs)`` shortcut
    didn't:

    - Hyphenated attribute names like ``default-execution-mode`` are
      accepted via the model's aliases (``populate_by_name=True``).
    - The ``default-agent-pool`` relationship — which sits OUTSIDE
      ``attributes`` in the JSON:API envelope — is lifted into the
      ``default_agent_pool`` field as ``{"id": "<pool-id>"}`` so callers
      can do ``org.default_agent_pool["id"]`` without traversing
      relationships themselves.
    """
    attrs = data.get("attributes") or {}
    org_data: dict[str, Any] = dict(attrs)
    org_data["id"] = _safe_str(data.get("id"))

    relationships = data.get("relationships") or {}
    pool_rel = (relationships.get("default-agent-pool") or {}).get("data")
    if pool_rel and pool_rel.get("id"):
        org_data["default_agent_pool"] = {"id": pool_rel["id"]}

    return attach_jsonapi(Organization.model_validate(org_data), data, included)


class Organizations(_Service):
    def delete(self, name: str) -> None:
        if not valid_string_id(name):
            raise ValueError(ERR_INVALID_ORG)
        self.t.request("DELETE", f"/api/v2/organizations/{name}")
        return None

    def update(self, name: str, options: OrganizationUpdateOptions) -> Organization:
        if not valid_string_id(name):
            raise ValueError(ERR_INVALID_ORG)
        body = {
            "data": {
                "type": "organizations",
                # by_alias=True is required so fields with hyphenated
                # JSON:API aliases (e.g. ``default-execution-mode``,
                # ``default-agent-pool-id``, ``max-ttl-enabled``) reach
                # the server with their wire names instead of being
                # silently dropped as unknown snake_case keys.
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                ),
            }
        }
        r = self.t.request("PATCH", f"/api/v2/organizations/{name}", json_body=body)
        return _parse_org(r.json()["data"])

    def create(self, options: OrganizationCreateOptions) -> Organization:
        Organizations.validate(options)
        body = {
            "data": {
                "type": "organizations",
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, mode="json"
                ),
            }
        }
        r = self.t.request("POST", "/api/v2/organizations", json_body=body)
        return _parse_org(r.json()["data"])

    def list(self) -> Iterator[Organization]:
        for item in self._list("/api/v2/organizations"):
            yield _parse_org(item)

    def read(
        self, name: str, options: OrganizationReadOptions | None = None
    ) -> Organization:
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([opt.value for opt in options.include])
        r = self.t.request("GET", f"/api/v2/organizations/{name}", params=params)
        payload = r.json()
        return _parse_org(payload["data"], payload.get("included"))

    # ---- Organization default settings (provider parity) -----------------
    #
    # All three methods below hit the regular org endpoint —
    # ``GET/PATCH /api/v2/organizations/{name}`` — but expose a narrower
    # surface focused on ``default-execution-mode`` and the
    # ``default-agent-pool`` relationship, which is how the Terraform
    # provider's ``tfe_organization_default_settings`` resource models
    # the same state.

    def _parse_default_settings(
        self, data: dict[str, Any]
    ) -> OrganizationDefaultSettings:
        attrs = data.get("attributes") or {}
        relationships = data.get("relationships") or {}
        pool_rel = (relationships.get("default-agent-pool") or {}).get("data")
        pool_id = pool_rel.get("id") if pool_rel else None
        return OrganizationDefaultSettings.model_validate(
            {
                "id": data.get("id"),
                "default-execution-mode": attrs.get("default-execution-mode"),
                "default_agent_pool_id": pool_id,
            }
        )

    def read_default_settings(self, organization: str) -> OrganizationDefaultSettings:
        """Read the org's default execution mode and default agent pool."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        r = self.t.request("GET", f"/api/v2/organizations/{organization}")
        return self._parse_default_settings(r.json()["data"])

    def update_default_settings(
        self,
        organization: str,
        options: OrganizationDefaultSettingsUpdateOptions,
    ) -> OrganizationDefaultSettings:
        """Patch only the default-settings fields on the org. Cross-field
        validation (``default_agent_pool_id`` requires ``agent`` execution
        mode) is enforced at options construction time, not here.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        body = {
            "data": {
                "type": "organizations",
                "attributes": options.to_payload(),
            }
        }
        r = self.t.request(
            "PATCH", f"/api/v2/organizations/{organization}", json_body=body
        )
        return self._parse_default_settings(r.json()["data"])

    def reset_default_settings(self, organization: str) -> OrganizationDefaultSettings:
        """Reset to ``remote`` execution and clear any default agent pool.

        Convenience over :meth:`update_default_settings` — equivalent to
        calling it with ``default_execution_mode="remote"`` and
        ``default_agent_pool_id=None`` explicitly (the latter is sent as
        wire ``null`` so any existing pool is unlinked).
        """
        # mypy reads the Pydantic-synthesised __init__ as accepting only
        # the wire-aliased kwargs (``default-execution-mode``) and not
        # the Python field names. The runtime behaviour with
        # ``populate_by_name=True`` accepts both; suppress here.
        return self.update_default_settings(
            organization,
            OrganizationDefaultSettingsUpdateOptions(  # type: ignore[call-arg]
                default_execution_mode="remote",
                default_agent_pool_id=None,
            ),
        )

    @staticmethod
    def validate(opts: OrganizationCreateOptions) -> None:
        """Validate organization creation options."""
        if not valid_string(opts.name):
            raise ValueError(ERR_REQUIRED_NAME)
        if not valid_string_id(opts.name):
            raise ValueError(ERR_INVALID_NAME)
        if not valid_string(opts.email):
            raise ValueError(ERR_REQUIRED_EMAIL)

    def read_capacity(self, organization: str) -> Capacity:
        """Read the currently used capacity of an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        r = self.t.request("GET", f"/api/v2/organizations/{organization}/capacity")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        c = Capacity(
            organization=_safe_str(d.get("id")),
            pending=attr.get("pending", 0),
            running=attr.get("running", 0),
        )
        return c

    def read_entitlements(self, organization: str) -> Entitlements:
        """Read the entitlements of an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        r = self.t.request(
            "GET", f"/api/v2/organizations/{organization}/entitlement-set"
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        e = Entitlements(
            id=_safe_str(d.get("id")),
            agents=attr.get("agents"),
            audit_logging=attr.get("audit-logging"),
            cost_estimation=attr.get("cost-estimation"),
            global_run_tasks=attr.get("global-run-tasks"),
            operations=attr.get("operations"),
            private_module_registry=attr.get("private-module-registry"),
            private_run_tasks=attr.get("private-run-tasks"),
            run_tasks=attr.get("run-tasks"),
            sso=attr.get("sso"),
            sentinel=attr.get("sentinel"),
            state_storage=attr.get("state-storage"),
            teams=attr.get("teams"),
            vcs_integrations=attr.get("vcs-integrations"),
            waypoint_actions=attr.get("waypoint-actions"),
            waypoint_templates_and_addons=attr.get("waypoint-templates-and-addons"),
        )
        return e

    def read_run_queue(
        self, organization: str, options: ReadRunQueueOptions
    ) -> RunQueue:
        """Read the current run queue of an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        params = {}
        if options.page_number is not None:
            params["page[number]"] = options.page_number
        if options.page_size is not None:
            params["page[size]"] = options.page_size

        r = self.t.request(
            "GET", f"/api/v2/organizations/{organization}/runs/queue", params=params
        )
        data = r.json()

        from ..models.organization import Pagination, Run, RunStatus

        runs = []
        for item in data.get("data", []):
            attr = item.get("attributes", {}) or {}
            run_id = _safe_str(item.get("id"))
            status_str = attr.get("status", "pending")

            # Map string status to RunStatus enum, fallback to pending
            try:
                status = RunStatus(status_str)
            except ValueError:
                status = RunStatus.PLANNING  # Default fallback

            runs.append(Run(id=run_id, status=status))

        # Extract pagination info
        pagination = None
        meta = data.get("meta", {})
        if meta:
            pagination = Pagination(
                current_page=meta.get("pagination", {}).get("current-page", 1),
                total_count=meta.get("pagination", {}).get("total-count", 0),
            )

        rq = RunQueue(pagination=pagination, items=runs)
        return rq

    def read_data_retention_policy_choice(
        self, organization: str
    ) -> DataRetentionPolicyChoice | None:
        """Read an organization's data retention policy choice (polymorphic).

        Note: This functionality is only available in Terraform Enterprise.
        Returns None if no data retention policy is configured.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        # First read the organization to see if it has a data retention policy
        try:
            org = self.read(organization)
            if (
                not hasattr(org, "data_retention_policy_choice")
                or org.data_retention_policy_choice is None
            ):
                return None

            # If there's a policy choice, fetch the full details
            r = self.t.request(
                "GET",
                f"/api/v2/organizations/{organization}/relationships/data-retention-policy",
            )
            d = r.json()["data"]

            choice = DataRetentionPolicyChoice()

            # Determine type and populate appropriate field
            policy_type = d.get("type", "")
            if policy_type == "data-retention-policy-delete-olders":
                attr = d.get("attributes", {}) or {}
                choice.data_retention_policy_delete_older = (
                    DataRetentionPolicyDeleteOlder(
                        id=_safe_str(d.get("id")),
                        delete_older_than_n_days=attr.get(
                            "delete-older-than-n-days", 0
                        ),
                    )
                )
            elif policy_type == "data-retention-policy-dont-deletes":
                choice.data_retention_policy_dont_delete = (
                    DataRetentionPolicyDontDelete(id=_safe_str(d.get("id")))
                )
            elif policy_type == "data-retention-policies":
                # Legacy type for TFE v202311-1 and v202312-1
                attr = d.get("attributes", {}) or {}
                choice.data_retention_policy = DataRetentionPolicy(
                    id=_safe_str(d.get("id")),
                    delete_older_than_n_days=attr.get("delete-older-than-n-days", 0),
                )

            return choice if choice.is_populated() else None

        except Exception:
            # If organization read fails or policy doesn't exist, return None
            return None

    def set_data_retention_policy(
        self, organization: str, options: DataRetentionPolicySetOptions
    ) -> DataRetentionPolicy:
        """Set an organization's data retention policy.

        Deprecated: Use set_data_retention_policy_delete_older instead.
        Note: This functionality is only available in Terraform Enterprise versions v202311-1 and v202312-1.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        body = {
            "data": {
                "type": "data-retention-policies",
                "attributes": {
                    "delete-older-than-n-days": options.delete_older_than_n_days
                },
            }
        }

        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/relationships/data-retention-policy",
            json_body=body,
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        drp = DataRetentionPolicy(
            id=_safe_str(d.get("id")),
            delete_older_than_n_days=attr.get("delete-older-than-n-days", 0),
        )
        return drp

    def set_data_retention_policy_delete_older(
        self, organization: str, options: DataRetentionPolicyDeleteOlderSetOptions
    ) -> DataRetentionPolicyDeleteOlder:
        """Set an organization's data retention policy to delete data older than a certain number of days.

        Note: This functionality is only available in Terraform Enterprise.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        body = {
            "data": {
                "type": "data-retention-policy-delete-olders",
                "attributes": {
                    "delete-older-than-n-days": options.delete_older_than_n_days
                },
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/relationships/data-retention-policy",
            json_body=body,
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        drp = DataRetentionPolicyDeleteOlder(
            id=_safe_str(d.get("id")),
            delete_older_than_n_days=attr.get("delete-older-than-n-days", 0),
        )
        return drp

    def set_data_retention_policy_dont_delete(
        self, organization: str, options: DataRetentionPolicyDontDeleteSetOptions
    ) -> DataRetentionPolicyDontDelete:
        """Set an organization's data retention policy to explicitly not delete data.

        Note: This functionality is only available in Terraform Enterprise.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        body = {
            "data": {"type": "data-retention-policy-dont-deletes", "attributes": {}}
        }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/relationships/data-retention-policy",
            json_body=body,
        )
        d = r.json()["data"]

        drp = DataRetentionPolicyDontDelete(id=_safe_str(d.get("id")))
        return drp

    def delete_data_retention_policy(self, organization: str) -> None:
        """Delete an organization's data retention policy.

        Note: This functionality is only available in Terraform Enterprise.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        self.t.request(
            "DELETE",
            f"/api/v2/organizations/{organization}/relationships/data-retention-policy",
        )
        return None
