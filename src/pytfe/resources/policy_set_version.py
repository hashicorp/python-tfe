from __future__ import annotations

from ..errors import (
    InvalidPolicySetIDError,
)
from ..models.policy_set_version import (
    PolicySetVersion,
)
from ..utils import pack_contents, valid_string_id
from ._base import _Service


class PolicySetVersions(_Service):
    """
    PolicySetVersions describes all the Policy Set Version related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets#create-a-policy-set-version
    """

    def create(self, policy_set_id: str) -> PolicySetVersion:
        """Create is used to create a new Policy Set Version."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        r = self.t.request(
            "POST",
            f"/api/v2/policy-sets/{policy_set_id}/versions",
        )
        jd = r.json()
        attrs = jd.get("data", {}).get("attributes", {})
        attrs["id"] = jd.get("data", {}).get("id")
        attrs["links"] = jd.get("data", {}).get("links", {})
        attrs["policy-set"] = (
            jd.get("data", {})
            .get("relationships", {})
            .get("policy-set", {})
            .get("data", {})
        )
        return PolicySetVersion.model_validate(attrs)

    def read(self, policy_set_version_id: str) -> PolicySetVersion:
        """Read is used to read a Policy Set Version by its ID."""
        if not valid_string_id(policy_set_version_id):
            raise InvalidPolicySetIDError()
        r = self.t.request(
            "GET",
            f"/api/v2/policy-set-versions/{policy_set_version_id}",
        )
        jd = r.json()
        attrs = jd.get("data", {}).get("attributes", {})
        attrs["id"] = jd.get("data", {}).get("id")
        attrs["links"] = jd.get("data", {}).get("links", {})
        attrs["policy-set"] = (
            jd.get("data", {})
            .get("relationships", {})
            .get("policy-set", {})
            .get("data", {})
        )
        return PolicySetVersion.model_validate(attrs)

    def upload(self, policy_set_version: PolicySetVersion, file_path: str) -> None:
        """
        Upload uploads policy files. It takes a Policy Set Version and a path
        to the set of sentinel files, which will be packaged by hashicorp/go-slug
        before being uploaded.
        """
        # Extract upload URL from policy set version links
        if not policy_set_version.links or "upload" not in policy_set_version.links:
            raise ValueError("the Policy Set Version does not contain an upload link")

        upload_url = policy_set_version.links["upload"]
        if not upload_url:
            raise ValueError("the Policy Set Version upload URL is empty")

        # Pack the policy files directory into a tar.gz archive
        body = pack_contents(file_path)

        self.t.request(
            "PUT",
            upload_url,
            data=body.getvalue(),
            headers={"Content-Type": "application/octet-stream"},
        )
        return None
