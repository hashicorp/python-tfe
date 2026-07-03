#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list, read, approve, and rerun stack deployment groups.

Usage::

    export TFE_TOKEN=<your-token>

    # List deployment groups in a stack configuration
    python3 examples/stack_deployment_group.py \\
        --stack-config-id stc-abc123

    # Read a specific group by ID
    python3 examples/stack_deployment_group.py \\
        --stack-config-id stc-abc123 --read --group-id sdg-xyz789

    # Read a group by deployment name
    python3 examples/stack_deployment_group.py \\
        --stack-config-id stc-abc123 --read-by-name dev

    # Approve all plans in a group
    python3 examples/stack_deployment_group.py \\
        --stack-config-id stc-abc123 --approve --group-id sdg-xyz789

    # Rerun a failed deployment group (pass deployment names, not run IDs)
    python3 examples/stack_deployment_group.py \\
        --stack-config-id stc-abc123 --rerun --group-id sdg-xyz789 \\
        --deployments dev prod
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    StackDeploymentGroupListOptions,
    StackDeploymentGroupRerunOptions,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage stack deployment groups")
    parser.add_argument("--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io"))
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument("--stack-config-id", required=True, help="Stack configuration ID (stc-...)")
    parser.add_argument("--group-id", help="Deployment group ID (sdg-...)")
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--read", action="store_true", help="Read a specific group (requires --group-id)")
    parser.add_argument("--read-by-name", metavar="NAME", help="Read a group by deployment name")
    parser.add_argument("--approve", action="store_true", help="Approve all plans (requires --group-id)")
    parser.add_argument("--rerun", action="store_true", help="Rerun a failed group (requires --group-id and --deployments)")
    parser.add_argument("--deployments", nargs="+", metavar="NAME", help="Deployment names to rerun, e.g. dev prod (from the 'deployment' field on runs)")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List deployment groups in the stack configuration
    _print_header(f"Listing deployment groups for config: {args.stack_config_id}")
    opts = StackDeploymentGroupListOptions(page_size=args.page_size)
    count = 0
    for group in client.stack_deployment_groups.list(args.stack_config_id, options=opts):
        count += 1
        print(f"- {group.id}")
        print(f"  Name:    {group.name}")
        print(f"  Status:  {group.status.value if group.status else None}")
        print(f"  Created: {group.created_at}")
        print(f"  Updated: {group.updated_at}")
        if group.stack_configuration:
            print(f"  Config:  {group.stack_configuration.id}")
        print()
    print(f"Total: {count} deployment group(s)")

    # 2) Read a specific group by ID
    if args.read:
        if not args.group_id:
            print("--group-id is required for --read")
        else:
            _print_header(f"Reading deployment group: {args.group_id}")
            group = client.stack_deployment_groups.read(args.group_id)
            print(f"ID:      {group.id}")
            print(f"Name:    {group.name}")
            print(f"Status:  {group.status.value if group.status else None}")
            print(f"Created: {group.created_at}")
            print(f"Updated: {group.updated_at}")

    # 3) Read a group by deployment name
    if args.read_by_name:
        _print_header(f"Reading deployment group by name: {args.read_by_name!r}")
        group = client.stack_deployment_groups.read_by_name(
            args.stack_config_id, args.read_by_name
        )
        print(f"ID:      {group.id}")
        print(f"Name:    {group.name}")
        print(f"Status:  {group.status.value if group.status else None}")

    # 4) Approve all plans
    if args.approve:
        if not args.group_id:
            print("--group-id is required for --approve")
        else:
            _print_header(f"Approving all plans for group: {args.group_id}")
            client.stack_deployment_groups.approve_all_plans(args.group_id)
            print(f"Approved {args.group_id}")

    # 5) Rerun a failed deployment group
    if args.rerun:
        if not args.group_id or not args.deployments:
            print("--group-id and --deployments are required for --rerun")
        else:
            _print_header(f"Rerunning {len(args.deployments)} deployment(s) in group: {args.group_id}")
            rerun_opts = StackDeploymentGroupRerunOptions(deployments=args.deployments)
            client.stack_deployment_groups.rerun(args.group_id, rerun_opts)
            print(f"Rerun triggered for: {', '.join(args.deployments)}")


if __name__ == "__main__":
    main()
