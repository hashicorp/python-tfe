# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Terraform Cloud/Enterprise Stack Deployments Example

Lists the deployments that belong to a Stack
(GET /stacks/:stack_id/stack-deployments).

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - A Stack id (e.g. st-xxxxxxxx)

Usage:
    python examples/stack_deployment.py --stack-id st-xxxxxxxx
    python examples/stack_deployment.py --stack-id st-xxxxxxxx --page-size 50
    python examples/stack_deployment.py --stack-id st-xxxxxxxx --include-latest-run
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    StackDeploymentIncludeOpt,
    StackDeploymentListOptions,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stack Deployments demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--stack-id", required=True, help="Stack ID (e.g. st-xxxxxxxx)"
    )
    parser.add_argument(
        "--page-size", type=int, default=20, help="Page size for listing deployments"
    )
    parser.add_argument(
        "--include-latest-run",
        action="store_true",
        help="Request the latest_deployment_run related resource",
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    include = (
        [StackDeploymentIncludeOpt.LATEST_DEPLOYMENT_RUN]
        if args.include_latest_run
        else None
    )
    options = StackDeploymentListOptions(page_size=args.page_size, include=include)

    _print_header(f"Listing deployments for stack {args.stack_id}")
    for deployment in client.stack_deployments.list(args.stack_id, options):
        print(f"  - {deployment.id}  {deployment.name}")
        if deployment.stack:
            print(f"      stack: {deployment.stack.id}")
        # The latest-deployment-run relation is not modelled as a typed field,
        # but it is always reachable losslessly via the raw escape hatch.
        for ref in deployment.related("latest-deployment-run"):
            print(f"      latest-deployment-run: {ref.get('id')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
