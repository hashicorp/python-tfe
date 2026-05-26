from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    Project,
    ProjectSettingsPermissionType,
    ProjectTeamsPermissionType,
    ProjectVariableSetsPermissionType,
    Team,
    TeamProjectAccessAddOptions,
    TeamProjectAccessListOptions,
    TeamProjectAccessProjectPermissionsOptions,
    TeamProjectAccessType,
    TeamProjectAccessUpdateOptions,
    TeamProjectAccessWorkspacePermissionsOptions,
    WorkspaceRunsPermissionType,
    WorkspaceSentinelMocksPermissionType,
    WorkspaceStateVersionsPermissionType,
    WorkspaceVariablesPermissionType,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_team_project_access(result):
    print(f"- id: {result.id}")
    print(f"- access: {result.access.value if result.access else None}")
    print(f"- team_id: {result.team.id if result.team else None}")
    print(f"- project_id: {result.project.id if result.project else None}")

    if result.project_access:
        print("- project_access:")
        print(f"  settings={result.project_access.project_settings_permission.value}")
        print(f"  teams={result.project_access.project_teams_permission.value}")
        print(
            "  variable_sets="
            f"{result.project_access.project_variable_sets_permission.value}"
        )

    if result.workspace_access:
        print("- workspace_access:")
        print(
            f"  runs={result.workspace_access.runs.value if result.workspace_access.runs else None}"
        )
        print(
            "  sentinel_mocks="
            f"{result.workspace_access.sentinel_mocks.value if result.workspace_access.sentinel_mocks else None}"
        )
        print(
            "  state_versions="
            f"{result.workspace_access.state_versions.value if result.workspace_access.state_versions else None}"
        )
        print(
            f"  variables={result.workspace_access.variables.value if result.workspace_access.variables else None}"
        )
        print(f"  create={result.workspace_access.create}")
        print(f"  delete={result.workspace_access.delete}")
        print(f"  locking={result.workspace_access.locking}")
        print(f"  move={result.workspace_access.move}")
        print(f"  run_tasks={result.workspace_access.run_tasks}")


