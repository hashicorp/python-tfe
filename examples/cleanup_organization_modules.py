#!/usr/bin/env python3
"""
Organization Module Cleanup Script

This script demonstrates using the registry module list() and delete functions
to find and remove all modules from a specific organization.

FEATURES:
- Lists all modules in the specified organization
- Shows module details (name, provider, status, versions)
- Provides options to delete individual modules or all modules
- Uses both delete_by_name() and delete() functions
- Safe mode with confirmation prompts

USAGE:
- Set your organization name below
- Run the script to see all modules
- Choose which modules to delete
- Confirm deletion operations

WARNING: This script can delete ALL modules in an organization!
Use with caution and test in a non-production environment first.
"""

import os
import sys
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tfe import TFEClient, TFEConfig
from tfe.models.registry_module_types import (
    RegistryModule,
    RegistryModuleID,
    RegistryModuleListOptions,
    RegistryName,
)


def main():
    """Main function to list and optionally delete organization modules."""

    # =====================================================
    # CONFIGURATION - MODIFY THESE VALUES
    # =====================================================
    organization_name = "aayush-test"  # Replace with your organization

    print("=" * 80)
    print("ORGANIZATION MODULE CLEANUP SCRIPT")
    print("=" * 80)
    print(f"Target Organization: {organization_name}")
    print("=" * 80)

    # Initialize TFE client
    try:
        config = TFEConfig()
        client = TFEClient(config)
        print("✓ TFE Client initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize TFE client: {e}")
        return

    # =====================================================
    # STEP 1: LIST ALL MODULES IN ORGANIZATION
    # =====================================================
    print(f"\n📋 STEP 1: Listing all modules in '{organization_name}' organization...")

    modules: list[RegistryModule] = []

    try:
        # Use the list() function to get all modules
        list_options = RegistryModuleListOptions(
            # You can add filters here if needed:
            # provider="aws",  # Filter by provider
            # search="test",   # Search for specific names
        )

        module_count = 0
        for module in client.registry_modules.list(organization_name, list_options):
            modules.append(module)
            module_count += 1

            print(f"   {module_count:2d}. Module: {module.name}")
            print(f"       Provider: {module.provider}")
            print(f"       Status: {module.status}")
            print(f"       Registry: {module.registry_name.value if module.registry_name else 'private'}")
            print(f"       No Code: {module.no_code}")

            # Show version information if available
            if hasattr(module, 'version_statuses') and module.version_statuses:
                print(f"       Versions: {len(module.version_statuses)} version(s)")
                for vs in module.version_statuses[:3]:  # Show first 3 versions
                    if hasattr(vs, 'version') and hasattr(vs, 'status'):
                        # Handle objects with attributes
                        version_str = vs.version if vs.version else 'unknown'
                        status_str = vs.status if vs.status else 'unknown'
                        print(f"         - v{version_str}: {status_str}")
                    elif isinstance(vs, dict):
                        # Handle dictionary objects
                        version_str = vs.get('version', 'unknown')
                        status_str = vs.get('status', 'unknown')
                        print(f"         - v{version_str}: {status_str}")
                    else:
                        # Handle other types
                        print(f"         - {vs}")
                if len(module.version_statuses) > 3:
                    print(f"         ... and {len(module.version_statuses) - 3} more")
            else:
                print("       Versions: No version information available")

            print(f"       Created: {module.created_at}")
            print()

        print(f"📊 Total modules found: {module_count}")

    except Exception as e:
        print(f"✗ Error listing modules: {e}")
        return

    if not modules:
        print("✅ No modules found in the organization. Nothing to delete!")
        return

    # =====================================================
    # STEP 2: INTERACTIVE DELETION MENU
    # =====================================================
    print("\n🗑️  STEP 2: Module Deletion Options")
    print("=" * 50)

    while True:
        print("\nChoose an action:")
        print("1. Delete specific module by number")
        print("2. Delete all modules (DANGEROUS!)")
        print("3. Test delete functions on non-existent module")
        print("4. Show module details")
        print("5. Exit without deleting")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            delete_specific_module(client, organization_name, modules)
        elif choice == "2":
            delete_all_modules(client, organization_name, modules)
        elif choice == "3":
            test_delete_functions(client, organization_name)
        elif choice == "4":
            show_module_details(client, organization_name, modules)
        elif choice == "5":
            print("👋 Exiting without making changes.")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def delete_specific_module(client: TFEClient, organization_name: str, modules: list[RegistryModule]):
    """Delete a specific module chosen by the user."""

    if not modules:
        print("❌ No modules available to delete.")
        return

    try:
        print("\nAvailable modules:")
        for i, module in enumerate(modules, 1):
            print(f"   {i:2d}. {module.name}/{module.provider}")

        choice = input(f"\nEnter module number to delete (1-{len(modules)}): ").strip()

        try:
            module_index = int(choice) - 1
            if module_index < 0 or module_index >= len(modules):
                print("❌ Invalid module number.")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return

        selected_module = modules[module_index]

        print("\n⚠️  DELETION CONFIRMATION")
        print(f"Module to delete: {selected_module.name}")
        print(f"Provider: {selected_module.provider}")
        print(f"Status: {selected_module.status}")

        confirm = input(f"\nAre you sure you want to delete '{selected_module.name}/{selected_module.provider}'? (yes/no): ").strip().lower()

        if confirm in ['yes', 'y']:
            # Test both delete functions
            print("\n🗑️  Deleting module using delete_by_name()...")

            module_id = RegistryModuleID(
                organization=organization_name,
                name=selected_module.name,
                provider=selected_module.provider,
                registry_name=RegistryName.PRIVATE
            )

            # Use delete_by_name function
            client.registry_modules.delete_by_name(module_id)
            print(f"✅ Successfully called delete_by_name() for {selected_module.name}")

            # Wait a moment and verify
            print("⏳ Waiting 3 seconds for deletion to process...")
            time.sleep(3)

            try:
                client.registry_modules.read(module_id)
                print("⚠️  Module still exists (deletion may take more time)")
            except Exception:
                print("✅ Confirmed: Module has been deleted")
                # Remove from our local list
                modules.remove(selected_module)

        else:
            print("❌ Deletion cancelled.")

    except Exception as e:
        print(f"✗ Error deleting module: {e}")

