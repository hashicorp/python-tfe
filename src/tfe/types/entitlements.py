from __future__ import annotations

from pydantic import BaseModel

__all__ = [
    "Entitlements",
]


class Entitlements(BaseModel):
    id: str
    agents: bool | None = None
    audit_logging: bool | None = None
    cost_estimation: bool | None = None
    global_run_tasks: bool | None = None
    operations: bool | None = None
    private_module_registry: bool | None = None
    private_run_tasks: bool | None = None
    run_tasks: bool | None = None
    sso: bool | None = None
    sentinel: bool | None = None
    state_storage: bool | None = None
    teams: bool | None = None
    vcs_integrations: bool | None = None
    waypoint_actions: bool | None = None
    waypoint_templates_and_addons: bool | None = None