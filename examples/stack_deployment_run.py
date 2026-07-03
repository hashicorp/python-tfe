#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list, read, approve, and cancel stack deployment runs.

Usage::

    export TFE_TOKEN=<your-token>

    # List runs in a deployment group
    python3 examples/stack_deployment_run.py \\
        --group-id sdg-xyz789

    # Read a single run
    python3 examples/stack_deployment_run.py \\
        --group-id sdg-xyz789 --read --run-id sdr-abc123

    # Approve all plans in a run that is pending-operator
    python3 examples/stack_deployment_run.py \\
        --group-id sdg-xyz789 --approve --run-id sdr-abc123

    # Cancel a run
    python3 examples/stack_deployment_run.py \\
        --group-id sdg-xyz789 --cancel --run-id sdr-abc123
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    StackDeploymentRunIncludeOpt,
    StackDeploymentRunListOptions,
    StackDeploymentRunReadOptions,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage stack deployment runs")
    parser.add_argument("--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io"))
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument("--group-id", required=True, help="Deployment group ID (sdg-...)")
    parser.add_argument("--run-id", help="Deployment run ID (sdr-...)")
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--include-group", action="store_true", help="Include stack-deployment-group relation")
    parser.add_argument("--read", action="store_true", help="Read a specific run (requires --run-id)")
    parser.add_argument("--approve", action="store_true", help="Approve all plans (requires --run-id)")
    parser.add_argument("--cancel", action="store_true", help="Cancel a run (requires --run-id)")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List deployment runs in the group
    _print_header(f"Listing deployment runs for group: {args.group_id}")
    include = [StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP] if args.include_group else None
    opts = StackDeploymentRunListOptions(page_size=args.page_size, include=include)
    count = 0
    for run in client.stack_deployment_runs.list(args.group_id, options=opts):
        count += 1
        print(f"- {run.id}")
        print(f"  Status:  {run.status.value if run.status else None}")
        print(f"  Created: {run.created_at}")
        print(f"  Updated: {run.updated_at}")
        if run.stack_deployment_group:
            print(f"  Group:   {run.stack_deployment_group.id}")
        print()
    print(f"Total: {count} deployment run(s)")

    # 2) Read a specific run
    if args.read:
        if not args.run_id:
            print("--run-id is required for --read")
        else:
            _print_header(f"Reading deployment run: {args.run_id}")
            read_opts = StackDeploymentRunReadOptions(
                include=[StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP] if args.include_group else None
            )
            run = client.stack_deployment_runs.read(args.run_id, options=read_opts)
            print(f"ID:      {run.id}")
            print(f"Status:  {run.status.value if run.status else None}")
            print(f"Created: {run.created_at}")
            print(f"Updated: {run.updated_at}")

    # 3) Approve all plans
    if args.approve:
        if not args.run_id:
            print("--run-id is required for --approve")
        else:
            _print_header(f"Approving all plans for run: {args.run_id}")
            client.stack_deployment_runs.approve_all_plans(args.run_id)
            print(f"Approved {args.run_id}")

    # 4) Cancel a run
    if args.cancel:
        if not args.run_id:
            print("--run-id is required for --cancel")
        else:
            _print_header(f"Cancelling run: {args.run_id}")
            client.stack_deployment_runs.cancel(args.run_id)
            print(f"Cancelled {args.run_id}")


if __name__ == "__main__":
    main()
