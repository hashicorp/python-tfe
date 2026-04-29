# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import time
from collections.abc import Iterator

from ..errors import (
    InvalidPolicyCheckIDError,
    InvalidRunIDError,
)
from ..models.policy_check import (
    PolicyCheck,
    PolicyCheckListOptions,
    PolicyStatus,
)
from ..utils import valid_string_id
from ._base import _Service


class PolicyChecks(_Service):
    """
    PolicyChecks describes all the policy check related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
    """

    def list(
        self, run_id: str, options: PolicyCheckListOptions | None = None
    ) -> Iterator[PolicyCheck]:
        """List all policy checks of the given run."""
        if not valid_string_id(run_id):
            raise InvalidRunIDError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )
        path = f"/api/v2/runs/{run_id}/policy-checks"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            attrs["run"] = item.get("relationships", {}).get("run", {}).get("data")
            yield PolicyCheck.model_validate(attrs)

    def read(self, policy_check_id: str) -> PolicyCheck:
        """Read a policy check by its ID."""
        if not valid_string_id(policy_check_id):
            raise InvalidPolicyCheckIDError()
        r = self.t.request(
            "GET",
            f"/api/v2/policy-checks/{policy_check_id}",
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["run"] = d.get("relationships", {}).get("run", {}).get("data")
        return PolicyCheck.model_validate(attrs)

    def override(self, policy_check_id: str) -> PolicyCheck:
        """Override a soft-mandatory or warning policy."""
        if not valid_string_id(policy_check_id):
            raise InvalidPolicyCheckIDError()
        r = self.t.request(
            "POST",
            f"/api/v2/policy-checks/{policy_check_id}/actions/override",
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["run"] = d.get("relationships", {}).get("run", {}).get("data")
        return PolicyCheck.model_validate(attrs)

    def logs(self, policy_check_id: str) -> str:
        """Logs retrieves the logs of a policy check."""
        if not valid_string_id(policy_check_id):
            raise InvalidPolicyCheckIDError()

        # Loop until the policy check is finished running.
        # The policy check logs are not streamed and so only available
        # once the check is finished.
        while True:
            pc = self.read(policy_check_id)

            # Continue polling if the policy check is still pending or queued
            if pc.status in (PolicyStatus.POLICY_PENDING, PolicyStatus.POLICY_QUEUED):
                time.sleep(0.5)  # 500ms wait
                continue

            # Policy check is finished, get the logs
            r = self.t.request(
                "GET",
                f"/api/v2/policy-checks/{policy_check_id}/output",
            )
            return r.text
