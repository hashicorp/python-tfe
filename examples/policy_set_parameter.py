from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    PolicySetParameterCreateOptions,
    PolicySetParameterListOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Policy Set Parameters demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--policy-set-id", required=True, help="Policy Set ID")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--create", action="store_true", help="Create a test parameter")
    parser.add_argument("--read", action="store_true", help="Read a specific parameter")
    parser.add_argument("--parameter-id", help="Parameter ID for read operation")
    parser.add_argument(
        "--key", default="test_param", help="Parameter key for creation"
    )
    parser.add_argument(
        "--value", default="test_value", help="Parameter value for creation"
    )
    parser.add_argument(
        "--sensitive", action="store_true", help="Mark parameter as sensitive"
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List all parameters for the policy set
    _print_header(f"Listing parameters for policy set: {args.policy_set_id}")

    options = PolicySetParameterListOptions(
        page_number=args.page,
        page_size=args.page_size,
    )

    param_list = client.policy_set_parameters.list(args.policy_set_id, options)

    print(f"Total parameters: {param_list.total_count}")
    print(f"Page {param_list.current_page} of {param_list.total_pages}")
    print()

    if not param_list.items:
        print("No parameters found.")
    else:
        for param in param_list.items:
            # Sensitive parameters will have masked values
            value_display = "***SENSITIVE***" if param.sensitive else param.value
            print(f"- {param.id}")
            print(f"  Key: {param.key}")
            print(f"  Value: {value_display}")
            print(f"  Category: {param.category.value}")
            print(f"  Sensitive: {param.sensitive}")
            print()

    # 2) Read a specific parameter (if --read flag is provided)
    if args.read:
        if not args.parameter_id:
            print("Error: --parameter-id is required for read operation")
            return

        _print_header(f"Reading parameter: {args.parameter_id}")

        param = client.policy_set_parameters.read(args.policy_set_id, args.parameter_id)

        print(f"Parameter ID: {param.id}")
        print(f"  Key: {param.key}")
        value_display = "***SENSITIVE***" if param.sensitive else param.value
        print(f"  Value: {value_display}")
        print(f"  Category: {param.category.value}")
        print(f"  Sensitive: {param.sensitive}")

    # 3) Create a new parameter (if --create flag is provided)
    if args.create:
        _print_header(f"Creating new parameter with key: {args.key}")

        create_options = PolicySetParameterCreateOptions(
            key=args.key,
            value=args.value,
            sensitive=args.sensitive,
        )

        new_param = client.policy_set_parameters.create(
            args.policy_set_id, create_options
        )

        print(f"Created parameter: {new_param.id}")
        print(f"  Key: {new_param.key}")
        value_display = "***SENSITIVE***" if new_param.sensitive else new_param.value
        print(f"  Value: {value_display}")
        print(f"  Category: {new_param.category.value}")
        print(f"  Sensitive: {new_param.sensitive}")

        # List again to show the new parameter
        _print_header("Listing parameters after creation")
        updated_list = client.policy_set_parameters.list(args.policy_set_id)
        print(f"Total parameters: {updated_list.total_count}")
        for param in updated_list.items:
            value_display = "***SENSITIVE***" if param.sensitive else param.value
            print(f"- {param.key}: {value_display} (sensitive={param.sensitive})")


if __name__ == "__main__":
    main()
