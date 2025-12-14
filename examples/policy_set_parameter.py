from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    PolicySetParameterCreateOptions,
    PolicySetParameterListOptions,
    PolicySetParameterUpdateOptions,
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
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for fetching parameters",
    )
    parser.add_argument("--create", action="store_true", help="Create a test parameter")
    parser.add_argument("--read", action="store_true", help="Read a specific parameter")
    parser.add_argument("--update", action="store_true", help="Update a parameter")
    parser.add_argument("--delete", action="store_true", help="Delete a parameter")
    parser.add_argument(
        "--parameter-id", help="Parameter ID for read/update/delete operation"
    )
    parser.add_argument("--key", help="Parameter key for creation/update")
    parser.add_argument("--value", help="Parameter value for creation/update")
    parser.add_argument(
        "--sensitive", action="store_true", help="Mark parameter as sensitive"
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List all parameters for the policy set
    _print_header(f"Listing parameters for policy set: {args.policy_set_id}")

    options = PolicySetParameterListOptions(
        page_size=args.page_size,
    )

    param_count = 0
    for param in client.policy_set_parameters.list(args.policy_set_id, options):
        param_count += 1
        # Sensitive parameters will have masked values
        value_display = "***SENSITIVE***" if param.sensitive else param.value
        print(f"- {param.id}")
        print(f"Key: {param.key}")
        print(f"Value: {value_display}")
        print(f"Category: {param.category.value}")
        print(f"Sensitive: {param.sensitive}")
        print()

    if param_count == 0:
        print("No parameters found.")
    else:
        print(f"Total: {param_count} parameters")

    # 2) Read a specific parameter (if --read flag is provided)
    if args.read:
        if not args.parameter_id:
            print("Error: --parameter-id is required for read operation")
            return

        _print_header(f"Reading parameter: {args.parameter_id}")

        param = client.policy_set_parameters.read(args.policy_set_id, args.parameter_id)

        print(f"Parameter ID: {param.id}")
        print(f"Key: {param.key}")
        value_display = "***SENSITIVE***" if param.sensitive else param.value
        print(f"Value: {value_display}")
        print(f"Category: {param.category.value}")
        print(f"Sensitive: {param.sensitive}")

    # 3) Update a parameter (if --update flag is provided)
    if args.update:
        if not args.parameter_id:
            print("Error: --parameter-id is required for update operation")
            return

        _print_header(f"Updating parameter: {args.parameter_id}")

        # First read the current parameter to show before state
        current_param = client.policy_set_parameters.read(
            args.policy_set_id, args.parameter_id
        )
        print("Before update:")
        print(f"Key: {current_param.key}")
        value_display = (
            "***SENSITIVE***" if current_param.sensitive else current_param.value
        )
        print(f"Value: {value_display}")
        print(f"Sensitive: {current_param.sensitive}")

        # Update the parameter
        update_options = PolicySetParameterUpdateOptions(
            key=args.key if args.key else None,
            value=args.value if args.value else None,
            sensitive=args.sensitive if args.sensitive else None,
        )

        updated_param = client.policy_set_parameters.update(
            args.policy_set_id, args.parameter_id, update_options
        )

        print("\nAfter update:")
        print(f"Key: {updated_param.key}")
        value_display = (
            "***SENSITIVE***" if updated_param.sensitive else updated_param.value
        )
        print(f"Value: {value_display}")
        print(f"Sensitive: {updated_param.sensitive}")

    # 4) Delete a parameter (if --delete flag is provided)
    if args.delete:
        if not args.parameter_id:
            print("Error: --parameter-id is required for delete operation")
            return

        _print_header(f"Deleting parameter: {args.parameter_id}")

        # First read the parameter to show what's being deleted
        try:
            param_to_delete = client.policy_set_parameters.read(
                args.policy_set_id, args.parameter_id
            )
            print("Parameter to delete:")
            print(f"ID: {param_to_delete.id}")
            print(f"Key: {param_to_delete.key}")
            value_display = (
                "***SENSITIVE***"
                if param_to_delete.sensitive
                else param_to_delete.value
            )
            print(f"Value: {value_display}")
            print(f"Sensitive: {param_to_delete.sensitive}")
        except Exception as e:
            print(f"Error reading parameter: {e}")
            return

        # Delete the parameter
        client.policy_set_parameters.delete(args.policy_set_id, args.parameter_id)
        print(f"\n  Successfully deleted parameter: {args.parameter_id}")

        # List remaining parameters
        _print_header("Listing parameters after deletion")
        print("Remaining parameters:")
        remaining_count = 0
        for param in client.policy_set_parameters.list(args.policy_set_id):
            remaining_count += 1
            value_display = "***SENSITIVE***" if param.sensitive else param.value
            print(f"- {param.key}: {value_display} (sensitive={param.sensitive})")

        if remaining_count == 0:
            print("No parameters remaining.")
        else:
            print(f"\nTotal: {remaining_count} parameters")

    # 5) Create a new parameter (if --create flag is provided)
    if args.create:
        if not args.key:
            print("Error: --key is required for create operation")
            return

        _print_header(f"Creating new parameter with key: {args.key}")

        create_options = PolicySetParameterCreateOptions(
            key=args.key,
            value=args.value if args.value else "",
            sensitive=args.sensitive,
        )

        new_param = client.policy_set_parameters.create(
            args.policy_set_id, create_options
        )

        print(f"Created parameter: {new_param.id}")
        print(f"Key: {new_param.key}")
        value_display = "***SENSITIVE***" if new_param.sensitive else new_param.value
        print(f"Value: {value_display}")
        print(f"Category: {new_param.category.value}")
        print(f"Sensitive: {new_param.sensitive}")

        # List again to show the new parameter
        _print_header("Listing parameters after creation")
        param_count = 0
        for param in client.policy_set_parameters.list(args.policy_set_id):
            param_count += 1
            value_display = "***SENSITIVE***" if param.sensitive else param.value
            print(f"- {param.key}: {value_display} (sensitive={param.sensitive})")
        print(f"\nTotal: {param_count} parameters")


if __name__ == "__main__":
    main()
