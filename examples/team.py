from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import TeamIncludeOpt, TeamListOptions


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
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

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
    print("options", options)
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
        print("team user", team.organization_memberships)

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
