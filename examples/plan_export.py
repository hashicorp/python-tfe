# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import PlanExportCreateOptions, PlanExportStatus


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Plan exports demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--plan-id",
        help="Finished plan ID to export (e.g. plan-xxxxx). Required with --create.",
    )
    parser.add_argument(
        "--create", action="store_true", help="Create a plan export from --plan-id"
    )
    parser.add_argument(
        "--id", help="Existing plan export ID (e.g. pe-xxxxx) for --read/--download"
    )
    parser.add_argument("--read", action="store_true", help="Read a plan export")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the export's .tar.gz archive",
    )
    parser.add_argument(
        "--output", default="plan-export.tar.gz", help="Path to write the archive to"
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete the plan export when done"
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    export_id = args.id

    if args.create:
        if not args.plan_id:
            print("--plan-id is required for --create")
            return 2
        _print_header(f"Creating a plan export for plan: {args.plan_id}")
        export = client.plan_exports.create(
            PlanExportCreateOptions(plan_id=args.plan_id)
        )
        export_id = export.id
        print(f"Created plan export: {export.id} (status={export.status})")

        # Poll until the export finishes (it is generated asynchronously).
        for _ in range(30):
            export = client.plan_exports.read(export_id)
            if export.status != PlanExportStatus.QUEUED:
                break
            time.sleep(1)
        print(f"Final status: {export.status}")

    if args.read:
        if not export_id:
            print("--id is required for --read")
            return 2
        _print_header(f"Reading plan export: {export_id}")
        export = client.plan_exports.read(export_id)
        print(f"ID: {export.id}")
        print(f"Data type: {export.data_type}")
        print(f"Status: {export.status}")

    if args.download:
        if not export_id:
            print("--id is required for --download")
            return 2
        _print_header(f"Downloading plan export: {export_id}")
        data = client.plan_exports.download(export_id)
        with open(args.output, "wb") as fh:
            fh.write(data)
        print(f"Wrote {len(data)} bytes to {args.output}")

    if args.delete and export_id:
        _print_header(f"Deleting plan export: {export_id}")
        client.plan_exports.delete(export_id)
        print("Deleted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
