#!/usr/bin/env python3
"""
Complete OAuth Token Testing Suite

This file contains individual tests for all 4 OAuth token functions:

FUNCTIONS AVAILABLE FOR TESTING:
1. list() - List OAuth tokens for an organization
2. read() - Read an OAuth token by its ID
3. update() - Update an existing OAuth token
4. delete() - Delete an OAuth token by its ID

USAGE:
- Uncomment specific test sections to test individual functions
- Modify test data (token IDs, SSH keys, etc.) as needed for your environment
- Ensure you have proper TFE credentials and organization access
- Note: OAuth tokens are automatically created when OAuth clients are created

PREREQUISITES:
- You need existing OAuth clients/tokens to test with
- Set TFE_TOKEN and TFE_ADDRESS environment variables
- Organization 'aayush-test' should exist with OAuth clients
"""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig
from pytfe.errors import NotFound
from pytfe.models import OAuthTokenUpdateOptions


def main():
    """Test all OAuth token functions individually."""

    print("=" * 80)
    print("OAUTH TOKEN COMPLETE TESTING SUITE")
    print("=" * 80)
    print("Testing ALL 4 functions in src/tfe/resources/oauth_token.py")
    print("Comprehensive test coverage for all OAuth token operations")
    print("=" * 80)

    # Initialize the TFE client
    client = TFEClient(TFEConfig.from_env())
    organization_name = "aayush-test"  # Using specified organization

    # Variables to store found resources for dependent tests
    test_token_id = None

    # =====================================================
    # TEST 1: LIST OAUTH TOKENS
    # =====================================================
    print("\n1. Testing list() function:")
    try:
        for token in client.oauth_tokens.list(organization_name):
            print(f"Token ID: {token.id}")
            print(f"Service Provider User: {token.service_provider_user}")
            print(f"Has SSH Key: {token.has_ssh_key}")
            print(f"Created: {token.created_at}")
            if token.oauth_client:
                print(f"OAuth Client: {token.oauth_client.id}")

            # Store first token for subsequent tests
            if token and not test_token_id:
                test_token_id = token.id
                print(f"\n   Using token {test_token_id} for subsequent tests \n")

    except NotFound:
        print(
            "No OAuth tokens found (organization may not exist or no tokens available)"
        )
    except Exception as e:
        print(f"Error: {e}")

    # =====================================================
    # TEST 2: READ OAUTH TOKEN
    # =====================================================
    if test_token_id:
        print("\n2. Testing read() function:")
        try:
            token = client.oauth_tokens.read(test_token_id)
            print(f"Read OAuth token: {token.id}")
            print(f"Service Provider User: {token.service_provider_user}")
            print(f"Has SSH Key: {token.has_ssh_key}")
            print(f"Created: {token.created_at}")
            if token.oauth_client:
                print(f"OAuth Client: {token.oauth_client.id}")

        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\n2. Testing read() function:")
        print("Skipped - No OAuth token available to read")

    # =====================================================
    # TEST 3: UPDATE OAUTH TOKEN
    # =====================================================
    if test_token_id:
        print("\n3. Testing update() function:")
        try:
            # Test updating with SSH key
            print("Testing update with SSH key...")
            ssh_key = """-----BEGIN RSA PRIVATE KEY-----
-----END RSA PRIVATE KEY-----"""

            options = OAuthTokenUpdateOptions(private_ssh_key=ssh_key)
            updated_token = client.oauth_tokens.update(test_token_id, options)
            print(f"Updated OAuth token: {updated_token.id}")
            print(f"Has SSH Key after update: {updated_token.has_ssh_key}")

            # Test updating without SSH key (no changes)
            print("\n   Testing update without changes...")
            options_empty = OAuthTokenUpdateOptions()
            updated_token_2 = client.oauth_tokens.update(test_token_id, options_empty)
            print(f"Updated OAuth token (no changes): {updated_token_2.id}")

        except Exception as e:
            print(f"Error: {e}")
            print(
                "Note: This may fail if the SSH key format is invalid or constraints apply"
            )
    else:
        print("\n3. Testing update() function:")
        print("Skipped - No OAuth token available to update")

    # =====================================================
    # TEST 4: DELETE OAUTH TOKEN
    # =====================================================
    print("\n4. Testing delete() function:")

    # Using specific OAuth token ID for deletion
    delete_token_id = "ot-WQf5ARHA1Qxzo9d4"

    try:
        print(f"Attempting to delete OAuth token: {delete_token_id}")
        client.oauth_tokens.delete(delete_token_id)
        print(f"Successfully deleted OAuth token: {delete_token_id}")

        # Verify deletion by trying to read the token
        try:
            client.oauth_tokens.read(delete_token_id)
            print("Token still exists after deletion!")
        except NotFound:
            print("Confirmed token was deleted - no longer accessible")
        except Exception as e:
            print(f"? Verification failed: {e}")

    except Exception as e:
        print(f"Error deleting token: {e}")

    # Uncomment the following section ONLY if you have a disposable OAuth token
    # WARNING: This will permanently delete the OAuth token!
    """
    if test_token_id:
        try:
            print(f"Attempting to delete OAuth token: {test_token_id}")
            client.oauth_tokens.delete(test_token_id)
            print(f"Successfully deleted OAuth token: {test_token_id}")

            # Verify deletion by trying to read the token
            try:
                client.oauth_tokens.read(test_token_id)
                print(f"Token still exists after deletion!")
            except NotFound:
                print(f"Confirmed token was deleted - no longer accessible")
            except Exception as e:
                print(f"? Verification failed: {e}")

        except Exception as e:
            print(f"Error deleting token: {e}")
    else:
        print("Skipped - No OAuth token available to delete")
    """

    # =====================================================
    # SUMMARY
    # =====================================================
    print("\n" + "=" * 80)
    print("OAUTH TOKEN TESTING COMPLETE")
    print("=" * 80)
    print("Functions tested:")
    print("1. list() - List OAuth tokens for organization")
    print("2. read() - Read OAuth token by ID")
    print("3. update() - Update existing OAuth token")
    print("4. delete() - Delete OAuth token (testing with ot-WQf5ARHA1Qxzo9d4)")
    print("")
    print("All OAuth token functions have been tested!")
    print("Check the output above for any errors or warnings.")
    print("=" * 80)


if __name__ == "__main__":
    main()