def main():
    parser = argparse.ArgumentParser(
        description="Team Project Access operations demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--operation",
        required=True,
        choices=["add", "read", "update", "list", "remove"],
        help="Operation to execute",
    )
    parser.add_argument("--team-id", help="Team ID (required for add)")
    parser.add_argument("--project-id", help="Project ID (required for add/list)")
    parser.add_argument(
        "--team-project-access-id",
        help="Team Project Access ID (required for read/update/remove)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Page size for list operation",
    )
    parser.add_argument(
        "--access",
        choices=[item.value for item in TeamProjectAccessType],
        default=None,
        help="Access level (required as custom when granular project/workspace permissions are set)",
    )

    # Optional custom project permissions
    parser.add_argument(
        "--project-settings",
        choices=[item.value for item in ProjectSettingsPermissionType],
        default=None,
        help="Project settings permission (custom access)",
    )
    parser.add_argument(
        "--project-teams",
        choices=[item.value for item in ProjectTeamsPermissionType],
        default=None,
        help="Project teams permission (custom access)",
    )
    parser.add_argument(
        "--project-variable-sets",
        choices=[item.value for item in ProjectVariableSetsPermissionType],
        default=None,
        help="Project variable sets permission (custom access)",
    )

    # Optional custom workspace permissions
    parser.add_argument(
        "--workspace-runs",
        choices=[item.value for item in WorkspaceRunsPermissionType],
        default=None,
        help="Workspace runs permission (custom access)",
    )
    parser.add_argument(
        "--workspace-sentinel-mocks",
        choices=[item.value for item in WorkspaceSentinelMocksPermissionType],
        default=None,
        help="Workspace sentinel-mocks permission (custom access)",
    )
    parser.add_argument(
        "--workspace-state-versions",
        choices=[item.value for item in WorkspaceStateVersionsPermissionType],
        default=None,
        help="Workspace state-versions permission (custom access)",
    )
    parser.add_argument(
        "--workspace-variables",
        choices=[item.value for item in WorkspaceVariablesPermissionType],
        default=None,
        help="Workspace variables permission (custom access)",
    )
    parser.add_argument("--workspace-create", action="store_true", default=None)
    parser.add_argument("--workspace-delete", action="store_true", default=None)
    parser.add_argument("--workspace-locking", action="store_true", default=None)
    parser.add_argument("--workspace-move", action="store_true", default=None)
    parser.add_argument("--workspace-run-tasks", action="store_true", default=None)

    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    project_access = None
    if any([args.project_settings, args.project_teams, args.project_variable_sets]):
        project_access = TeamProjectAccessProjectPermissionsOptions(
            settings=(
                ProjectSettingsPermissionType(args.project_settings)
                if args.project_settings
                else None
            ),
            teams=(
                ProjectTeamsPermissionType(args.project_teams)
                if args.project_teams
                else None
            ),
            variable_sets=(
                ProjectVariableSetsPermissionType(args.project_variable_sets)
                if args.project_variable_sets
                else None
            ),
        )

    workspace_access = None
    if any(
        [
            args.workspace_runs,
            args.workspace_sentinel_mocks,
            args.workspace_state_versions,
            args.workspace_variables,
            args.workspace_create,
            args.workspace_delete,
            args.workspace_locking,
            args.workspace_move,
            args.workspace_run_tasks,
        ]
    ):
        workspace_access = TeamProjectAccessWorkspacePermissionsOptions(
            runs=(
                WorkspaceRunsPermissionType(args.workspace_runs)
                if args.workspace_runs
                else None
            ),
            sentinel_mocks=(
                WorkspaceSentinelMocksPermissionType(args.workspace_sentinel_mocks)
                if args.workspace_sentinel_mocks
                else None
            ),
            state_versions=(
                WorkspaceStateVersionsPermissionType(args.workspace_state_versions)
                if args.workspace_state_versions
                else None
            ),
            variables=(
                WorkspaceVariablesPermissionType(args.workspace_variables)
                if args.workspace_variables
                else None
            ),
            create=args.workspace_create,
            delete=args.workspace_delete,
            locking=args.workspace_locking,
            move=args.workspace_move,
            run_tasks=args.workspace_run_tasks,
        )

    has_granular_permissions = (
        project_access is not None or workspace_access is not None
    )
    if (
        has_granular_permissions
        and args.access
        and args.access != TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM.value
    ):
        parser.error(
            "When custom project/workspace permissions are provided, --access must be 'custom'"
        )

    if args.operation == "add":
        if not args.team_id or not args.project_id:
            parser.error("--team-id and --project-id are required for operation=add")

        _print_header("Adding team project access")
        access_value = args.access
        if access_value is None:
            access_value = (
                TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM.value
                if has_granular_permissions
                else TeamProjectAccessType.TEAM_PROJECT_ACCESS_READ.value
            )

        options = TeamProjectAccessAddOptions(
            access=TeamProjectAccessType(access_value),
            team=Team(id=args.team_id),
            project=Project(id=args.project_id),
            project_access=project_access,
            workspace_access=workspace_access,
        )
        result = client.team_project_accesses.add(options)
        print("Created team project access")
        _print_team_project_access(result)
        return

    if args.operation == "read":
        if not args.team_project_access_id:
            parser.error("--team-project-access-id is required for operation=read")

        _print_header("Reading team project access")
        result = client.team_project_accesses.read(args.team_project_access_id)
        print("Retrieved team project access")
        _print_team_project_access(result)
        return

    if args.operation == "update":
        if not args.team_project_access_id:
            parser.error("--team-project-access-id is required for operation=update")

        _print_header("Updating team project access")
        update_access = None
        if args.access:
            update_access = TeamProjectAccessType(args.access)
        elif has_granular_permissions:
            update_access = TeamProjectAccessType.TEAM_PROJECT_ACCESS_CUSTOM

        update_options = TeamProjectAccessUpdateOptions(
            access=update_access,
            project_access=project_access,
            workspace_access=workspace_access,
        )
        result = client.team_project_accesses.update(
            args.team_project_access_id,
            update_options,
        )
        print("Updated team project access")
        _print_team_project_access(result)
        return

    if args.operation == "list":
        if not args.project_id:
            parser.error("--project-id is required for operation=list")

        _print_header("Listing team project accesses")
        list_options = TeamProjectAccessListOptions(
            page_size=args.page_size,
            Project_id=args.project_id,
        )
        results = list(client.team_project_accesses.list(list_options))
        print(f"Found {len(results)} team project access entries")
        for item in results:
            print("-")
            _print_team_project_access(item)
        return

    if args.operation == "remove":
        if not args.team_project_access_id:
            parser.error("--team-project-access-id is required for operation=remove")

        _print_header("Removing team project access")
        client.team_project_accesses.remove(args.team_project_access_id)
        print(f"Removed team project access: {args.team_project_access_id}")
        return


if __name__ == "__main__":
    main()
