from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RegistryProviderID,
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
    RegistryProviderVersionListOptions,
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
    parser.add_argument("--read", action="store_true", help="Read a specific version")
    parser.add_argument(
        "--delete", action="store_true", help="Delete a specific version"
    )
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

    # 1) List all versions for the registry provider
    _print_header(
        f"Listing versions for {args.registry_name}/{args.namespace}/{args.name}"
    )
    provider_id = RegistryProviderID(
        organization_name=args.organization,
        registry_name=args.registry_name,
        namespace=args.namespace,
        name=args.name,
    )

    options = RegistryProviderVersionListOptions(
        page_size=args.page_size,
    )

    version_count = 0
    for version in client.registry_provider_versions.list(
        provider_id=provider_id,
        options=options,
    ):
        version_count += 1
        print(f"- Version {version.version} (ID: {version.id})")
        print(f"  Created: {version.created_at}")
        print(f"  Updated: {version.updated_at}")
        print(f"  Key ID: {version.key_id}")
        print(f"  Protocols: {', '.join(version.protocols)}")
        print(f"  Shasums Uploaded: {version.shasums_uploaded}")
        print(f"  Shasums Signature Uploaded: {version.shasums_sig_uploaded}")
        if version.permissions:
            print("  Permissions:")
            print(f"    Can Delete: {version.permissions.can_delete}")
            print(f"    Can Upload Asset: {version.permissions.can_upload_asset}")
        print()

    if version_count == 0:
        print("No versions found.")
    else:
        print(f"Total: {version_count} versions")

    # 2) Create a new version (if --create flag is provided)
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
            provider_id=provider_id,
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

    # 3) Read a specific version (if --read flag is provided)
    if args.read:
        if not args.version:
            print("Error: --version is required for read operation")
            return

        _print_header(f"Reading version: {args.version}")

        version_id = RegistryProviderVersionID(
            organization_name=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
            version=args.version,
        )

        version = client.registry_provider_versions.read(version_id)

        print(f"Version ID: {version.id}")
        print(f"  Version: {version.version}")
        print(f"  Created: {version.created_at}")
        print(f"  Updated: {version.updated_at}")
        print(f"  Key ID: {version.key_id}")
        print(f"  Protocols: {', '.join(version.protocols)}")
        print(f"  Shasums Uploaded: {version.shasums_uploaded}")
        print(f"  Shasums Signature Uploaded: {version.shasums_sig_uploaded}")

        if version.permissions:
            print("  Permissions:")
            print(f"    Can Delete: {version.permissions.can_delete}")
            print(f"    Can Upload Asset: {version.permissions.can_upload_asset}")

        # Show links if available
        if version.links:
            print("  Links:")
            for key, value in version.links.items():
                print(f"    {key}: {value}")

    # 4) Delete a version (if --delete flag is provided)
    if args.delete:
        if not args.version:
            print("Error: --version is required for delete operation")
            return

        _print_header(f"Deleting version: {args.version}")

        version_id = RegistryProviderVersionID(
            organization_name=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
            version=args.version,
        )

        # First read the version to show what's being deleted
        try:
            version_to_delete = client.registry_provider_versions.read(version_id)
            print("Version to delete:")
            print(f"  ID: {version_to_delete.id}")
            print(f"  Version: {version_to_delete.version}")
            print(f"  Protocols: {', '.join(version_to_delete.protocols)}")
            print(f"  Key ID: {version_to_delete.key_id}")
        except Exception as e:
            print(f"Error reading version: {e}")
            return

        # Delete the version
        client.registry_provider_versions.delete(version_id)
        print(f"\n  Successfully deleted version: {args.version}")

        # List remaining versions
        _print_header("Listing versions after deletion")
        provider_id = RegistryProviderID(
            organization_name=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
        )

        options = RegistryProviderVersionListOptions(
            page_size=args.page_size,
        )
        print("Remaining versions:")
        remaining_count = 0
        for version in client.registry_provider_versions.list(
            provider_id=provider_id,
            options=options,
        ):
            remaining_count += 1
            print(
                f"- Version {version.version}: "
                f"  protocols={', '.join(version.protocols)}, "
                f"  shasums_uploaded={version.shasums_uploaded}"
            )

        if remaining_count == 0:
            print("No versions remaining.")
        else:
            print(f"\nTotal: {remaining_count} versions")


if __name__ == "__main__":
    main()
