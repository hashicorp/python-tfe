from __future__ import annotations

from ..errors import (
    InvalidNameError,
    InvalidOrgError,
    InvalidPolicyIDError,
    RequiredEnforceError,
    RequiredNameError,
    RequiredQueryError,
)
from ..models.policy import (
    Policy,
    PolicyCreateOptions,
    PolicyList,
    PolicyListOptions,
    PolicyUpdateOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service


class Policies(_Service):
    def list(
        self, organization: str, options: PolicyListOptions | None = None
    ) -> PolicyList:
        """List all the policies of the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )
        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/policies",
            params=params,
        )
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            attrs["organization"] = d.get("relationships", {}).get("organization", {})
            items.append(Policy.model_validate(attrs))
        return PolicyList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

    def create(self, organization: str, options: PolicyCreateOptions) -> Policy:
        """Create a new policy in the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        valid = self._valid_create_options(options)
        if valid is not None:
            raise valid
        payload = {
            "data": {
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
                "type": "policies",
            }
        }
        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/policies",
            json_body=payload,
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        return Policy.model_validate(attrs)

    def read(self, policy_id: str) -> Policy:
        """Read a specific policy by its ID."""
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        r = self.t.request(
            "GET",
            f"/api/v2/policies/{policy_id}",
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["organization"] = d.get("relationships", {}).get("organization", {})
        return Policy.model_validate(attrs)

    def update(self, policy_id: str, options: PolicyUpdateOptions) -> Policy:
        """Update an existing policy by its ID."""
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        payload = {
            "data": {
                "type": "policies",
                "attributes": options.model_dump(by_alias=True, exclude_none=True),
            }
        }
        r = self.t.request(
            "PATCH",
            f"/api/v2/policies/{policy_id}",
            json_body=payload,
        )
        jd = r.json()
        d = jd.get("data", {})
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["organization"] = d.get("relationships", {}).get("organization", {})
        return Policy.model_validate(attrs)

    def delete(self, policy_id: str) -> None:
        """Delete a specific policy by its ID."""
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        self.t.request(
            "DELETE",
            f"/api/v2/policies/{policy_id}",
        )
        return None

    def upload(self, policy_id: str, content: bytes) -> None:
        """Upload the policy content of the policy."""
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError

        # Send binary content directly (not as JSON)
        self.t.request(
            "PUT",
            f"/api/v2/policies/{policy_id}/upload",
            data=content,
            headers={"Content-Type": "application/octet-stream"},
        )
        return None

    def download(self, policy_id: str) -> bytes:
        """Download the policy content of the policy."""
        if not valid_string_id(policy_id):
            raise InvalidPolicyIDError
        r = self.t.request(
            "GET",
            f"/api/v2/policies/{policy_id}/download",
        )
        return r.content

    def _valid_create_options(self, options: PolicyCreateOptions) -> None | Exception:
        """Validate the given PolicyCreateOptions."""
        if not valid_string(options.name):
            return RequiredNameError()
        if not valid_string_id(options.name):
            return InvalidNameError()

        if options.kind == "opa" and not valid_string(options.query):
            return RequiredQueryError()

        if not options.enforcement_level:
            return RequiredEnforceError()

        return None
