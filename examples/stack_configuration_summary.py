#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list stack configuration summaries for a stack.

Usage::

    export TFE_TOKEN=<your-token>

    # List configuration summaries for a stack
    python3 examples/stack_configuration_summary.py --stack-id st-abc123

    # List with pagination
    python3 examples/stack_configuration_summary.py --stack-id st-abc123 --page-size 10
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import StackConfigurationSummaryListOptions


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="List stack configuration summaries")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument("--stack-id", required=True, help="Stack ID (e.g. st-abc123)")
    parser.add_argument("--page-size", type=int, help="Max items per page")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("TFE_TOKEN is not set")

    client = TFEClient(config=TFEConfig(token=args.token, address=args.address))

    _print_header(f"Stack Configuration Summaries for {args.stack_id}")
    opts = (
        StackConfigurationSummaryListOptions(page_size=args.page_size)
        if args.page_size
        else None
    )
    count = 0
    for summary in client.stack_configuration_summaries.list(
        args.stack_id, options=opts
    ):
        count += 1
        print(f"  {summary.id}  seq={summary.sequence_number}  status={summary.status}")
        if summary.group_status_summary:
            g = summary.group_status_summary
            print(
                f"    groups: pending={g.pending} deploying={g.deploying} "
                f"succeeded={g.succeeded} failed={g.failed} abandoned={g.abandoned}"
            )
        if summary.run_status_summary:
            r = summary.run_status_summary
            print(
                f"    runs: succeeded={r.succeeded} failed={r.failed} "
                f"deploying={r.deploying} pending={r.pending}"
            )
    print(f"\nTotal: {count} configuration summary/summaries")


if __name__ == "__main__":
    main()
