from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RegistryProviderVersionCreateOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Registry Provider Versions demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", required=True, help="Organization name")
    parser.add_argument(
        "--registry-name",
        default="private",
        help="Registry name (default: private)",
    )
    parser.add_argument("--namespace", required=True, help="Provider namespace")
    parser.add_argument("--name", required=True, help="Provider name")
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for fetching versions",
    )
    parser.add_argument("--create", action="store_true", help="Create a test version")
    parser.add_argument("--version", help="Version number (e.g., 1.0.0)")
    parser.add_argument("--key-id", help="GPG key ID for version signing")
    parser.add_argument(
        "--protocols",
        nargs="+",
        help="Supported protocols (e.g., 5.0 6.0)",
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Create a new version (if --create flag is provided)
    if args.create:
        if not args.version:
            print("Error: --version is required for create operation")
            return
        if not args.key_id:
            print("Error: --key-id is required for create operation")
            return
        if not args.protocols:
            print("Error: --protocols is required for create operation")
            return

        _print_header(f"Creating new version: {args.version}")

        create_options = RegistryProviderVersionCreateOptions(
            version=args.version,
            key_id=args.key_id,
            protocols=args.protocols,
        )

        new_version = client.registry_provider_versions.create(
            organization=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
            options=create_options,
        )

        print(f"Created version: {new_version.id}")
        print(f"  Version: {new_version.version}")
        print(f"  Created: {new_version.created_at}")
        print(f"  Key ID: {new_version.key_id}")
        print(f"  Protocols: {', '.join(new_version.protocols)}")
        print(f"  Shasums Uploaded: {new_version.shasums_uploaded}")
        print(f"  Shasums Signature Uploaded: {new_version.shasums_sig_uploaded}")

        # Show upload URLs if available in links
        if new_version.links:
            print("\n  Upload URLs:")
            if "shasums-upload" in new_version.links:
                print(f"    Shasums: {new_version.links['shasums-upload']}")
            if "shasums-sig-upload" in new_version.links:
                print(
                    f"    Shasums Signature: {new_version.links['shasums-sig-upload']}"
                )


if __name__ == "__main__":
    main()
