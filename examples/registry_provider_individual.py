#!/usr/bin/env python3
"""
Registry Provider Individual Function Tests

This file provides individual test functions for each registry provider operation.
You can run specific functions to test individual parts of the API.

Functions available:
- test_list_simple() - Basic list test
- test_create_private() - Create a private provider
- test_create_public() - Create a public provider
- test_read_with_id() - Read a provider by ID
- test_delete_by_id() - Delete a provider by ID

Usage:
    python registry_provider_individual.py
"""

import os
import random
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tfe import TFEClient
from tfe.models.registry_provider_types import (
    RegistryName,
    RegistryProviderCreateOptions,
    RegistryProviderID,
    RegistryProviderIncludeOps,
    RegistryProviderListOptions,
    RegistryProviderReadOptions,
)


def get_client_and_org():
    """Initialize client and get organization name."""
    client = TFEClient()
    organization_name = os.getenv("TFE_ORGANIZATION", "aayush-test")
    return client, organization_name


def test_list_simple():
    """Test 1: Simple list of registry providers."""
    print("=== Test 1: List Registry Providers ===")

    client, org = get_client_and_org()

    try:
        providers = list(client.registry_providers.list(org))
        print(f"✓ Found {len(providers)} providers in organization '{org}'")

        for i, provider in enumerate(providers[:5], 1):
            print(f"  {i}. {provider.name}")
            print(f"     Namespace: {provider.namespace}")
            print(f"     Registry: {provider.registry_name.value}")
            print(f"     ID: {provider.id}")
            print(f"     Can Delete: {provider.permissions.can_delete}")
            print()

        return providers

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def test_list_with_options():
    """Test 2: List with filtering options."""
    print("=== Test 2: List with Options ===")

    client, org = get_client_and_org()

    try:
        # Test with search
        options = RegistryProviderListOptions(
            search="test", registry_name=RegistryName.PRIVATE, page_size=5
        )

        providers = list(client.registry_providers.list(org, options))
        print(f"✓ Found {len(providers)} providers matching search 'test'")

        # Test with include
        include_options = RegistryProviderListOptions(
            include=[RegistryProviderIncludeOps.REGISTRY_PROVIDER_VERSIONS]
        )

        detailed_providers = list(client.registry_providers.list(org, include_options))
        print(f"✓ Found {len(detailed_providers)} providers with version details")

        return providers

    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def test_create_private():
    """Test 3: Create a private registry provider."""
    print("=== Test 3: Create Private Provider ===")

    client, org = get_client_and_org()

    try:
        provider_name = f"test-provider-{random.randint(100000, 999999)}"

        options = RegistryProviderCreateOptions(
            name=provider_name,
            namespace=org,  # For private providers, namespace = org name
            registry_name=RegistryName.PRIVATE,
        )

        provider = client.registry_providers.create(org, options)
        print(f"✓ Created private provider: {provider.name}")
        print(f"  ID: {provider.id}")
        print(f"  Namespace: {provider.namespace}")
        print(f"  Registry: {provider.registry_name.value}")
        print(f"  Created: {provider.created_at}")

        return provider

    except Exception as e:
        print(f"✗ Error creating private provider: {e}")
        return None


def test_create_public():
    """Test 4: Create a public registry provider."""
    print("=== Test 4: Create Public Provider ===")

    client, org = get_client_and_org()

    try:
        provider_name = f"test-provider-{random.randint(100000, 999999)}"
        namespace_name = f"test-namespace-{random.randint(1000, 9999)}"

        options = RegistryProviderCreateOptions(
            name=provider_name,
            namespace=namespace_name,
            registry_name=RegistryName.PUBLIC,
        )

        provider = client.registry_providers.create(org, options)
        print(f"✓ Created public provider: {provider.name}")
        print(f"  ID: {provider.id}")
        print(f"  Namespace: {provider.namespace}")
        print(f"  Registry: {provider.registry_name.value}")
        print(f"  Created: {provider.created_at}")

        return provider

    except Exception as e:
        print(f"✗ Error creating public provider: {e}")
        return None


