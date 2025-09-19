from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from ..types import Pagination
from .agentpool import AgentPool
from .organization import Organization
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
    PRE_PLAN = "pre-plan"
    POST_PLAN = "post-plan"
    PRE_APPLY = "pre-apply"
    POST_APPLY = "post-apply"


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
