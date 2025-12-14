#!/usr/bin/env python3
"""Reserved Tag Keys Example Script.

This script demonstrates how to use the Reserved Tag Keys API to:
1. List all reserved tag keys for an organization
2. Create a new reserved tag key
3. Update a reserved tag key
4. Delete a reserved tag key

Before running this script:
1. Set TFE_TOKEN environment variable with your Terraform Cloud API token
2. Set TFE_ORG environment variable with your organization name
"""

import os
import sys

# Add the source directory to the path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.models import (
    ReservedTagKeyCreateOptions,
    ReservedTagKeyListOptions,
    ReservedTagKeyUpdateOptions,
)

# Configuration
TFE_TOKEN = os.getenv("TFE_TOKEN")
TFE_ORG = os.getenv("TFE_ORG")


def main():
    """Main function demonstrating Reserved Tag Keys API usage."""

    # Validate environment variables
    if not TFE_TOKEN:
        print("Error: TFE_TOKEN environment variable is required")
        sys.exit(1)

    if not TFE_ORG:
        print("Error: TFE_ORG environment variable is required")
        sys.exit(1)

    # Initialize the TFE client
    config = TFEConfig(token=TFE_TOKEN)
    client = TFEClient(config)

    print(f"Reserved Tag Keys API Example for organization: {TFE_ORG}")
    print("=" * 60)

    try:
        # 1. List existing reserved tag keys
        print("\n1. Listing reserved tag keys...")
        reserved_tag_keys = client.reserved_tag_key.list(TFE_ORG)
        print(f"Found {len(reserved_tag_keys.items)} reserved tag keys:")
        for rtk in reserved_tag_keys.items:
            print(
                f"  - ID: {rtk.id}, Key: {rtk.key}, Disable Overrides: {rtk.disable_overrides}"
            )

        # 2. Create a new reserved tag key
        print("\n2. Creating a new reserved tag key...")
        create_options = ReservedTagKeyCreateOptions(
            key="python-tfe-example", disable_overrides=False
        )

        new_rtk = client.reserved_tag_key.create(TFE_ORG, create_options)
        print(f"Created reserved tag key: {new_rtk.id} - {new_rtk.key}")
        print(f"Disable Overrides: {new_rtk.disable_overrides}")

        # 3. Update the reserved tag key
        print("\n3. Updating the reserved tag key...")
        update_options = ReservedTagKeyUpdateOptions(
            key="python-tfe-example-updated", disable_overrides=True
        )

        updated_rtk = client.reserved_tag_key.update(new_rtk.id, update_options)
        print(f"Updated reserved tag key: {updated_rtk.id} - {updated_rtk.key}")
        print(f"Disable Overrides: {updated_rtk.disable_overrides}")

        # 4. Delete the reserved tag key
        print("\n4. Deleting the reserved tag key...")
        client.reserved_tag_key.delete(new_rtk.id)
        print(f"Deleted reserved tag key: {new_rtk.id}")

        # 5. Verify deletion by listing again
        print("\n5. Verifying deletion...")
        reserved_tag_keys_after = client.reserved_tag_key.list(TFE_ORG)
        print(f"Reserved tag keys after deletion: {len(reserved_tag_keys_after.items)}")

        # 6. Demonstrate pagination with options
        print("\n6. Demonstrating pagination options...")
        list_options = ReservedTagKeyListOptions(page_size=5, page_number=1)
        paginated_rtks = client.reserved_tag_key.list(TFE_ORG, list_options)
        print(f"Page 1 with page size 5: {len(paginated_rtks.items)} keys")
        print(f"Total pages: {paginated_rtks.total_pages}")
        print(f"Total count: {paginated_rtks.total_count}")

        print("\n Reserved Tag Keys API example completed successfully!")

    except NotImplementedError as e:
        print(f"\n Note: {e}")
        print("This is expected - the read operation is not supported by the API.")

    except TFEError as e:
        print(f"\n TFE API Error: {e}")
        if hasattr(e, "status"):
            if e.status == 403:
                print("Permission denied - check token permissions")
            elif e.status == 401:
                print("Authentication failed - check token validity")
            elif e.status == 422:
                print("Validation error - check reserved tag key format")
        sys.exit(1)

    except Exception as e:
        print(f"\n Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
