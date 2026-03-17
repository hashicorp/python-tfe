from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import ERR_REQUIRED_PROJECT, InvalidProjectIDError, RequiredTeamError
from ..utils import valid_string_id
from .project import Project
from .team import Team


class TeamProjectAccessType(str, Enum):
    """TeamProjectAccessType represents a team project access type."""

    TEAM_PROJECT_ACCESS_ADMIN = "admin"
    TEAM_PROJECT_ACCESS_MAINTAIN = "maintain"
    TEAM_PROJECT_ACCESS_WRITE = "write"
    TEAM_PROJECT_ACCESS_READ = "read"
    TEAM_PROJECT_ACCESS_CUSTOM = "custom"


class ProjectSettingsPermissionType(str, Enum):
    """ProjectSettingsPermissionType represents the permissiontype to a project's settings"""

    PROJECT_SETTINGS_PERMISSION_READ = "read"
    PROJECT_SETTINGS_PERMISSION_UPDATE = "update"
    PROJECT_SETTINGS_PERMISSION_DELETE = "delete"


class ProjectTeamsPermissionType(str, Enum):
    """ProjectTeamsPermissionType represents the permissiontype to a project's teams"""

    PROJECT_TEAMS_PERMISSION_READ = "read"
    PROJECT_TEAMS_PERMISSION_NONE = "none"
    PROJECT_TEAMS_PERMISSION_MANAGE = "manage"


class ProjectVariableSetsPermissionType(str, Enum):
    """ProjectVariableSetsPermissionType represents the permissiontype to a project's variable sets"""

    PROJECT_VARIABLE_SETS_PERMISSION_READ = "read"
    PROJECT_VARIABLE_SETS_PERMISSION_WRITE = "write"
    PROJECT_VARIABLE_SETS_PERMISSION_NONE = "none"


class TeamProjectAccessProjectPermissions(BaseModel):
    """ProjectPermissions represents the team's permissions on its project"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    project_settings_permission: ProjectSettingsPermissionType = Field(alias="settings")
    project_teams_permission: ProjectTeamsPermissionType = Field(alias="teams")
    # ProjectVariableSetsPermission represents read, manage, and no access custom permission for project-level variable sets
    project_variable_sets_permission: ProjectVariableSetsPermissionType = Field(
        alias="variable-sets"
    )


class WorkspaceRunsPermissionType(str, Enum):
    """WorkspaceRunsPermissionType represents the permissiontype to project workspaces' runs"""

    WORKSPACE_RUNS_PERMISSION_READ = "read"
    WORKSPACE_RUNS_PERMISSION_PLAN = "plan"
    WORKSPACE_RUNS_PERMISSION_APPLY = "apply"


class WorkspaceSentinelMocksPermissionType(str, Enum):
    """WorkspaceSentinelMocksPermissionType represents the permissiontype to project workspaces' sentinel-mocks"""

    WORKSPACE_SENTINEL_MOCKS_PERMISSION_READ = "read"
    WORKSPACE_SENTINEL_MOCKS_PERMISSION_NONE = "none"


class WorkspaceStateVersionsPermissionType(str, Enum):
    """WorkspaceStateVersionsPermissionType represents the permissiontype to project workspaces' state-versions"""

    WORKSPACE_STATE_VERSIONS_PERMISSION_NONE = "none"
    WORKSPACE_STATE_VERSIONS_PERMISSION_READ_OUTPUTS = "read-outputs"
    WORKSPACE_STATE_VERSIONS_PERMISSION_WRITE = "write"


class WorkspaceVariablesPermissionType(str, Enum):
    """WorkspaceVariablesPermissionType represents the permissiontype to project workspaces' variables"""

    WORKSPACE_VARIABLES_PERMISSION_NONE = "none"
    WORKSPACE_VARIABLES_PERMISSION_READ = "read"
    WORKSPACE_VARIABLES_PERMISSION_WRITE = "write"


class TeamProjectAccessWorkspacePermissions(BaseModel):
    """WorkspacePermissions represents the team's permission on all workspaces in its project"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    runs: WorkspaceRunsPermissionType | None = Field(default=None, alias="runs")
    sentinel_mocks: WorkspaceSentinelMocksPermissionType | None = Field(
        default=None, alias="sentinel-mocks"
    )
    state_versions: WorkspaceStateVersionsPermissionType | None = Field(
        default=None, alias="state-versions"
    )
    variables: WorkspaceVariablesPermissionType | None = Field(
        default=None, alias="variables"
    )
    create: bool = Field(default=False, alias="create")
    delete: bool = Field(default=False, alias="delete")
    locking: bool = Field(default=False, alias="locking")
    move: bool = Field(default=False, alias="move")
    run_tasks: bool = Field(default=False, alias="run-tasks")


class TeamProjectAccess(BaseModel):
    """TeamProjectAccess represents a project access for a team"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    access: TeamProjectAccessType | None = Field(default=None, alias="access")
    project_access: TeamProjectAccessProjectPermissions | None = Field(
        default=None, alias="project-access"
    )
    workspace_access: TeamProjectAccessWorkspacePermissions | None = Field(
        default=None, alias="workspace-access"
    )

    # relations
    project: Project | None = Field(default=None, alias="project")
    team: Team | None = Field(default=None, alias="team")


class TeamProjectAccessListOptions(BaseModel):
    """TeamProjectAccessListOptions represents the options for listing team project accesses"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    Project_id: str | None = Field(default=None, alias="filter[project][id]")

    @model_validator(mode="after")
    def valid(self) -> TeamProjectAccessListOptions:
        """Validate the options."""
        if self.Project_id is not None and not valid_string_id(self.Project_id):
            raise InvalidProjectIDError()
        return self


class TeamProjectAccessProjectPermissionsOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    settings: ProjectSettingsPermissionType | None = Field(
        default=None, alias="settings"
    )
    teams: ProjectTeamsPermissionType | None = Field(default=None, alias="teams")
    variable_sets: ProjectVariableSetsPermissionType | None = Field(
        default=None, alias="variable-sets"
    )


class TeamProjectAccessAddOptions(BaseModel):
    """TeamProjectAccessAddOptions represents the options for adding team access for a project"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    access: TeamProjectAccessType = Field(alias="access")
    project_access: TeamProjectAccessProjectPermissionsOptions | None = Field(
        default=None, alias="project-access"
    )
    workspace_access: TeamProjectAccessWorkspacePermissions | None = Field(
        default=None, alias="workspace-access"
    )

    # relations
    team: Team | None = Field(default=None, alias="team")
    project: Project | None = Field(default=None, alias="project")

    @model_validator(mode="after")
    def valid(self) -> TeamProjectAccessAddOptions:
        """Validate the options."""

        if self.team is None:
            raise RequiredTeamError()
        if self.project is None:
            raise ValueError(ERR_REQUIRED_PROJECT)
        return self


class TeamProjectAccessUpdateOptions(BaseModel):
    """TeamProjectAccessUpdateOptions represents the options for updating a team project access"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    access: TeamProjectAccessType | None = Field(default=None, alias="access")
    project_access: TeamProjectAccessProjectPermissionsOptions | None = Field(
        default=None, alias="project-access"
    )
    workspace_access: TeamProjectAccessWorkspacePermissions | None = Field(
        default=None, alias="workspace-access"
    )
