#!/usr/bin/env python3
"""
Organization Token Operations Example

Demonstrates usage of all 6 organization token operations:
1. create() - Create a new organization token, replacing any existing token
2. create_with_options() - Create with options like expiration date and token type
3. read() - Read the organization token
4. read_with_options() - Read with options like token type
5. delete() - Delete the organization token
6. delete_with_options() - Delete with options like token type

Usage:
- Modify organization names as needed for your environment
- Ensure you have proper TFE credentials and organization access
- Organization tokens are used for organization-level API access

Prerequisites:
- Set TFE_TOKEN and TFE_ADDRESS environment variables
- You need an existing organization or admin permissions to create one
- Appropriate permissions to manage organization tokens
"""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    OrganizationTokenCreateOptions,
    OrganizationTokenDeleteOptions,
    OrganizationTokenReadOptions,
    TokenType,
)


def main():
    """Execute organization token operation examples."""

    print("=" * 80)
    print("ORGANIZATION TOKEN OPERATIONS")
    print("=" * 80)

    # Initialize the TFE client
    client = TFEClient(TFEConfig.from_env())
    organization_name = "my-org"  # Change to your organization name

    # =====================================================
    # 1. CREATE ORGANIZATION TOKEN (BASIC)
    # =====================================================
    print("\n1. create() - Create a new organization token:")
    print("-" * 40)
    try:
        print(f"Creating token for organization: {organization_name}")
        token = client.organization_tokens.create(organization_name)

        print("Token created successfully!")
        print(f"  Token ID: {token.id}")
        print(f"  Created At: {token.created_at}")
        print(f"  Description: {token.description}")
        print(f"  Token Value: {token.token}")
        if token.expired_at:
            print(f"  Expires At: {token.expired_at}")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()

    # =====================================================
    # 2. CREATE WITH OPTIONS (WITH EXPIRATION)
    # =====================================================
    print("2. create_with_options() - Create token with expiration date:")
    print("-" * 40)
    try:
        # Create a token that expires in 30 days
        expiry_date = datetime.utcnow() + timedelta(days=30)
        options = OrganizationTokenCreateOptions(expired_at=expiry_date)

        print(f"Creating organization token with expiration date: {expiry_date}")
        token = client.organization_tokens.create_with_options(
            organization_name, options
        )

        print("Token created with options successfully!")
        print(f"  Token ID: {token.id}")
        print(f"  Created At: {token.created_at}")
        if token.expired_at:
            print(f"  Expires At: {token.expired_at}")
        print()

    except Exception as e:
        print(f" Error: {e}")
        print()

    # =====================================================
    print("3. create_with_options() - Create audit-trails token:")
    print("-" * 40)
    try:
        options = OrganizationTokenCreateOptions(token_type=TokenType.AUDIT_TRAILS)

        print(f"Creating audit-trails token for organization: {organization_name}")
        token = client.organization_tokens.create_with_options(
            organization_name, options
        )

        print(" Audit-trails token created successfully!")
        print(f"  Token ID: {token.id}")
        print(f"  Token Value: {token.token}")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()

    # =====================================================
    print("4. read() - Read the organization token:")
    print("-" * 40)
    try:
        print(f"Reading organization token for organization: {organization_name}")
        token = client.organization_tokens.read(organization_name)

        print("Token read successfully!")
        print(f"  Token ID: {token.id}")
        print(f"  Created At: {token.created_at}")
        print(f"  Description: {token.description}")
        if token.last_used_at:
            print(f"  Last Used At: {token.last_used_at}")
        if token.expired_at:
            print(f"  Expires At: {token.expired_at}")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()

    # =====================================================
    print("5. read_with_options() - Read audit-trails token:")
    print("-" * 40)
    try:
        options = OrganizationTokenReadOptions(token_type=TokenType.AUDIT_TRAILS)

        print(f"Reading audit-trails token for organization: {organization_name}")
        token = client.organization_tokens.read_with_options(organization_name, options)

        print(" Audit-trails token read successfully!")
        print(f"  Token ID: {token.id}")
        print(f"  Token Value: {token.token}")
        print()

    except Exception as e:
        print(f"✗ Error: {e}")
        print()

    # =====================================================
    print("6. delete() - Delete the organization token:")
    print("-" * 40)
    try:
        print(f"Deleting organization token for organization: {organization_name}")
        client.organization_tokens.delete(organization_name)

        print("✓ Token deleted successfully!")
        print()

    except Exception as e:
        print(f" Error: {e}")
        print()

    # =====================================================
    print("7. delete_with_options() - Delete audit-trails token:")
    print("-" * 40)
    try:
        options = OrganizationTokenDeleteOptions(token_type=TokenType.AUDIT_TRAILS)

        print(f"Deleting audit-trails token for organization: {organization_name}")
        client.organization_tokens.delete_with_options(organization_name, options)

        print(" Audit-trails token deleted successfully!")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()

    print("=" * 80)
    print("ORGANIZATION TOKEN OPERATIONS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
