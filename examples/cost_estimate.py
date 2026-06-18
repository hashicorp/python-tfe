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
    parser = argparse.ArgumentParser(
        description="Cost estimates demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--cost-estimate-id", help="Cost estimate ID to read (e.g. ce-xxxxx)"
    )
    parser.add_argument(
        "--run-id",
        help="Run ID to discover the cost estimate from (e.g. run-xxxxx)",
    )
    parser.add_argument(
        "--logs", action="store_true", help="Also print the cost estimate logs"
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    ce_id = args.cost_estimate_id

    # Cost estimates have no list endpoint; the ID lives on a run's
    # relationships.cost-estimate. Look it up when only a run ID is given.
    if not ce_id and args.run_id:
        _print_header(f"Discovering cost estimate from run: {args.run_id}")
        run = client.runs.read(args.run_id)
        if run.cost_estimate and run.cost_estimate.id:
            ce_id = run.cost_estimate.id
            print(f"Found cost estimate: {ce_id}")
        else:
            print("This run has no cost estimate.")
            return 0

    if not ce_id:
        print("Provide --cost-estimate-id or --run-id")
        return 2

    _print_header(f"Reading cost estimate: {ce_id}")
    ce = client.cost_estimates.read(ce_id)
    print(f"ID: {ce.id}")
    print(f"Status: {ce.status}")
    print(
        f"Resources: {ce.resources_count} "
        f"(matched={ce.matched_resources_count}, "
        f"unmatched={ce.unmatched_resources_count})"
    )
    print(f"Prior monthly cost:    {ce.prior_monthly_cost}")
    print(f"Proposed monthly cost: {ce.proposed_monthly_cost}")
    print(f"Delta monthly cost:    {ce.delta_monthly_cost}")
    if ce.error_message:
        print(f"Error: {ce.error_message}")

    if args.logs:
        _print_header(f"Cost estimate logs: {ce_id}")
        print(client.cost_estimates.logs(ce_id) or "(no log output yet)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
