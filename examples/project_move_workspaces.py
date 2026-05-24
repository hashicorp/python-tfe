#!/usr/bin/env python3
"""Project move-workspaces example.

Demonstrates ``client.projects.move_workspaces(project_id, workspace_ids)``.

This example, by default, creates two scratch projects and a scratch
workspace, moves the workspace from one project to the other, then deletes
the scratch resources.  To exercise against existing resources use
``--target-project-id`` and one or more ``--workspace-id`` flags.

Usage::

    TFE_TOKEN=... TFE_ORG=prab-sandbox02 python examples/project_move_workspaces.py
"""

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    ProjectCreateOptions,
    WorkspaceCreateOptions,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    p.add_argument("--target-project-id", help="If set, move into this project")
    p.add_argument(
        "--workspace-id",
        action="append",
        default=[],
        help="Workspace(s) to move (may be repeated)",
    )
    args = p.parse_args()

    if not args.token or not args.organization:
        print("set TFE_TOKEN and TFE_ORG (or pass --token / --organization)")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    created_resources: dict[str, str] = {}
    try:
        if args.target_project_id and args.workspace_id:
            # Existing-resource mode
            print(
                f"moving {args.workspace_id} into {args.target_project_id} ..."
            )
            client.projects.move_workspaces(
                args.target_project_id, args.workspace_id
            )
            print("done")
            return 0

        # Scratch mode: create source project, target project, and a workspace
        stamp = int(time.time())
        src = client.projects.create(
            args.organization,
            ProjectCreateOptions(name=f"pytfe-move-src-{stamp}"),
        )
        created_resources["src_project"] = src.id
        print(f"created source project:  {src.id} ({src.name})")

        dst = client.projects.create(
            args.organization,
            ProjectCreateOptions(name=f"pytfe-move-dst-{stamp}"),
        )
        created_resources["dst_project"] = dst.id
        print(f"created target project:  {dst.id} ({dst.name})")

        ws = client.workspaces.create(
            args.organization,
            WorkspaceCreateOptions(
                name=f"pytfe-move-ws-{stamp}",
                project={"id": src.id},  # attach to source project at creation
            ),
        )
        created_resources["workspace"] = ws.id
        print(f"created workspace:       {ws.id} ({ws.name}) in {src.id}")

        print(f"\nmoving {ws.id} into {dst.id} ...")
        client.projects.move_workspaces(dst.id, [ws.id])

        ws2 = client.workspaces.read_by_id(ws.id)
        moved_project = (
            ws2.project.id if ws2.project else "?"
        )
        print(f"workspace now belongs to project: {moved_project}")
        assert moved_project == dst.id, "workspace did not move"
        print("OK")
        return 0
    finally:
        if "workspace" in created_resources:
            try:
                client.workspaces.delete_by_id(created_resources["workspace"])
                print(f"cleaned up workspace {created_resources['workspace']}")
            except Exception as e:
                print(f"WARN: could not clean up workspace: {e}")
        for key in ("dst_project", "src_project"):
            if key in created_resources:
                try:
                    client.projects.delete(created_resources[key])
                    print(f"cleaned up project {created_resources[key]}")
                except Exception as e:
                    print(f"WARN: could not clean up project {key}: {e}")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
