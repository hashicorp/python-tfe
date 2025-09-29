from __future__ import annotations

import argparse
import json
import os

from tfe import TFEClient, TFEConfig


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Plans demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--plan-id", required=True, help="Plan ID to work with")
    parser.add_argument("--save-json", help="Path to save JSON output")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Read the plan details
    _print_header("Reading Plan Details")
    try:
        plan = client.plans.read(args.plan_id)
        print(f"Plan ID: {plan.id}")
        print(f"Status: {plan.status}")
        print(f"Has Changes: {plan.has_changes}")
        print(f"Resource Additions: {plan.resource_additions}")
        print(f"Resource Changes: {plan.resource_changes}")
        print(f"Resource Destructions: {plan.resource_destructions}")
        print(f"Resource Imports: {plan.resource_imports}")
        print(f"Status Timestamps: {plan.status_timestamps}")
        print(f"Log Read URL: {plan.log_read_url}")
    except Exception as e:
        print(f"Error reading plan: {e}")
        return 1

    # 2) Get JSON output if the plan has it
    _print_header("Reading JSON Output")
    try:
        json_output = client.plans.read_json_output(args.plan_id)
        print(
            f"JSON Output Keys: {list(json_output.keys()) if isinstance(json_output, dict) else 'Not a dict'}"
        )

        if isinstance(json_output, dict):
            # Print some key information from the JSON output
            if "format_version" in json_output:
                print(f"Format Version: {json_output['format_version']}")
            if "terraform_version" in json_output:
                print(f"Terraform Version: {json_output['terraform_version']}")
            if "resource_changes" in json_output:
                changes = json_output["resource_changes"]
                print(f"Number of Resource Changes: {len(changes) if changes else 0}")

                # Show first few resource changes
                if changes:
                    print("\nFirst few resource changes:")
                    for i, change in enumerate(changes[:3]):
                        action = change.get("change", {}).get("actions", [])
                        address = change.get("address", "unknown")
                        print(f"  {i + 1}. {address}: {action}")

        # Save JSON output if requested
        if args.save_json:
            with open(args.save_json, "w") as f:
                json.dump(json_output, f, indent=2, default=str)
            print(f"\nJSON output saved to: {args.save_json}")

    except Exception as e:
        print(f"Error reading JSON output: {e}")

    print("\n" + "=" * 80)
    print("Plan demo completed successfully!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    exit(main())
