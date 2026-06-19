# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import time
from collections.abc import Iterator

from .._jsonapi import attach_jsonapi
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
        """List policy checks for the given run.

        Args:
            run_id: The run ID (e.g. ``"run-veDoQbv6xh6TbnJD"``).
            options: Optional includes and pagination, as a
                :class:`PolicyCheckListOptions`.

        Returns:
            A single-use ``Iterator[PolicyCheck]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidRunIDError: If ``run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for check in client.policy_checks.list("run-veDoQbv6xh6TbnJD"):
            ...     print(check.id, check.status)
        """
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
            yield attach_jsonapi(PolicyCheck.model_validate(attrs), item)

    def read(self, policy_check_id: str) -> PolicyCheck:
        """Read a policy check by its ID.

        Args:
            policy_check_id: The policy check ID
                (e.g. ``"polchk-9VYRc9bpfJEsnwum"``).

        Returns:
            The :class:`PolicyCheck`.

        Raises:
            InvalidPolicyCheckIDError: If ``policy_check_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> check = client.policy_checks.read("polchk-9VYRc9bpfJEsnwum")
            >>> print(check.status)
        """
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
        return attach_jsonapi(PolicyCheck.model_validate(attrs), d)

    def override(self, policy_check_id: str) -> PolicyCheck:
        """Override a soft-mandatory or warning policy check.

        Args:
            policy_check_id: The policy check ID
                (e.g. ``"polchk-EasPB4Srx5NAiWAU"``).

        Returns:
            The :class:`PolicyCheck`.

        Raises:
            InvalidPolicyCheckIDError: If ``policy_check_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> check = client.policy_checks.override("polchk-EasPB4Srx5NAiWAU")
            >>> print(check.status)
        """
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
        return attach_jsonapi(PolicyCheck.model_validate(attrs), d)

    def logs(self, policy_check_id: str) -> str:
        """Read the logs for a completed policy check.

        Args:
            policy_check_id: The policy check ID
                (e.g. ``"polchk-9VYRc9bpfJEsnwum"``).

        Returns:
            The policy check logs as a string.

        Raises:
            InvalidPolicyCheckIDError: If ``policy_check_id`` is not a valid
                resource ID.
            TFEError: If the API request fails.

        Example:
            >>> logs = client.policy_checks.logs("polchk-9VYRc9bpfJEsnwum")
            >>> print(logs)
        """
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
