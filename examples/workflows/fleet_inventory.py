# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Fleet inventory and bulk changes using pytfe.workflows

Answers the questions that need every workspace at once: what is drifted, what
is locked, what Terraform versions are in use, where a resource type is
deployed, and what a settings change would do before you make it.

Prerequisites:
    - TFE_TOKEN   API token
    - TFE_ADDRESS (optional) defaults to https://app.terraform.io

Quick Start:
    python examples/workflows/fleet_inventory.py --help

1. Health of every workspace, as a table:
    python examples/workflows/fleet_inventory.py --org my-org

2. Same, as CSV:
    python examples/workflows/fleet_inventory.py --org my-org --csv

3. Where is a resource type deployed?
    python examples/workflows/fleet_inventory.py --org my-org \\
        --resources --resource-type aws_s3_bucket

4. Preview a fleet-wide Terraform version bump (writes nothing):
    python examples/workflows/fleet_inventory.py --org my-org \\
        --set-terraform-version 1.9.5 --match "prod-*"

5. Apply it (a human has approved):
    python examples/workflows/fleet_inventory.py --org my-org \\
        --set-terraform-version 1.9.5 --match "prod-*" --confirmed

6. Audit tokens for anything expiring soon:
    python examples/workflows/fleet_inventory.py --org my-org --tokens
"""

from __future__ import annotations

import argparse
import os
import sys

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.workflows import (
    WorkspaceFilter,
    WorkspaceSpec,
    bulk_update,
    org_inventory,
    resource_inventory,
    token_audit,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fleet inventory demo for the python-tfe workflows layer"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--match", help="Only workspaces matching this glob")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--csv", action="store_true", help="Emit CSV")
    parser.add_argument(
        "--resources", action="store_true", help="Inventory managed resources"
    )
    parser.add_argument("--resource-type", help="Filter resources by type")
    parser.add_argument("--tokens", action="store_true", help="Audit API tokens")
    parser.add_argument(
        "--set-terraform-version", help="Converge every match onto this version"
    )
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Assert a human approved the fleet-wide write",
    )
    args = parser.parse_args()

    selector: WorkspaceFilter = {}
    if args.match:
        selector["name_pattern"] = args.match

    # A read-only client unless the run is explicitly making a change.
    read_only = args.set_terraform_version is None
    config = TFEConfig(
        address=args.address,
        token=args.token,
        read_only=read_only,
        user_agent_suffix="pytfe-workflows-example/1.0",
    )

    with TFEClient(config) as tfe:
        try:
            if args.tokens:
                _print_header("Token audit")
                audit = token_audit(tfe, args.org)
                for row in audit.tokens:
                    flag = (
                        "EXPIRED"
                        if row.expired
                        else ("expiring" if row.expiring else "ok")
                    )
                    print(f"  {row.kind:13} {row.id or '-':22} {flag}")
                for warning in audit.warnings:
                    print(f"  note: {warning}")
                return 0

            if args.resources:
                _print_header("Resource inventory")
                inventory = resource_inventory(
                    tfe,
                    args.org,
                    resource_type=args.resource_type,
                    filter=selector,
                    concurrency=args.concurrency,
                )
                for workspace, count in sorted(inventory.by_workspace.items()):
                    print(f"  {workspace:40} {count:>5}")
                if inventory.truncated:
                    print("  (truncated)")
                return 0

            if args.set_terraform_version:
                _print_header(
                    "Preview" if not args.confirmed else "Applying fleet update"
                )
                fleet = bulk_update(
                    tfe,
                    args.org,
                    spec=WorkspaceSpec(terraform_version=args.set_terraform_version),
                    filter=selector,
                    dry_run=not args.confirmed,
                    confirmed=args.confirmed,
                    concurrency=args.concurrency,
                )
                for item in fleet.items:
                    if item.error:
                        print(
                            f"  {item.workspace.name:40} ERROR {item.error['message']}"
                        )
                    else:
                        print(f"  {item.workspace.name:40} {item.result.action}")
                for warning in fleet.warnings:
                    print(f"  note: {warning}")
                print(f"\n{fleet}")
                return 0 if fleet.ok else 1

            _print_header(f"Workspace health in {args.org}")
            inventory = org_inventory(
                tfe, args.org, filter=selector, concurrency=args.concurrency
            )
            if args.csv:
                print(inventory.to_csv())
            else:
                for row in inventory.rows:
                    print(
                        f"  {row.name:40} {row.health:10} "
                        f"{row.terraform_version or '-':10} "
                        f"{row.resource_count if row.resource_count is not None else '-'}"
                    )
                print(f"\n  by version: {inventory.by_terraform_version}")
                if inventory.errored:
                    print(f"  errored:    {', '.join(inventory.errored)}")
                if inventory.drifted:
                    print(f"  drifted:    {', '.join(inventory.drifted)}")
                if inventory.locked:
                    print(f"  locked:     {', '.join(inventory.locked)}")
            for warning in inventory.warnings:
                print(f"  note: {warning}")

        except TFEError as exc:
            print(f"\nerror: {exc}", file=sys.stderr)
            if exc.hint:
                print(f"hint:  {exc.hint}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
