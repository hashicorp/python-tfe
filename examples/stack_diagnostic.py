#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: read and acknowledge stack diagnostics.

Usage::

    export TFE_TOKEN=<your-token>

    # Read a specific diagnostic
    python3 examples/stack_diagnostic.py --diagnostic-id stf-abc123

    # Acknowledge a diagnostic
    python3 examples/stack_diagnostic.py --diagnostic-id stf-abc123 --acknowledge
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage stack diagnostics")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument(
        "--diagnostic-id", required=True, help="Stack diagnostic ID (e.g. stf-abc123)"
    )
    parser.add_argument(
        "--acknowledge",
        action="store_true",
        help="Acknowledge the diagnostic after reading it",
    )
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("TFE_TOKEN is not set")

    client = TFEClient(config=TFEConfig(token=args.token, address=args.address))

    _print_header(f"Stack Diagnostic: {args.diagnostic_id}")
    diag = client.stack_diagnostics.read(args.diagnostic_id)
    print(f"  ID:             {diag.id}")
    print(f"  Severity:       {diag.severity}")
    print(f"  Summary:        {diag.summary}")
    print(f"  Detail:         {diag.detail}")
    print(f"  Acknowledged:   {diag.acknowledged}")
    print(f"  Acknowledged At:{diag.acknowledged_at}")
    print(f"  Created At:     {diag.created_at}")

    if args.acknowledge:
        if diag.acknowledged:
            print("\nDiagnostic is already acknowledged — nothing to do.")
        else:
            client.stack_diagnostics.acknowledge(args.diagnostic_id)
            print("\nDiagnostic acknowledged successfully.")


if __name__ == "__main__":
    main()
