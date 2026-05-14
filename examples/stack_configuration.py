# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    StackConfigurationCreateOptions,
    StackConfigurationListOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Stack Configurations demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--stack-id", required=True, help="Stack ID (e.g. st-xxxxx)")
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for listing configurations",
    )
    parser.add_argument(
        "--create", action="store_true", help="Create a new stack configuration"
    )
    parser.add_argument(
        "--speculative",
        action="store_true",
        help="Mark created configuration as speculative",
    )
    parser.add_argument(
        "--read", action="store_true", help="Read a specific stack configuration"
    )
    parser.add_argument(
        "--upload-url",
        action="store_true",
        help="Fetch the upload URL for a stack configuration",
    )
    parser.add_argument(
        "--fetch-from-vcs",
        action="store_true",
        help="Trigger fetch of latest config from VCS",
    )
    parser.add_argument("--id", help="Stack configuration ID (e.g. stc-xxxxx)")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Always list existing stack configurations
    _print_header(f"Listing stack configurations for stack: {args.stack_id}")
    options = StackConfigurationListOptions(page_size=args.page_size)
    config_count = 0
    for config in client.stack_configurations.list(
        stack_id=args.stack_id, options=options
    ):
        config_count += 1
        print(f"- ID: {config.id}")
        print(f"  Status: {config.status.value if config.status else None}")
        print(f"  Sequence: {config.sequence_number}")
        print(f"  Speculative: {config.speculative}")
        print(f"  Created: {config.created_at}")
        print(f"  Updated: {config.updated_at}")
        print()

    if config_count == 0:
        print("No stack configurations found.")
    else:
        print(f"Total: {config_count} stack configurations")

    # 2) Create a new stack configuration
    if args.create:
        _print_header("Creating a new stack configuration")
        create_opts = StackConfigurationCreateOptions(
            speculative_enabled=args.speculative
        )
        config = client.stack_configurations.create(
            stack_id=args.stack_id, options=create_opts
        )
        print(f"Created stack configuration: {config.id}")
        print(f"  Status: {config.status.value if config.status else None}")
        print(f"  Speculative: {config.speculative}")
        print(f"  Sequence: {config.sequence_number}")
        print(f"  Created: {config.created_at}")

    # 3) Read a specific stack configuration
    if args.read:
        if not args.id:
            print("--id is required for --read")
        else:
            _print_header(f"Reading stack configuration: {args.id}")
            config = client.stack_configurations.read(stack_configuration_id=args.id)
            print(f"ID: {config.id}")
            print(f"Status: {config.status.value if config.status else None}")
            print(f"Sequence: {config.sequence_number}")
            print(f"Speculative: {config.speculative}")
            print(f"Created: {config.created_at}")
            print(f"Updated: {config.updated_at}")


if __name__ == "__main__":
    main()
