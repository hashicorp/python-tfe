from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    TeamCreateOptions,
    TeamIncludeOpt,
    TeamListOptions,
    TeamUpdateOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Teams list demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--org",
        required=True,
        help="Organization name",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Page size for fetching teams",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Optional q filter for team search",
    )
    parser.add_argument(
        "--names",
        nargs="+",
        default=None,
        help="Optional team names filter (space-separated)",
    )
    parser.add_argument(
        "--include-users",
        action="store_true",
        help="Include related users",
    )
    parser.add_argument(
        "--include-memberships",
        action="store_true",
        help="Include related organization-memberships",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create a new team before listing",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Team name for create operation",
    )
    parser.add_argument(
        "--visibility",
        default="secret",
        help="Team visibility for create operation (secret or organization)",
    )
    parser.add_argument(
        "--sso-team-id",
        default=None,
        help="Optional SSO team ID for create operation",
    )
    parser.add_argument(
        "--allow-member-token-management",
        action="store_true",
        help="Enable member token management on create/update",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update a team before listing",
    )
    parser.add_argument(
        "--team-id",
        default=None,
        help="Team ID for update operation",
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    if args.create:
        if not args.name:
            print("Error: --name is required when using --create")
            return

        _print_header(f"Creating team in organization: {args.org}")
        create_options = TeamCreateOptions(
            name=args.name,
            visibility=args.visibility,
            sso_team_id=args.sso_team_id,
            allow_member_token_management=args.allow_member_token_management,
        )
        new_team = client.teams.create(args.org, create_options)
        print(f"Created Team ID: {new_team.id}")
        print(f"Name: {new_team.name}")
        print(f"Visibility: {new_team.visibility}")
        print(
            f"Allow Member Token Management: {new_team.allow_member_token_management}"
        )
        print()

    if args.update:
        if not args.team_id:
            print("Error: --team-id is required when using --update")
            return

        _print_header(f"Updating team: {args.team_id}")
        update_options = TeamUpdateOptions(
            name=args.name,
            visibility=args.visibility,
            sso_team_id=args.sso_team_id,
            allow_member_token_management=args.allow_member_token_management,
        )
        updated_team = client.teams.update(args.team_id, update_options)
        print(f"Updated Team ID: {updated_team.id}")
        print(f"Name: {updated_team.name}")
        print(f"Visibility: {updated_team.visibility}")
        print(
            f"Allow Member Token Management: {updated_team.allow_member_token_management}"
        )
        print()

    includes: list[TeamIncludeOpt] = []
    if args.include_users:
        includes.append(TeamIncludeOpt.TEAM_USERS)
    if args.include_memberships:
        includes.append(TeamIncludeOpt.TEAM_ORGANIZATION_MEMBERSHIPS)

    options = TeamListOptions(
        page_size=args.page_size,
        query=args.query,
        names=args.names,
        include=includes or None,
    )

    _print_header(f"Listing teams for organization: {args.org}")
    print("Options:")
    print(f"- page_size={args.page_size}")
    print(f"- query={args.query}")
    print(f"- names={args.names}")
    print(f"- include={[item.value for item in includes] if includes else None}")
    print()

    count = 0
    for team in client.teams.list(args.org, options):
        count += 1
        print(f"[{count}] Team ID: {team.id}")
        print(f"Name: {team.name}")
        print(f"Visibility: {team.visibility}")
        print(f"Is Unified: {team.is_unified}")
        print(f"User Count: {team.user_count}")
        print(f"Allow Member Token Management: {team.allow_member_token_management}")

        if team.organization_access:
            print("Organization Access:")
            print(f"  - manage_workspaces={team.organization_access.manage_workspaces}")
            print(f"  - read_workspaces={team.organization_access.read_workspaces}")
            print(f"  - manage_projects={team.organization_access.manage_projects}")

        if team.permissions:
            print("Permissions:")
            print(f"  - can_update_membership={team.permissions.can_update_membership}")
            print(f"  - can_destroy={team.permissions.can_destroy}")

        print(f"Users included: {len(team.users)}")
        print(
            f"Organization memberships included: {len(team.organization_memberships)}"
        )
        print()

    if count == 0:
        print("No teams found.")
    else:
        print(f"Total teams: {count}")


if __name__ == "__main__":
    main()
