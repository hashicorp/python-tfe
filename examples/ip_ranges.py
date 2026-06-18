# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os
from datetime import datetime

from pytfe import TFEClient, TFEConfig


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="IP ranges demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--modified-since",
        help="ISO-8601 timestamp; only fetch ranges changed since then "
        "(e.g. 2020-05-26T15:10:05).",
    )
    args = parser.parse_args()

    # The IP ranges endpoint does not require authentication.
    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    modified_since = (
        datetime.fromisoformat(args.modified_since) if args.modified_since else None
    )

    _print_header("Reading HCP Terraform / TFE IP ranges")
    ranges = client.ip_ranges.read(modified_since=modified_since)

    if ranges is None:
        print("Not modified since the supplied date.")
        return

    for name, cidrs in (
        ("API", ranges.api),
        ("Notifications", ranges.notifications),
        ("Sentinel", ranges.sentinel),
        ("VCS", ranges.vcs),
    ):
        print(f"\n{name} ({len(cidrs)} ranges):")
        for cidr in cidrs:
            print(f"  - {cidr}")


if __name__ == "__main__":
    main()
