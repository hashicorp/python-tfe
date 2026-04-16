# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator

from pytfe.models import (
    AgentPool,
    Project,
)

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
        """Create a new stack within a project."""
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
        """Update an existing stack."""
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
        """List stacks within an organization, with optional filtering by project."""
        params = options.model_dump(by_alias=True, exclude_none=True)
        path = f"/api/v2/organizations/{organization}/stacks"
        for item in self._list(path, params=params):
            yield self._stack_from(item)

    def read(self, stack_id: str) -> Stack:
        """Read a stack by ID."""
        r = self.t.request(
            "GET",
            path=f"/api/v2/stacks/{stack_id}",
        )
        data = r.json().get("data", {})
        return self._stack_from(data)

    def delete(self, stack_id: str) -> None:
        """Delete a stack by ID."""
        self.t.request(
            "DELETE",
            path=f"/api/v2/stacks/{stack_id}",
        )
        return None

    def force_delete(self, stack_id: str) -> None:
        """ForceDelete deletes a stack that still has deployments."""
        self.t.request(
            "DELETE",
            path=f"/api/v2/stacks/{stack_id}?force=true",
        )
        return None

    def _stack_from(self, data: dict) -> Stack:
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")
        relationships = data.get("relationships", {})
        vcs_repo_raw = attrs.get("vcs-repo")
        if vcs_repo_raw:
            attrs["vcs_repo"] = StackVcsRepo.model_validate(vcs_repo_raw)
        else:
            attrs["vcs_repo"] = None
        project_data = relationships.get("project", {}).get("data", {})
        agent_pool_data = relationships.get("agent-pool", {}).get("data", {})
        if isinstance(project_data, dict) and project_data.get("id"):
            attrs["project"] = Project(id=project_data["id"])
        if isinstance(agent_pool_data, dict) and agent_pool_data.get("id"):
            attrs["agent_pool"] = AgentPool(id=agent_pool_data["id"])
        return Stack.model_validate(attrs)
