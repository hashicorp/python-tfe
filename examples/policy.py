#!/usr/bin/env python3
"""Policy management example for python-tfe SDK.

This example demonstrates how to use the Policy API to:
1. List policies in an organization
2. Create a new policy (Sentinel or OPA)
3. Upload policy content
4. Read policy details
5. Update policy settings
6. Download policy content
7. Delete a policy

Usage:
    python examples/policy.py --org myorg --policy-name my-policy
    python examples/policy.py --org myorg --policy-name my-policy --upload sentinel_policy.sentinel
    python examples/policy.py --org myorg --policy-name my-policy --download downloaded_policy.sentinel
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    EnforcementLevel,
    PolicyCreateOptions,
    PolicyKind,
    PolicyListOptions,
    PolicyUpdateOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Policy management demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--policy-name", required=True, help="Policy name to work with")
    parser.add_argument(
        "--kind",
        choices=["sentinel", "opa"],
        default="sentinel",
        help="Policy kind (sentinel or opa)",
    )
    parser.add_argument(
        "--enforcement-level",
        choices=["advisory", "soft-mandatory", "hard-mandatory", "mandatory"],
        default="advisory",
        help="Policy enforcement level",
    )
    parser.add_argument("--upload", help="Path to policy file to upload")
    parser.add_argument("--download", help="Path to save downloaded policy content")
    parser.add_argument("--description", help="Policy description")
    parser.add_argument("--query", help="OPA query (required for OPA policies)")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--search", help="Search policies by name")
    parser.add_argument("--delete", action="store_true", help="Delete the policy")

    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument required")
        return 1

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List all policies in the organization
    _print_header(f"Listing policies in organization: {args.org}")

    list_options = PolicyListOptions(
        page_number=args.page,
        page_size=args.page_size,
    )

    if args.search:
        list_options.search = args.search
    if args.kind:
        list_options.kind = (
            PolicyKind.SENTINEL if args.kind == "sentinel" else PolicyKind.OPA
        )

    policy_list = client.policies.list(args.org, list_options)

    print(f"Total policies: {policy_list.total_count}")
    print(f"Page {policy_list.current_page} of {policy_list.total_pages}")
    print()

    existing_policy = None
    for policy in policy_list.items:
        print(
            f"- {policy.id} | {policy.name} | kind={policy.kind} | enforcement={policy.enforcement_level}"
        )
        if policy.name == args.policy_name:
            existing_policy = policy

    # 2) Create a new policy if it doesn't exist
    if not existing_policy:
        _print_header(f"Creating new policy: {args.policy_name}")

        # Map string enforcement level to enum
        enforcement_map = {
            "advisory": EnforcementLevel.ENFORCEMENT_ADVISORY,
            "soft-mandatory": EnforcementLevel.ENFORCEMENT_SOFT,
            "hard-mandatory": EnforcementLevel.ENFORCEMENT_HARD,
            "mandatory": EnforcementLevel.ENFORCEMENT_MANDATORY,
        }

        create_options = PolicyCreateOptions(
            name=args.policy_name,
            kind=PolicyKind.SENTINEL if args.kind == "sentinel" else PolicyKind.OPA,
            enforcement_level=enforcement_map[args.enforcement_level],
            description=args.description
            or f"Example {args.kind} policy created via python-tfe SDK",
        )

        # OPA policies require a query
        if args.kind == "opa":
            if not args.query:
                create_options.query = "terraform.main"  # Default OPA query
            else:
                create_options.query = args.query

        try:
            policy = client.policies.create(args.org, create_options)
            print(f"Created policy: {policy.id}")
            print(f"Name: {policy.name}")
            print(f"Kind: {policy.kind}")
            print(f"Enforcement: {policy.enforcement_level}")
            if policy.query:
                print(f"Query: {policy.query}")
            existing_policy = policy
        except Exception as e:
            print(f"Error creating policy: {e}")
            return 1

    # 3) Read the policy details
    _print_header(f"Reading policy details: {existing_policy.id}")
    policy_details = client.policies.read(existing_policy.id)
    print(f"Policy ID: {policy_details.id}")
    print(f"Name: {policy_details.name}")
    print(f"Kind: {policy_details.kind}")
    print(f"Description: {policy_details.description}")
    print(f"Enforcement Level: {policy_details.enforcement_level}")
    print(f"Policy Set Count: {policy_details.policy_set_count}")
    print(f"Updated At: {policy_details.updated_at}")
    if policy_details.query:
        print(f"Query: {policy_details.query}")

    # 4) Upload policy content if provided
    if args.upload:
        _print_header(f"Uploading policy content from: {args.upload}")
        try:
            policy_content = Path(args.upload).read_bytes()
            client.policies.upload(existing_policy.id, policy_content)
            print(
                f"Successfully uploaded {len(policy_content)} bytes to policy {existing_policy.id}"
            )
        except Exception as e:
            print(f"Error uploading policy content: {e}")
            return 1
    elif not args.upload and not existing_policy:
        # Upload default content for demonstration
        _print_header("Uploading default policy content")
        if args.kind == "sentinel":
            default_content = """# Example Sentinel policy
main = rule {
    true
}
"""
        else:  # OPA
            default_content = """# Example OPA policy
package terraform

default main = true

main {
    input.resource_changes
}
"""
        try:
            client.policies.upload(existing_policy.id, default_content.encode("utf-8"))
            print(f"Uploaded default {args.kind} policy content")
        except Exception as e:
            print(f"Error uploading default content: {e}")

    # 5) Download policy content if requested
    if args.download:
        _print_header(f"Downloading policy content to: {args.download}")
        try:
            policy_content = client.policies.download(existing_policy.id)
            Path(args.download).write_bytes(policy_content)
            print(f"Downloaded {len(policy_content)} bytes to {args.download}")

            # Also print the content to console
            print("\nPolicy content preview:")
            print("-" * 40)
            content_str = policy_content.decode("utf-8")
            lines = content_str.split("\n")
            for i, line in enumerate(lines[:10], 1):  # Show first 10 lines
                print(f"{i:2d}: {line}")
            if len(lines) > 10:
                print(f"... ({len(lines) - 10} more lines)")
            print("-" * 40)

        except Exception as e:
            print(f"Error downloading policy content: {e}")

    # 6) Update policy if description provided
    if args.description and existing_policy:
        _print_header("Updating policy description")
        try:
            enforcement_map = {
                "advisory": EnforcementLevel.ENFORCEMENT_ADVISORY,
                "soft-mandatory": EnforcementLevel.ENFORCEMENT_SOFT,
                "hard-mandatory": EnforcementLevel.ENFORCEMENT_HARD,
                "mandatory": EnforcementLevel.ENFORCEMENT_MANDATORY,
            }

            update_options = PolicyUpdateOptions(
                description=args.description,
                enforcement_level=enforcement_map[args.enforcement_level],
            )

            if args.kind == "opa" and args.query:
                update_options.query = args.query

            updated_policy = client.policies.update(existing_policy.id, update_options)
            print(f"Updated policy: {updated_policy.id}")
            print(f"New description: {updated_policy.description}")
            print(f"Enforcement level: {updated_policy.enforcement_level}")
        except Exception as e:
            print(f"Error updating policy: {e}")

    # 7) Delete policy if requested
    if args.delete and existing_policy:
        _print_header(f"Deleting policy: {existing_policy.id}")
        try:
            client.policies.delete(existing_policy.id)
            print(f"Successfully deleted policy: {existing_policy.id}")
        except Exception as e:
            print(f"Error deleting policy: {e}")
            return 1

    print("\nPolicy operations completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
