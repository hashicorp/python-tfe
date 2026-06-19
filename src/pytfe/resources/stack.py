# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator

from pytfe.models import (
    AgentPool,
    Project,
)

from .._jsonapi import attach_jsonapi, parse_relationships
from ..models.stack import (
    Stack,
    StackCreateOptions,
    StackListOptions,
    StackUpdateOptions,
    StackVcsRepo,
)
from ._base import _Service


class Stacks(_Service):
    def create(self, options: StackCreateOptions) -> Stack:
        """Create a new stack within a project.

        Args:
            options: The stack creation settings, as a :class:`StackCreateOptions`.

        Returns:
            The created :class:`Stack`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import Project, StackCreateOptions
            >>> stack = client.stacks.create(
            ...     StackCreateOptions(
            ...         name="app-stack", project=Project(id="prj-xxxxxxxx")
            ...     )
            ... )
        """
        payload = {
            "data": {
                "attributes": options.model_dump(
                    by_alias=True, exclude_none=True, exclude={"project", "agent_pool"}
                ),
                "type": "stacks",
                "relationships": {},
            }
        }
        relationships = {}
        if options.project:
            relationships["project"] = {
                "data": {"id": options.project.id, "type": "projects"}
            }
        if options.agent_pool:
            relationships["agent-pool"] = {
                "data": {"id": options.agent_pool.id, "type": "agent-pools"}
            }
        payload["data"]["relationships"] = relationships
        r = self.t.request(
            "POST",
            path="/api/v2/stacks",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._stack_from(data)

    def update(self, stack_id: str, options: StackUpdateOptions) -> Stack:
        """Update an existing stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).
            options: The stack fields to update, as a :class:`StackUpdateOptions`.

        Returns:
            The :class:`Stack`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StackUpdateOptions
            >>> stack = client.stacks.update(
            ...     "st-123", StackUpdateOptions(description="Production stack")
            ... )
        """
        payload = {
            "data": {
                "attributes": options.model_dump(
                    by_alias=True,
                    exclude_none=True,
                    exclude={"agent_pool", "project"},
                ),
                "type": "stacks",
                "relationships": {},
            }
        }
        relationships = {}
        if options.project:
            relationships.update(
                {"project": {"data": {"id": options.project.id, "type": "projects"}}}
            )
        if options.agent_pool:
            relationships.update(
                {
                    "agent-pool": {
                        "data": {"id": options.agent_pool.id, "type": "agent-pools"}
                    }
                }
            )
        payload["data"]["relationships"] = relationships
        r = self.t.request(
            "PATCH",
            path=f"/api/v2/stacks/{stack_id}",
            json_body=payload,
        )
        data = r.json().get("data", {})
        return self._stack_from(data)

    def list(self, organization: str, options: StackListOptions) -> Iterator[Stack]:
        """List stacks within an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: Filtering and pagination settings, as a :class:`StackListOptions`.

        Returns:
            A single-use ``Iterator[Stack]``. Wrap with ``list(...)`` to materialize
            the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StackListOptions
            >>> stacks = client.stacks.list(
            ...     "my-org", StackListOptions(page_size=20)
            ... )
            >>> for stack in stacks:
            ...     print(stack.id, stack.name)
        """
        params = options.model_dump(by_alias=True, exclude_none=True)
        path = f"/api/v2/organizations/{organization}/stacks"
        for item in self._list(path, params=params):
            yield self._stack_from(item)

    def read(self, stack_id: str) -> Stack:
        """Read a stack by ID.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).

        Returns:
            The :class:`Stack`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> stack = client.stacks.read("st-123")
            >>> print(stack.name)
        """
        r = self.t.request(
            "GET",
            path=f"/api/v2/stacks/{stack_id}",
        )
        data = r.json().get("data", {})
        return self._stack_from(data)

    def delete(self, stack_id: str) -> None:
        """Delete a stack by ID.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.stacks.delete("st-123")
        """
        self.t.request(
            "DELETE",
            path=f"/api/v2/stacks/{stack_id}",
        )
        return None

    def force_delete(self, stack_id: str) -> None:
        """Force delete a stack that still has deployments.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> client.stacks.force_delete("st-123")
        """
        self.t.request(
            "DELETE",
            path=f"/api/v2/stacks/{stack_id}?force=true",
        )
        return None

    def fetch_latest_from_vcs(self, stack_id: str) -> Stack:
        """Fetch the latest stack configuration from VCS.

        This triggers stack preparation for the latest VCS revision.

        Args:
            stack_id: The stack ID (e.g. ``"st-xxxxxxxx"``).

        Returns:
            The :class:`Stack`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> stack = client.stacks.fetch_latest_from_vcs("st-123")
            >>> print(stack.updated_at)
        """
        path = f"/api/v2/stacks/{stack_id}/fetch-latest-from-vcs"
        r = self.t.request("POST", path=path)
        data = r.json().get("data", {})
        return self._stack_from(data)

    def _stack_from(self, data: dict) -> Stack:
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        vcs_repo_raw = attrs.get("vcs-repo")
        attrs["vcs_repo"] = (
            StackVcsRepo.model_validate(vcs_repo_raw) if vcs_repo_raw else None
        )
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"project": Project, "agent-pool": AgentPool},
            )
        )
        return attach_jsonapi(Stack.model_validate(attrs), data)
