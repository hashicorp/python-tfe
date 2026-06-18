# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""IP allowlist (CIDR range list) demo for the python-tfe SDK.

HCP Terraform's IP allowlist feature is exposed as the JSON:API
``cidr-range-lists`` and ``cidr-ranges`` resources, surfaced here as
``client.cidr_range_lists`` and ``client.cidr_ranges``.
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    CIDRRangeCreateOptions,
    CIDRRangeListCreateOptions,
    EnforcementScope,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="IP allowlists (CIDR range lists) demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create an allowlist (with --name) and add --cidr to it",
    )
    parser.add_argument("--name", help="Name for the new IP allowlist")
    parser.add_argument(
        "--cidr", help="CIDR block to add (e.g. 192.168.1.0/24), with --create"
    )
    parser.add_argument("--id", help="IP allowlist ID for --read / --delete")
    parser.add_argument("--read", action="store_true", help="Read one IP allowlist")
    parser.add_argument(
        "--delete", action="store_true", help="Delete the IP allowlist (--id)"
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    _print_header(f"Listing IP allowlists for {args.organization}")
    for crl in client.cidr_range_lists.list(args.organization):
        ranges = list(client.cidr_range_lists.list_cidr_ranges(crl.id))
        print(f"- {crl.id}  {crl.name}  scope={crl.enforcement_scope}")
        for r in ranges:
            print(f"    {r.id}  {r.cidr_block}")

    if args.create:
        if not args.name:
            print("--name is required for --create")
            return 2
        _print_header(f"Creating IP allowlist: {args.name}")
        crl = client.cidr_range_lists.create(
            args.organization,
            CIDRRangeListCreateOptions(
                name=args.name,
                enforcement_scope=EnforcementScope.SELECTED_AGENT_POOLS,
            ),
        )
        print(f"Created {crl.id}")
        if args.cidr:
            cidr = client.cidr_range_lists.add_cidr_range(
                crl.id, CIDRRangeCreateOptions(cidr_block=args.cidr)
            )
            print(f"Added CIDR range {cidr.id}: {cidr.cidr_block}")

    if args.read:
        if not args.id:
            print("--id is required for --read")
            return 2
        _print_header(f"Reading IP allowlist: {args.id}")
        crl = client.cidr_range_lists.read(args.id)
        print(f"Name: {crl.name}")
        print(f"Description: {crl.description}")
        print(f"Enforcement scope: {crl.enforcement_scope}")

    if args.delete and args.id:
        _print_header(f"Deleting IP allowlist: {args.id}")
        client.cidr_range_lists.delete(args.id)
        print("Deleted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
