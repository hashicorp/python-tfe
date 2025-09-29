"""Run Events Example for python-tfe SDK

This example demonstrates how to work with run events using the python-tfe SDK.
Run events represent activities that happen during a run's lifecycle, such as:
- Run state changes (queued, planning, planned, etc.)
- User actions (approve, discard, cancel)
- System events (plan finished, apply started, etc.)

Features demonstrated:
1. Listing all run events for a specific run
2. Reading individual run event details
3. Including related data (actor, comment) in responses
4. Error handling and proper client configuration

Usage examples:
  # List all events for a run
  python examples/run_events.py --run-id run-abc123

  # List events with actor and comment information included
  python examples/run_events.py --run-id run-abc123 --include-actor --include-comment

  # Read a specific run event
  python examples/run_events.py --run-id run-abc123 --event-id re-xyz789

Environment variables:
  TFE_ADDRESS: Terraform Enterprise/Cloud address (default: https://app.terraform.io)
  TFE_TOKEN: API token for authentication (required)

Requirements:
  - Valid TFE API token with appropriate permissions
  - Valid run ID (from an existing run in your organization)
  - Optional: Valid run event ID for detailed reading
"""

from __future__ import annotations

import argparse
import os

from tfe import TFEClient, TFEConfig
from tfe.models.run_event import (
    RunEventIncludeOpt,
    RunEventListOptions,
    RunEventReadOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Run Events demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--run-id", required=True, help="Run ID to list events for")
    parser.add_argument("--event-id", help="Specific Run Event ID to read")
    parser.add_argument(
        "--include-actor",
        action="store_true",
        help="Include actor information in the response",
    )
    parser.add_argument(
        "--include-comment",
        action="store_true",
        help="Include comment information in the response",
    )
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument is required")
        return 1

    # Configure the client
    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # Build include options if requested
    include_opts = []
    if args.include_actor:
        include_opts.append(RunEventIncludeOpt.RUN_EVENT_ACTOR)
    if args.include_comment:
        include_opts.append(RunEventIncludeOpt.RUN_EVENT_COMMENT)

    # 1) List run events for the specified run
    _print_header(f"Listing Run Events for Run: {args.run_id}")

    options = RunEventListOptions(include=include_opts if include_opts else None)

    try:
        event_list = client.run_events.list(args.run_id, options)

        print(f"Total run events: {event_list.total_count or 'N/A'}")
        if event_list.current_page and event_list.total_pages:
            print(f"Page {event_list.current_page} of {event_list.total_pages}")
        print()

        if not event_list.items:
            print("No run events found for this run.")
        else:
            for event in event_list.items:
                print(f"Event ID: {event.id}")
                print(f"  Action: {event.action or 'N/A'}")
                print(f"  Description: {event.description or 'N/A'}")
                print(f"  Created At: {event.created_at or 'N/A'}")

                print()

    except Exception as e:
        print(f"Error listing run events: {e}")
        return 1

    # 2) Read a specific run event if provided
    if args.event_id:
        _print_header(f"Reading Run Event: {args.event_id}")

        read_options = RunEventReadOptions(
            include=include_opts if include_opts else None
        )

        try:
            event = client.run_events.read_with_options(args.event_id, read_options)

            print(f"Event ID: {event.id}")
            print(f"Action: {event.action or 'N/A'}")
            print(f"Description: {event.description or 'N/A'}")
            print(f"Created At: {event.created_at or 'N/A'}")

        except Exception as e:
            print(f"Error reading run event: {e}")
            return 1

    # 3) Summary
    _print_header("Summary")
    print(f"Successfully demonstrated run events for run: {args.run_id}")
    print(f"Total events found: {event_list.total_count or 'N/A'}")
    if args.event_id:
        print(f"Successfully read specific event: {args.event_id}")
    return 0


if __name__ == "__main__":
    exit(main())