def delete_all_modules(client: TFEClient, organization_name: str, modules: list[RegistryModule]):
    """Delete all modules in the organization (with strong confirmation)."""

    if not modules:
        print("❌ No modules to delete.")
        return

    print("\n🚨 DANGER ZONE: DELETE ALL MODULES")
    print("=" * 50)
    print(f"This will delete ALL {len(modules)} modules in '{organization_name}':")

    for i, module in enumerate(modules, 1):
        print(f"   {i:2d}. {module.name}/{module.provider}")

    print("\n⚠️  This action cannot be undone!")

    # Multiple confirmations for safety
    confirm1 = input(f"\nType 'DELETE ALL' to confirm deletion of {len(modules)} modules: ").strip()
    if confirm1 != "DELETE ALL":
        print("❌ Deletion cancelled - confirmation text did not match.")
        return

    confirm2 = input(f"Type the organization name '{organization_name}' to confirm: ").strip()
    if confirm2 != organization_name:
        print("❌ Deletion cancelled - organization name did not match.")
        return

    final_confirm = input("Type 'I understand this cannot be undone' to proceed: ").strip()
    if final_confirm != "I understand this cannot be undone":
        print("❌ Deletion cancelled - final confirmation failed.")
        return

    print(f"\n🗑️  Proceeding with deletion of all {len(modules)} modules...")

    deleted_count = 0
    failed_count = 0

    for i, module in enumerate(modules, 1):
        try:
            print(f"   [{i:2d}/{len(modules)}] Deleting {module.name}/{module.provider}...")

            # Alternate between delete_by_name and delete functions
            if i % 2 == 1:
                # Use delete_by_name
                module_id = RegistryModuleID(
                    organization=organization_name,
                    name=module.name,
                    provider=module.provider,
                    registry_name=RegistryName.PRIVATE
                )
                client.registry_modules.delete_by_name(module_id)
                print("       ✅ Used delete_by_name()")
            else:
                # Use delete
                client.registry_modules.delete(organization_name, module.name)
                print("       ✅ Used delete()")

            deleted_count += 1
            time.sleep(1)  # Brief pause between deletions

        except Exception as e:
            print(f"       ✗ Failed: {e}")
            failed_count += 1

    print("\n📊 Deletion Summary:")
    print(f"   ✅ Successfully deleted: {deleted_count}")
    print(f"   ✗ Failed: {failed_count}")
    print(f"   📋 Total attempted: {len(modules)}")

