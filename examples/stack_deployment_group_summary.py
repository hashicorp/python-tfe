#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list stack deployment group summaries for a stack configuration.

Usage::

    export TFE_TOKEN=<your-token>

    # List deployment group summaries for a configuration
    python3 examples/stack_deployment_group_summary.py --configuration-id stc-abc123

    # List with pagination
    python3 examples/stack_deployment_group_summary.py \\
        --configuration-id stc-abc123 --page-size 10
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import StackDeploymentGroupSummaryListOptions


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List stack deployment group summaries"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument(
        "--configuration-id",
        required=True,
        help="Stack configuration ID (e.g. stc-abc123)",
    )
    parser.add_argument("--page-size", type=int, help="Max items per page")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("TFE_TOKEN is not set")

    client = TFEClient(config=TFEConfig(token=args.token, address=args.address))

    _print_header(f"Deployment Group Summaries for {args.configuration_id}")
    opts = (
        StackDeploymentGroupSummaryListOptions(page_size=args.page_size)
        if args.page_size
        else None
    )
    count = 0
    for summary in client.stack_deployment_group_summaries.list(
        args.configuration_id, options=opts
    ):
        count += 1
        counts = summary.status_counts
        counts_str = ""
        if counts:
            counts_str = (
                f"  [pending={counts.pending} deploying={counts.deploying} "
                f"succeeded={counts.succeeded} failed={counts.failed}]"
            )
        print(
            f"  {summary.id}  name={summary.name}  status={summary.status}{counts_str}"
        )
    print(f"\nTotal: {count} deployment group summary/summaries")


if __name__ == "__main__":
    main()
