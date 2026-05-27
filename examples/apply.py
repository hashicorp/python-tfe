# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

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
    parser.add_argument(
        "--recover-errored-state",
        action="store_true",
        help="Fetch the failed-upload state via /applies/{id}/errored-state",
    )
    parser.add_argument(
        "--out",
        help="When recovering errored state, write the bytes to this path",
    )
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

    if args.recover_errored_state:
        from pytfe.errors import NotFound

        _print_header("Recovering errored state (GET /applies/{id}/errored-state)")
        try:
            data = client.applies.errored_state(args.apply_id)
        except NotFound:
            print(
                "No errored state available — apply did not fail during state "
                "upload, or storage retention has elapsed."
            )
        else:
            print(f"Recovered {len(data)} bytes of errored state")
            if args.out:
                with open(args.out, "wb") as f:
                    f.write(data)
                print(f"Wrote {args.out}")
            else:
                preview = data[:256].decode("utf-8", errors="replace")
                print(f"--- preview ---\n{preview}\n--- end preview ---")

    print("\n" + "=" * 80)
    print("Apply demo completed successfully!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    exit(main())
