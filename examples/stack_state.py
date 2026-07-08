#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list, read, and download descriptions for stack states.

Usage::

    export TFE_TOKEN=<your-token>

    # List states for a stack
    python3 examples/stack_state.py --stack-id st-abc123

    # List with pagination
    python3 examples/stack_state.py --stack-id st-abc123 --page-size 5

    # Read a specific state
    python3 examples/stack_state.py --stack-id st-abc123 --read --state-id ss-xyz789

    # Download description for a state (prints to stdout)
    python3 examples/stack_state.py --stack-id st-abc123 --description --state-id ss-xyz789

    # Download description and save to a file
    python3 examples/stack_state.py \\
        --stack-id st-abc123 --description --state-id ss-xyz789 \\
        --output-file /tmp/state-description.txt
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import StackStateListOptions


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage stack states")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument("--stack-id", required=True, help="Stack ID (e.g. st-abc123)")
    parser.add_argument("--state-id", help="Stack state ID (e.g. ss-abc123)")
    parser.add_argument("--page-size", type=int, help="Max items per page")
    parser.add_argument(
        "--read",
        action="store_true",
        help="Read a specific state (requires --state-id)",
    )
    parser.add_argument(
        "--description",
        action="store_true",
        help="Download the description for a state (requires --state-id)",
    )
    parser.add_argument(
        "--output-file", help="Write description bytes to this file instead of stdout"
    )
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("TFE_TOKEN is not set")

    client = TFEClient(config=TFEConfig(token=args.token, address=args.address))

    if args.read:
        if not args.state_id:
            raise SystemExit("--state-id is required with --read")
        _print_header(f"Stack State: {args.state_id}")
        state = client.stack_states.read(args.state_id)
        print(f"  ID:                      {state.id}")
        print(f"  Generation:              {state.generation}")
        print(f"  Status:                  {state.status}")
        print(f"  Deployment:              {state.deployment}")
        print(f"  Is Current:              {state.is_current}")
        print(f"  Resource Instance Count: {state.resource_instance_count}")
        return

    if args.description:
        if not args.state_id:
            raise SystemExit("--state-id is required with --description")
        _print_header(f"State Description: {args.state_id}")
        content = client.stack_states.download_description(args.state_id)
        if args.output_file:
            with open(args.output_file, "wb") as f:
                f.write(content)
            print(f"  Written {len(content)} bytes to {args.output_file}")
        else:
            print(content.decode("utf-8", errors="replace"))
        return

    # Default: list all states for the stack
    _print_header(f"Stack States for {args.stack_id}")
    opts = StackStateListOptions(page_size=args.page_size) if args.page_size else None
    count = 0
    for state in client.stack_states.list(args.stack_id, options=opts):
        count += 1
        current_marker = " (current)" if state.is_current else ""
        print(
            f"  {state.id}  gen={state.generation}  "
            f"status={state.status}  deployment={state.deployment}"
            f"  resources={state.resource_instance_count}{current_marker}"
        )
    print(f"\nTotal: {count} state(s)")


if __name__ == "__main__":
    main()
