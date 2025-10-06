#!/usr/bin/env python3
"""SSH Keys Example Script.

This script demonstrates how to use the SSH Keys API to:
1. List all SSH keys for an organization
2. Create a new SSH key
3. Read a specific SSH key
4. Update an SSH key
5. Delete an SSH key

IMPORTANT: SSH Keys API has special authentication requirements:
- ❌ CANNOT use Organization Tokens (AT-*)
- ✅ MUST use User Tokens or Team Tokens
- ✅ MUST have 'manage VCS settings' permission

Before running this script:
1. Create a User Token in Terraform Cloud:
   - Go to User Settings → Tokens (not Organization Settings)
   - Create new token with VCS management permissions
2. Set TFE_TOKEN environment variable with your User token (not Organization token!)
3. Set TFE_ORG environment variable with your organization name
4. Set SSH_PRIVATE_KEY environment variable with your SSH private key
"""

import os
import sys

# Add the source directory to the path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tfe import TFEClient, TFEConfig
from tfe.errors import NotFound, TFEError
from tfe.models import SSHKeyCreateOptions, SSHKeyListOptions, SSHKeyUpdateOptions

# Configuration
TFE_TOKEN = os.getenv("TFE_TOKEN")
TFE_ORG = os.getenv("TFE_ORG")

# SSH private key from environment variable (API expects private key, not public)
SSH_KEY_VALUE = os.getenv("SSH_PRIVATE_KEY")


def check_token_type(token):
    """Check and validate token type for SSH Keys API."""
    print("🔍 Token Analysis:")
    if token.startswith("AT-"):
        print("   Token Type: Organization Token (AT-*)")
        print("   ❌ SSH Keys API does NOT support Organization Tokens")
        print("   💡 Please create a User Token instead")
        print("")
        print("🔧 To create a User Token:")
        print("   1. Go to Terraform Cloud → User Settings → Tokens")
        print("   2. Create new token with VCS management permissions")
        print("   3. Replace TFE_TOKEN environment variable")
        return False
    elif token.startswith("TF-"):
        print("   Token Type: User Token (TF-*)")
        print("   ✅ SSH Keys API supports User Tokens")
        return True
    elif ".atlasv1." in token:
        print("   Token Type: User/Team Token (.atlasv1. format)")
        print("   ✅ SSH Keys API supports User/Team Tokens")
        return True
    else:
        print(f"   Token Type: Unknown format ({token[:10]}...)")
        print("   💡 Expected User Token (TF-*) or Team Token")
        return True  # Allow unknown formats to try


def main():
    """Main function demonstrating SSH Keys API usage."""

    # Validate environment variables
    if not TFE_TOKEN:
        print("❌ Error: TFE_TOKEN environment variable is required")
        print("💡 Create a User Token (not Organization Token) in Terraform Cloud")
        sys.exit(1)

    if not TFE_ORG:
        print("❌ Error: TFE_ORG environment variable is required")
        sys.exit(1)

    if not SSH_KEY_VALUE:
        print("❌ Error: SSH_PRIVATE_KEY environment variable is required")
        print("💡 Provide a valid SSH private key for testing")
        sys.exit(1)

    # Check token type first
    if not check_token_type(TFE_TOKEN):
        sys.exit(1)

    # Initialize the TFE client
    config = TFEConfig(token=TFE_TOKEN)
    client = TFEClient(config)

    print(f"\nSSH Keys API Example for organization: {TFE_ORG}")
    print("=" * 50)

    try:
        # 1. List existing SSH keys
        print("\n1. Listing SSH keys...")
        ssh_keys = client.ssh_keys.list(TFE_ORG)
        print(f"✅ Found {len(ssh_keys.items)} SSH keys:")
        for key in ssh_keys.items:
            print(f"  - ID: {key.id}, Name: {key.name}")

        # 2. Create a new SSH key
        print("\n2. Creating a new SSH key...")
        create_options = SSHKeyCreateOptions(
            name="Python TFE Example SSH Key", value=SSH_KEY_VALUE
        )

        new_key = client.ssh_keys.create(TFE_ORG, create_options)
        print(f"✅ Created SSH key: {new_key.id} - {new_key.name}")

        # 3. Read the SSH key we just created
        print("\n3. Reading the SSH key...")
        read_key = client.ssh_keys.read(new_key.id)
        print(f"✅ Read SSH key: {read_key.id} - {read_key.name}")

        # 4. Update the SSH key
        print("\n4. Updating the SSH key...")
        update_options = SSHKeyUpdateOptions(name="Updated Python TFE Example SSH Key")

        updated_key = client.ssh_keys.update(new_key.id, update_options)
        print(f"✅ Updated SSH key: {updated_key.id} - {updated_key.name}")

        # 5. Delete the SSH key
        print("\n5. Deleting the SSH key...")
        client.ssh_keys.delete(new_key.id)
        print(f"✅ Deleted SSH key: {new_key.id}")

        # 6. Verify deletion by listing again
        print("\n6. Verifying deletion...")
        ssh_keys_after = client.ssh_keys.list(TFE_ORG)
        print(f"✅ SSH keys after deletion: {len(ssh_keys_after.items)}")

        # 7. Demonstrate pagination with options
        print("\n7. Demonstrating pagination options...")
        list_options = SSHKeyListOptions(page_size=5, page_number=1)
        paginated_keys = client.ssh_keys.list(TFE_ORG, list_options)
        print(f"✅ Page 1 with page size 5: {len(paginated_keys.items)} keys")
        print(f"   Total pages: {paginated_keys.total_pages}")
        print(f"   Total count: {paginated_keys.total_count}")

        print("\n🎉 SSH Keys API example completed successfully!")

    except NotFound as e:
        print(f"\n❌ SSH Keys API Error: {e}")
        print("\n💡 This error usually means:")
        print("   - Using Organization Token (not allowed)")
        print("   - SSH Keys feature not available")
        print("   - Insufficient permissions")
        print("\n🔧 Try using a User Token instead of Organization Token")
        sys.exit(1)

    except TFEError as e:
        print(f"\n❌ TFE API Error: {e}")
        if hasattr(e, "status"):
            if e.status == 403:
                print("💡 Permission denied - check token type and permissions")
            elif e.status == 401:
                print("💡 Authentication failed - check token validity")
            elif e.status == 422:
                print("💡 Validation error - check SSH key format")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
