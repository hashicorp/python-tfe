from __future__ import annotations

from ..errors import (
    InvalidCategoryError,
    InvalidParamIDError,
    InvalidPolicySetIDError,
    RequiredCategoryError,
    RequiredKeyError,
)
from ..models.policy_set_parameter import (
    PolicySetParameter,
    PolicySetParameterCreateOptions,
    PolicySetParameterList,
    PolicySetParameterListOptions,
    PolicySetParameterUpdateOptions,
)
from ..models.variable import CategoryType
from ..utils import valid_string, valid_string_id
from ._base import _Service


class PolicySetParameters(_Service):
    """
    PolicySetParameters describes all the parameter related methods that the Terraform Enterprise API supports.
    TFE API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-set-params
    """

    def list(
        self, policy_set_id: str, options: PolicySetParameterListOptions | None = None
    ) -> PolicySetParameterList:
        """List all the parameters associated with the given policy-set."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        r = self.t.request(
            "GET",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters",
            params=params,
        )
        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})
        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            attrs["policy_set"] = (
                d.get("relationships", {}).get("configurable", {}).get("data", {})
            )
            items.append(PolicySetParameter.model_validate(attrs))
        return PolicySetParameterList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

    def create(
        self, policy_set_id: str, options: PolicySetParameterCreateOptions
    ) -> PolicySetParameter:
        """Create is used to create a new parameter."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string(options.key):
            raise RequiredKeyError()

        if options.category is None:
            raise RequiredCategoryError()
        if options.category != CategoryType.POLICY_SET:
            raise InvalidCategoryError()

        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {
            "data": {
                "type": "vars",
                "attributes": attributes,
            }
        }
        r = self.t.request(
            "POST",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters",
            json_body=payload,
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs["policy_set"] = (
            data.get("relationships", {}).get("configurable", {}).get("data", {})
        )
        return PolicySetParameter.model_validate(attrs)

    def read(self, policy_set_id: str, parameter_id: str) -> PolicySetParameter:
        """Read a parameter by its ID."""
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string_id(parameter_id):
            raise InvalidParamIDError()

        r = self.t.request(
            "GET",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters/{parameter_id}",
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs["policy_set"] = (
            data.get("relationships", {}).get("configurable", {}).get("data", {})
        )
        return PolicySetParameter.model_validate(attrs)

    def update(
        self,
        policy_set_id: str,
        parameter_id: str,
        options: PolicySetParameterUpdateOptions,
    ) -> PolicySetParameter:
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string_id(parameter_id):
            raise InvalidParamIDError()
        attributes = options.model_dump(by_alias=True, exclude_none=True)
        payload = {
            "data": {
                "type": "vars",
                "id": parameter_id,
                "attributes": attributes,
            }
        }
        r = self.t.request(
            "PATCH",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters/{parameter_id}",
            json_body=payload,
        )
        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        attrs["policy_set"] = (
            data.get("relationships", {}).get("configurable", {}).get("data", {})
        )
        return PolicySetParameter.model_validate(attrs)

    def delete(self, policy_set_id: str, parameter_id: str) -> None:
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string_id(parameter_id):
            raise InvalidParamIDError()
        self.t.request(
            "DELETE",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters/{parameter_id}",
        )
        return None
