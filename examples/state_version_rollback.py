#!/usr/bin/env python3
"""State-version rollback example.

Demonstrates ``client.state_versions.rollback(workspace_id, rollback_sv_id)``,
which duplicates a previous state version and sets the copy as the current
one. The workspace **must be locked** by the caller before rollback,
otherwise the API returns HTTP 409.

Usage::

    TFE_TOKEN=... python examples/state_version_rollback.py \\
        --workspace-id ws-XXXX \\
        --rollback-to sv-YYYY \\
        --dry-run

Without ``--dry-run`` the script will lock the workspace, perform the
rollback, then unlock.
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--workspace-id", required=True)
    p.add_argument(
        "--rollback-to",
        required=False,
        help="State version id to roll back to. If omitted, the script picks "
        "the second-newest state version.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen but do not lock/rollback/unlock.",
    )
    args = p.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    current_sv = client.state_versions.read_current(args.workspace_id)
    print(f"current state version: {current_sv.id} (serial={current_sv.serial})")

    target_id = args.rollback_to
    if target_id is None:
        from pytfe.models.state_version import StateVersionListOptions

        ws = client.workspaces.read_by_id(args.workspace_id)
        # `ws.organization` is populated as a relationship stub: its .id
        # carries the organization name.
        org_name = (
            ws.organization.name
            if ws.organization and ws.organization.name
            else (ws.organization.id if ws.organization else None)
        )
        opts = StateVersionListOptions(organization=org_name, workspace=ws.name)
        candidates = []
        for sv in client.state_versions.list(options=opts):
            candidates.append(sv)
            if len(candidates) >= 5:
                break
        target = next((c for c in candidates if c.id != current_sv.id), None)
        if target is None:
            print("no previous state version available to roll back to")
            return 1
        target_id = target.id
        print(f"selected rollback target: {target_id}")
    else:
        print(f"using explicit rollback target: {target_id}")

    if args.dry_run:
        print("--dry-run set; not locking or rolling back")
        return 0

    print(f"locking workspace {args.workspace_id} ...")
    from pytfe.models.workspace import WorkspaceLockOptions

    client.workspaces.lock(
        args.workspace_id, WorkspaceLockOptions(reason="rollback demo")
    )
    try:
        print("performing rollback ...")
        new_sv = client.state_versions.rollback(args.workspace_id, target_id)
        print(
            f"rollback succeeded — new state version: {new_sv.id} "
            f"(serial={new_sv.serial})"
        )
    finally:
        print("unlocking workspace ...")
        client.workspaces.unlock(args.workspace_id)

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
