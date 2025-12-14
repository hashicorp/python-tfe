from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Applies demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--apply-id", required=True, help="Apply ID to work with")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Read the apply details
    _print_header("Reading Apply Details")
    try:
        apply = client.applies.read(args.apply_id)
        print(f"Apply ID: {apply.id}")
        print(f"Status: {apply.status}")
        print(f"Resource Additions: {apply.resource_additions}")
        print(f"Resource Changes: {apply.resource_changes}")
        print(f"Resource Destructions: {apply.resource_destructions}")
        print(f"Resource Imports: {apply.resource_imports}")
        print(f"Status Timestamps: {apply.status_timestamps}")
        print(f"Log Read URL: {apply.log_read_url}")

        # Display timestamp details if available
        if apply.status_timestamps:
            print(f"Queued At: {apply.status_timestamps.queued_at}")
            print(f"Started At: {apply.status_timestamps.started_at}")
            print(f"Finished At: {apply.status_timestamps.finished_at}")
    except Exception as e:
        print(f"Error reading apply: {e}")
        return 1

    print("\n" + "=" * 80)
    print("Apply demo completed successfully!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    exit(main())
