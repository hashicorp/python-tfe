# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RegistryProviderPlatformCreateOptions,
    RegistryProviderPlatformID,
    RegistryProviderPlatformListOptions,
    RegistryProviderVersionID,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Registry Provider Platforms demo for python-tfe SDK"
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
        "--version", required=True, help="Provider version (e.g., 1.0.0)"
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Page size for listing platforms",
    )
    parser.add_argument("--create", action="store_true", help="Create a platform")
    parser.add_argument("--read", action="store_true", help="Read a specific platform")
    parser.add_argument(
        "--delete", action="store_true", help="Delete a specific platform"
    )
    parser.add_argument(
        "--os", dest="os", help="Operating system (e.g., linux, darwin)"
    )
    parser.add_argument("--arch", help="Architecture (e.g., amd64, arm64)")
    parser.add_argument("--shasum", help="SHA256 checksum of the provider binary")
    parser.add_argument("--filename", help="Filename of the provider binary zip")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    version_id = RegistryProviderVersionID(
        organization_name=args.organization,
        registry_name=args.registry_name,
        namespace=args.namespace,
        name=args.name,
        version=args.version,
    )

    # 1) List all platforms for the provider version
    _print_header(
        f"Listing platforms for {args.registry_name}/{args.namespace}/{args.name} @ {args.version}"
    )

    list_options = RegistryProviderPlatformListOptions(page_size=args.page_size)

    platform_count = 0
    for platform in client.registry_provider_platforms.list(
        version_id=version_id,
        options=list_options,
    ):
        platform_count += 1
        print(f"- Platform {platform.os}/{platform.arch} (ID: {platform.id})")
        print(f"  Filename: {platform.filename}")
        print(f"  Shasum: {platform.shasum}")
        print(f"  Provider Binary Uploaded: {platform.provider_binary_uploaded}")
        if platform.permissions:
            print("  Permissions:")
            print(f"    Can Delete: {platform.permissions.can_delete}")
            print(f"    Can Upload Asset: {platform.permissions.can_upload_asset}")
        if platform.links:
            print("  Links:")
            for key, value in platform.links.items():
                print(f"    {key}: {value}")
        print()

    if platform_count == 0:
        print("No platforms found.")
    else:
        print(f"Total: {platform_count} platforms")

    # 2) Create a new platform (if --create flag is provided)
    if args.create:
        if not args.os:
            print("Error: --os is required for create operation")
            return
        if not args.arch:
            print("Error: --arch is required for create operation")
            return
        if not args.shasum:
            print("Error: --shasum is required for create operation")
            return
        if not args.filename:
            print("Error: --filename is required for create operation")
            return

        _print_header(f"Creating platform: {args.os}/{args.arch}")

        create_options = RegistryProviderPlatformCreateOptions(
            os=args.os,
            arch=args.arch,
            shasum=args.shasum,
            filename=args.filename,
        )

        new_platform = client.registry_provider_platforms.create(
            version_id=version_id,
            options=create_options,
        )

        print(f"Created platform: {new_platform.id}")
        print(f"  OS: {new_platform.os}")
        print(f"  Arch: {new_platform.arch}")
        print(f"  Filename: {new_platform.filename}")
        print(f"  Shasum: {new_platform.shasum}")
        print(f"  Provider Binary Uploaded: {new_platform.provider_binary_uploaded}")

        if new_platform.links:
            print("\n  Upload URLs:")
            if "provider-binary-upload" in new_platform.links:
                print(
                    f"    Provider Binary: {new_platform.links['provider-binary-upload']}"
                )

    # 3) Read a specific platform (if --read flag is provided)
    if args.read:
        if not args.os:
            print("Error: --os is required for read operation")
            return
        if not args.arch:
            print("Error: --arch is required for read operation")
            return

        _print_header(f"Reading platform: {args.os}/{args.arch}")

        platform_id = RegistryProviderPlatformID(
            organization_name=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
            version=args.version,
            os=args.os,
            arch=args.arch,
        )

        platform = client.registry_provider_platforms.read(platform_id)

        print(f"Platform ID: {platform.id}")
        print(f"  OS: {platform.os}")
        print(f"  Arch: {platform.arch}")
        print(f"  Filename: {platform.filename}")
        print(f"  Shasum: {platform.shasum}")
        print(f"  Provider Binary Uploaded: {platform.provider_binary_uploaded}")

        if platform.permissions:
            print("  Permissions:")
            print(f"    Can Delete: {platform.permissions.can_delete}")
            print(f"    Can Upload Asset: {platform.permissions.can_upload_asset}")

        if platform.links:
            print("  Links:")
            for key, value in platform.links.items():
                print(f"    {key}: {value}")

    # 4) Delete a platform (if --delete flag is provided)
    if args.delete:
        if not args.os:
            print("Error: --os is required for delete operation")
            return
        if not args.arch:
            print("Error: --arch is required for delete operation")
            return

        _print_header(f"Deleting platform: {args.os}/{args.arch}")

        platform_id = RegistryProviderPlatformID(
            organization_name=args.organization,
            registry_name=args.registry_name,
            namespace=args.namespace,
            name=args.name,
            version=args.version,
            os=args.os,
            arch=args.arch,
        )

        try:
            platform_to_delete = client.registry_provider_platforms.read(platform_id)
            print("Platform to delete:")
            print(f"  ID: {platform_to_delete.id}")
            print(f"  OS/Arch: {platform_to_delete.os}/{platform_to_delete.arch}")
            print(f"  Filename: {platform_to_delete.filename}")
        except Exception as e:
            print(f"Error reading platform: {e}")
            return

        client.registry_provider_platforms.delete(platform_id)
        print(f"\n  Successfully deleted platform: {args.os}/{args.arch}")

        # List remaining platforms
        _print_header("Listing platforms after deletion")
        remaining_count = 0
        for platform in client.registry_provider_platforms.list(version_id=version_id):
            remaining_count += 1
            print(f"- {platform.os}/{platform.arch} (ID: {platform.id})")

        if remaining_count == 0:
            print("No platforms remaining.")
        else:
            print(f"Total remaining: {remaining_count} platforms")


if __name__ == "__main__":
    main()