def test_delete_functions(client: TFEClient, organization_name: str):
    """Test delete functions on non-existent modules for demonstration."""

    print("\n🧪 TESTING DELETE FUNCTIONS")
    print("=" * 50)
    print("Testing delete functions with non-existent modules (safe testing)...")

    # Test delete() function
    print("\n1. Testing delete() function:")
    try:
        test_name = "non-existent-test-module"
        print(f"   Calling delete('{organization_name}', '{test_name}')")
        client.registry_modules.delete(organization_name, test_name)
        print("   ✅ delete() function executed successfully")
    except Exception as e:
        print(f"   ⚠️  Expected error: {e}")

    # Test delete_by_name() function
    print("\n2. Testing delete_by_name() function:")
    try:
        test_module_id = RegistryModuleID(
            organization=organization_name,
            name="non-existent-test-module",
            provider="aws",
            registry_name=RegistryName.PRIVATE
        )
        print("   Calling delete_by_name() with non-existent module")
        client.registry_modules.delete_by_name(test_module_id)
        print("   ✅ delete_by_name() function executed successfully")
    except Exception as e:
        print(f"   ⚠️  Expected error: {e}")

    print("\n✅ Delete function testing completed!")

def show_module_details(client: TFEClient, organization_name: str, modules: list[RegistryModule]):
    """Show detailed information about a specific module."""

    if not modules:
        print("❌ No modules available.")
        return

    try:
        print("\nAvailable modules:")
        for i, module in enumerate(modules, 1):
            print(f"   {i:2d}. {module.name}/{module.provider}")

        choice = input(f"\nEnter module number for details (1-{len(modules)}): ").strip()

        try:
            module_index = int(choice) - 1
            if module_index < 0 or module_index >= len(modules):
                print("❌ Invalid module number.")
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            return

        selected_module = modules[module_index]

        print("\n📋 DETAILED MODULE INFORMATION")
        print("=" * 50)
        print(f"Name: {selected_module.name}")
        print(f"Provider: {selected_module.provider}")
        print(f"Status: {selected_module.status}")
        print(f"Registry: {selected_module.registry_name.value if selected_module.registry_name else 'private'}")
        print(f"No Code: {selected_module.no_code}")
        print(f"Created: {selected_module.created_at}")
        print(f"Updated: {selected_module.updated_at}")

        if hasattr(selected_module, 'organization') and selected_module.organization:
            print(f"Organization: {selected_module.organization}")

        if hasattr(selected_module, 'vcs_repo') and selected_module.vcs_repo:
            print(f"VCS Repository: {selected_module.vcs_repo}")

        if hasattr(selected_module, 'version_statuses') and selected_module.version_statuses:
            print(f"\nVersions ({len(selected_module.version_statuses)}):")
            for vs in selected_module.version_statuses:
                if hasattr(vs, 'version') and hasattr(vs, 'status'):
                    # Handle objects with attributes
                    version_str = vs.version if vs.version else 'unknown'
                    status_str = vs.status if vs.status else 'unknown'
                    print(f"  - v{version_str}: {status_str}")
                elif isinstance(vs, dict):
                    # Handle dictionary objects
                    version_str = vs.get('version', 'unknown')
                    status_str = vs.get('status', 'unknown')
                    print(f"  - v{version_str}: {status_str}")
                else:
                    # Handle other types
                    print(f"  - {vs}")

        # Try to get more details using read() function
        try:
            print("\n🔍 Fetching additional details using read() function...")
            module_id = RegistryModuleID(
                organization=organization_name,
                name=selected_module.name,
                provider=selected_module.provider,
                registry_name=RegistryName.PRIVATE
            )

            detailed_module = client.registry_modules.read(module_id)
            print("✅ Successfully retrieved detailed information")
            print(f"Publishing Mechanism: {detailed_module.publishing_mechanism}")

            if hasattr(detailed_module, 'permissions') and detailed_module.permissions:
                print(f"Permissions: {detailed_module.permissions}")

        except Exception as e:
            print(f"⚠️  Could not fetch additional details: {e}")

    except Exception as e:
        print(f"✗ Error showing module details: {e}")

if __name__ == "__main__":
    main()