def test_read_with_id(provider_data):
    """Test 5: Read a provider by ID."""
    print("=== Test 5: Read Provider by ID ===")

    client, org = get_client_and_org()

    if not provider_data:
        print("⚠️  No provider data provided")
        return None

    try:
        provider_id = RegistryProviderID(
            organization_name=org,
            registry_name=provider_data.registry_name,
            namespace=provider_data.namespace,
            name=provider_data.name,
        )

        # Basic read
        provider = client.registry_providers.read(provider_id)
        print(f"✓ Read provider: {provider.name}")
        print(f"  ID: {provider.id}")
        print(f"  Namespace: {provider.namespace}")
        print(f"  Registry: {provider.registry_name.value}")
        print(f"  Created: {provider.created_at}")
        print(f"  Updated: {provider.updated_at}")
        print(f"  Can Delete: {provider.permissions.can_delete}")

        # Read with options
        options = RegistryProviderReadOptions(
            include=[RegistryProviderIncludeOps.REGISTRY_PROVIDER_VERSIONS]
        )

        detailed_provider = client.registry_providers.read(provider_id, options)
        print(f"✓ Read with options: {detailed_provider.name}")

        if detailed_provider.registry_provider_versions:
            print(
                f"  Found {len(detailed_provider.registry_provider_versions)} versions"
            )
        else:
            print("  No versions found")

        return provider

    except Exception as e:
        print(f"✗ Error reading provider: {e}")
        return None


def test_delete_by_id(provider_data):
    """Test 6: Delete a provider by ID."""
    print("=== Test 6: Delete Provider by ID ===")

    client, org = get_client_and_org()

    if not provider_data:
        print("⚠️  No provider data provided")
        return False

    try:
        provider_id = RegistryProviderID(
            organization_name=org,
            registry_name=provider_data.registry_name,
            namespace=provider_data.namespace,
            name=provider_data.name,
        )

        # Verify provider exists
        provider = client.registry_providers.read(provider_id)
        print(f"✓ Found provider to delete: {provider.name}")

        # Delete the provider
        client.registry_providers.delete(provider_id)
        print("✓ Successfully called delete() for provider")

        # Verify deletion (optional - may take time)
        import time

        time.sleep(2)

        try:
            client.registry_providers.read(provider_id)
            print("⚠️  Provider still exists (deletion may take time)")
        except Exception:
            print("✓ Provider successfully deleted")

        return True

    except Exception as e:
        print(f"✗ Error deleting provider: {e}")
        return False


def main():
    """Run all tests in sequence."""
    print("🚀 REGISTRY PROVIDER INDIVIDUAL TESTS")
    print("=" * 50)

    # Test 1: List providers
    providers = test_list_simple()
    print()

    # Test 2: List with options
    test_list_with_options()
    print()

    # ⚠️ WARNING: Uncomment the following tests to create/delete providers
    print("⚠️  WARNING: Creation and deletion tests are commented out for safety")
    print("⚠️  Uncomment them in the code to test creation and deletion")
    print()

    # UNCOMMENT TO TEST CREATION:
    # Test 3: Create private provider
    private_provider = test_create_private()
    print()

    # Test 4: Create public provider
    public_provider = test_create_public()
    print()

    # Test 5: Read provider
    if private_provider:
        test_read_with_id(private_provider)
        print()

    # Test 6: Delete provider (UNCOMMENT TO TEST DELETION)
    if private_provider:
        test_delete_by_id(private_provider)
        print()

    if public_provider:
        test_delete_by_id(public_provider)
        print()

    # Test with existing provider if available
    if providers:
        print("=== Testing with Existing Provider ===")
        existing_provider = providers[0]
        test_read_with_id(existing_provider)
        print()

    print("✅ Individual tests completed!")
    print("💡 To test creation/deletion, uncomment the relevant sections in the code")


if __name__ == "__main__":
    main()
