from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ..models.common import Pagination
from .agent import AgentPool
from .organization import Organization

# Use TYPE_CHECKING to avoid circular import issues between RunTask and WorkspaceRunTask
# This allows forward references without importing at runtime
if TYPE_CHECKING:
    from .workspace_run_task import WorkspaceRunTask


class RunTask(BaseModel):
    id: str
    name: str
    description: str | None = None
    url: str
    category: str
    hmac_key: str | None = None
    enabled: bool
    global_configuration: GlobalRunTask | None = None

    agent_pool: AgentPool | None = None
    organization: Organization | None = None
    # Workspace run tasks that use this run task
    # Added to support the workspace_run_tasks relationship in the API
    workspace_run_tasks: list[WorkspaceRunTask] = Field(default_factory=list)


class GlobalRunTask(BaseModel):
    enabled: bool
    stages: list[Stage] = Field(default_factory=list)
    enforcement_level: TaskEnforcementLevel


class GlobalRunTaskOptions(BaseModel):
    enabled: bool | None = None
    stages: list[Stage] | None = Field(default_factory=list)
    enforcement_level: TaskEnforcementLevel | None = None


class Stage(str, Enum):
    """Run task stage enumeration.

    Defines when a run task should execute in the run lifecycle.

    Note: Values use underscore format (e.g., 'pre_plan') to match the
    Terraform Cloud API specification. This was changed from hyphen format
    (e.g., 'pre-plan') to align with the actual API responses and requests.
    """

    PRE_PLAN = "pre_plan"
    POST_PLAN = "post_plan"
    PRE_APPLY = "pre_apply"
    POST_APPLY = "post_apply"


class TaskEnforcementLevel(str, Enum):
    ADVISORY = "advisory"
    MANDATORY = "mandatory"


class RunTaskIncludeOptions(str, Enum):
    RUN_TASK_WORKSPACE_TASKS = "workspace_tasks"
    RUN_TASK_WORKSPACE = "workspace_tasks.workspace"


class RunTaskList(BaseModel):
    items: list[RunTask] = Field(default_factory=list)
    pagination: Pagination | None = None


class RunTaskListOptions(BaseModel):
    page_number: int | None = None
    page_size: int | None = None
    include: list[RunTaskIncludeOptions] | None = Field(default_factory=list)


class RunTaskReadOptions(BaseModel):
    include: list[RunTaskIncludeOptions] | None = Field(default_factory=list)


class RunTaskCreateOptions(BaseModel):
    type: str = Field(default="tasks")
    name: str
    description: str | None = None
    url: str
    category: str
    hmac_key: str | None = None
    enabled: bool = True
    global_configuration: GlobalRunTaskOptions | None = None
    agent_pool: AgentPool | None = None


class RunTaskUpdateOptions(BaseModel):
    type: str = Field(default="tasks")
    name: str | None = None
    description: str | None = None
    url: str | None = None
    category: str | None = None
    hmac_key: str | None = None
    enabled: bool | None = None
    global_configuration: GlobalRunTaskOptions | None = None
    agent_pool: AgentPool | None = None


def _rebuild_models() -> None:
    """Rebuild models to resolve forward references.

    This function resolves the circular dependency between RunTask and WorkspaceRunTask.
    It imports WorkspaceRunTask and rebuilds the Pydantic models so that forward
    references (e.g., list["WorkspaceRunTask"]) are properly resolved.

    The try-except ensures that if WorkspaceRunTask hasn't been defined yet,
    the models will rebuild later when first used.
    """
    try:
        from .workspace_run_task import WorkspaceRunTask  # noqa: F401

        RunTask.model_rebuild()
        GlobalRunTask.model_rebuild()
        GlobalRunTaskOptions.model_rebuild()
        RunTaskUpdateOptions.model_rebuild()
    except Exception:
        # Models will rebuild later when first used
        pass


_rebuild_models()
