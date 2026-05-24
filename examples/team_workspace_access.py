#!/usr/bin/env python3
"""Team-workspace access example.

Demonstrates the new ``client.team_workspace_accesses`` resource (the
go-tfe equivalent is ``TeamAccesses`` — ``/api/v2/team-workspaces``)::

    client.team_workspace_accesses.add(options)
    client.team_workspace_accesses.list(workspace_id)
    client.team_workspace_accesses.read(team_workspace_access_id)
    client.team_workspace_accesses.update(id, options)
    client.team_workspace_accesses.remove(id)

By default the script creates a scratch team and a scratch workspace,
grants the team read access on the workspace, escalates the grant to
``custom`` (and tweaks the per-resource permissions), then removes the
grant and tears down the scratch resources.

Usage::

    TFE_TOKEN=... TFE_ORG=prab-sandbox02 \\
        python examples/team_workspace_access.py
"""

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    TeamCreateOptions,
    TeamWorkspaceAccessAddOptions,
    TeamWorkspaceAccessType,
    TeamWorkspaceAccessUpdateOptions,
    TeamWorkspaceRunsPermission,
    TeamWorkspaceStateVersionsPermission,
    TeamWorkspaceVariablesPermission,
    WorkspaceCreateOptions,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    p.add_argument("--team-id")
    p.add_argument("--workspace-id")
    args = p.parse_args()
    if not args.token or not args.organization:
        print("set TFE_TOKEN and TFE_ORG")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    created: dict[str, str] = {}
    grant_id: str | None = None
    try:
        team_id = args.team_id
        workspace_id = args.workspace_id

        if not team_id:
            stamp = int(time.time())
            t = client.teams.create(
                args.organization,
                TeamCreateOptions(name=f"pytfe-twa-{stamp}", visibility="secret"),
            )
            created["team"] = t.id
            team_id = t.id
            print(f"created team:      {t.id} ({t.name})")

        if not workspace_id:
            stamp = int(time.time())
            ws = client.workspaces.create(
                args.organization,
                WorkspaceCreateOptions(name=f"pytfe-twa-ws-{stamp}"),
            )
            created["workspace"] = ws.id
            workspace_id = ws.id
            print(f"created workspace: {ws.id} ({ws.name})")

        print(f"\nlisting existing grants on workspace {workspace_id} ...")
        existing = list(client.team_workspace_accesses.list(workspace_id))
        print(f"  {len(existing)} existing grant(s)")
        for g in existing:
            print(f"  - {g.id} team-access={g.access}")

        print(f"\ngranting team {team_id} READ access on workspace {workspace_id}")
        grant = client.team_workspace_accesses.add(
            TeamWorkspaceAccessAddOptions(
                team_id=team_id,
                workspace_id=workspace_id,
                access=TeamWorkspaceAccessType.READ,
            )
        )
        grant_id = grant.id
        print(f"  created grant {grant.id} access={grant.access}")

        print("\nreading grant back")
        readback = client.team_workspace_accesses.read(grant.id)
        print(f"  access={readback.access}")

        print("\nupgrading grant to CUSTOM (apply runs + write vars + write state)")
        updated = client.team_workspace_accesses.update(
            grant.id,
            TeamWorkspaceAccessUpdateOptions(
                access=TeamWorkspaceAccessType.CUSTOM,
                runs=TeamWorkspaceRunsPermission.APPLY,
                variables=TeamWorkspaceVariablesPermission.WRITE,
                state_versions=TeamWorkspaceStateVersionsPermission.WRITE,
                workspace_locking=True,
            ),
        )
        print(
            f"  access={updated.access} runs={updated.runs} "
            f"variables={updated.variables} state_versions={updated.state_versions} "
            f"workspace_locking={updated.workspace_locking}"
        )

        return 0
    finally:
        if grant_id:
            try:
                client.team_workspace_accesses.remove(grant_id)
                print(f"cleaned up grant {grant_id}")
            except Exception as e:
                print(f"WARN: could not remove grant: {e}")
        if "workspace" in created:
            try:
                client.workspaces.delete_by_id(created["workspace"])
                print(f"cleaned up workspace {created['workspace']}")
            except Exception as e:
                print(f"WARN: could not clean up workspace: {e}")
        if "team" in created:
            try:
                client.teams.delete(created["team"])
                print(f"cleaned up team {created['team']}")
            except Exception as e:
                print(f"WARN: could not clean up team: {e}")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
