#!/usr/bin/env python3
"""Team membership example.

Demonstrates the new team-membership management methods on ``Teams``::

    add_users(team_id, usernames)
    remove_users(team_id, usernames)
    list_users(team_id)
    add_organization_memberships(team_id, ou_ids)
    remove_organization_memberships(team_id, ou_ids)
    list_organization_memberships(team_id)

This example creates a scratch team, lists its (initially empty)
members, adds and removes a user, then deletes the scratch team.

Usage::

    TFE_TOKEN=... TFE_ORG=prab-sandbox02 \\
        python examples/team_membership.py --username someone

To exercise add/remove by organization-membership id, pass
``--ou-id ou-XXXX`` instead of ``--username``.
"""

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import TeamCreateOptions


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    p.add_argument("--team-id", help="Use an existing team instead of creating one")
    p.add_argument(
        "--username",
        help="HCP Terraform username to add to the team (read-only demo if "
        "omitted)",
    )
    p.add_argument(
        "--ou-id",
        help="Organization membership id to add/remove (alternative to --username)",
    )
    args = p.parse_args()

    if not args.token or not args.organization:
        print("set TFE_TOKEN and TFE_ORG")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    created_team_id: str | None = None
    try:
        team_id = args.team_id
        if team_id is None:
            stamp = int(time.time())
            t = client.teams.create(
                args.organization,
                TeamCreateOptions(
                    name=f"pytfe-team-{stamp}", visibility="secret"
                ),
            )
            team_id = t.id
            created_team_id = t.id
            print(f"created team: {t.id} ({t.name})")

        users = client.teams.list_users(team_id)
        print(f"team has {len(users)} users initially")

        ous = client.teams.list_organization_memberships(team_id)
        print(f"team has {len(ous)} organization-membership records initially")

        if args.username:
            print(f"\nadding user '{args.username}' to team {team_id}")
            client.teams.add_users(team_id, [args.username])
            after = client.teams.list_users(team_id)
            print(f"team now has {len(after)} users")
            print(f"removing user '{args.username}' from team {team_id}")
            client.teams.remove_users(team_id, [args.username])
            after2 = client.teams.list_users(team_id)
            print(f"team now has {len(after2)} users")

        if args.ou_id:
            print(f"\nadding organization membership '{args.ou_id}' to team")
            client.teams.add_organization_memberships(team_id, [args.ou_id])
            after_ou = client.teams.list_organization_memberships(team_id)
            print(f"team now has {len(after_ou)} organization memberships")
            print(f"removing organization membership '{args.ou_id}' from team")
            client.teams.remove_organization_memberships(team_id, [args.ou_id])
            after_ou2 = client.teams.list_organization_memberships(team_id)
            print(f"team now has {len(after_ou2)} organization memberships")

        if not args.username and not args.ou_id:
            print(
                "\n(read-only demo — pass --username or --ou-id to exercise "
                "add/remove)"
            )

        return 0
    finally:
        if created_team_id:
            try:
                client.teams.delete(created_team_id)
                print(f"cleaned up team {created_team_id}")
            except Exception as e:
                print(f"WARN: could not clean up team: {e}")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
