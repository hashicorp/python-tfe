# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Billing demo (subscriptions + invoices) for the python-tfe SDK.

Both APIs are HCP Terraform only and read-only.
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="Billing demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    _print_header(f"Subscription for {args.organization}")
    sub = client.subscriptions.read_for_organization(args.organization)
    print(f"  id:          {sub.id}")
    print(f"  active:      {sub.is_active}")
    print(f"  start_at:    {sub.start_at}")
    print(f"  runs_ceiling: {sub.runs_ceiling}  agents_ceiling: {sub.agents_ceiling}")
    print(f"  feature_set: {sub.feature_set_id}")
    fs = sub.related("feature-set")
    if fs and fs[0].get("attributes"):
        print(f"  feature_set name: {fs[0]['attributes'].get('name')}")

    _print_header(f"Invoices for {args.organization}")
    count = 0
    for inv in client.invoices.list(args.organization):
        count += 1
        print(
            f"  - {inv.number or inv.id}  status={inv.status}  total={inv.total}  paid={inv.paid}"
        )
    if count == 0:
        print("  (no previous invoices)")

    _print_header("Next (upcoming) invoice")
    nxt = client.invoices.read_next(args.organization)
    if nxt is None:
        print("  (no upcoming invoice / not on a credit-card-billed plan)")
    else:
        print(f"  {nxt.number or nxt.id}  status={nxt.status}  total={nxt.total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
