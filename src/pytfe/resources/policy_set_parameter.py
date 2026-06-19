# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
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
    ) -> Iterator[PolicySetParameter]:
        """List parameters for a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Optional pagination controls, as a
                :class:`PolicySetParameterListOptions`.

        Returns:
            A single-use ``Iterator[PolicySetParameter]``. Wrap with ``list(...)``
            to materialize the results or iterate more than once.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for parameter in client.policy_set_parameters.list("polset-123"):
            ...     print(parameter.id, parameter.key)
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/policy-sets/{policy_set_id}/parameters"
        for item in self._list(path, params=params):
            yield self._policy_set_parameter_from(item)

    def create(
        self, policy_set_id: str, options: PolicySetParameterCreateOptions
    ) -> PolicySetParameter:
        """Create a parameter on a policy set.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            options: Parameter key, value, category, and sensitivity, as a
                :class:`PolicySetParameterCreateOptions`.

        Returns:
            The created :class:`PolicySetParameter`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            RequiredKeyError: If ``options.key`` is missing or empty.
            RequiredCategoryError: If ``options.category`` is missing.
            InvalidCategoryError: If ``options.category`` is not ``policy-set``.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import CategoryType, PolicySetParameterCreateOptions
            >>> parameter = client.policy_set_parameters.create(
            ...     "polset-123",
            ...     PolicySetParameterCreateOptions(
            ...         key="environment", value="prod", category=CategoryType.POLICY_SET
            ...     ),
            ... )
        """
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
        data = r.json().get("data", {})
        return self._policy_set_parameter_from(data)

    def read(self, policy_set_id: str, parameter_id: str) -> PolicySetParameter:
        """Read a policy set parameter by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            parameter_id: The policy set parameter ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            The :class:`PolicySetParameter`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            InvalidParamIDError: If ``parameter_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> parameter = client.policy_set_parameters.read("polset-123", "var-789")
            >>> print(parameter.key)
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string_id(parameter_id):
            raise InvalidParamIDError()

        r = self.t.request(
            "GET",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters/{parameter_id}",
        )
        data = r.json().get("data", {})
        return self._policy_set_parameter_from(data)

    def update(
        self,
        policy_set_id: str,
        parameter_id: str,
        options: PolicySetParameterUpdateOptions,
    ) -> PolicySetParameter:
        """Update a policy set parameter by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            parameter_id: The policy set parameter ID (e.g. ``"var-xxxxxxxx"``).
            options: Parameter attributes to update, as a
                :class:`PolicySetParameterUpdateOptions`.

        Returns:
            The updated :class:`PolicySetParameter`.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            InvalidParamIDError: If ``parameter_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import PolicySetParameterUpdateOptions
            >>> parameter = client.policy_set_parameters.update(
            ...     "polset-123", "var-789",
            ...     PolicySetParameterUpdateOptions(value="staging"),
            ... )
        """
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
        data = r.json().get("data", {})
        return self._policy_set_parameter_from(data)

    def delete(self, policy_set_id: str, parameter_id: str) -> None:
        """Delete a policy set parameter by its ID.

        Args:
            policy_set_id: The policy set ID (e.g. ``"polset-xxxxxxxx"``).
            parameter_id: The policy set parameter ID (e.g. ``"var-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidPolicySetIDError: If ``policy_set_id`` is not a valid resource ID.
            InvalidParamIDError: If ``parameter_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.policy_set_parameters.delete("polset-123", "var-789")
        """
        if not valid_string_id(policy_set_id):
            raise InvalidPolicySetIDError()

        if not valid_string_id(parameter_id):
            raise InvalidParamIDError()
        self.t.request(
            "DELETE",
            path=f"api/v2/policy-sets/{policy_set_id}/parameters/{parameter_id}",
        )
        return None

    def _policy_set_parameter_from(self, d: dict[str, Any]) -> PolicySetParameter:
        """Convert API response dict to PolicySetParameter model."""
        attrs = d.get("attributes", {})
        attrs["id"] = d.get("id")
        attrs["policy_set"] = (
            d.get("relationships", {}).get("configurable", {}).get("data", {})
        )
        return attach_jsonapi(PolicySetParameter.model_validate(attrs), d)
