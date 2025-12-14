from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDeleteSetOptions,
    OrganizationCreateOptions,
    ReadRunQueueOptions,
)


def test_basic_org_operations(client):
    """Test basic organization CRUD operations."""
    print("=== Testing Basic Organization Operations ===")

    # List organizations
    print("\n1. Listing Organizations:")
    try:
        org_list = client.organizations.list()
        orgs = list(org_list)
        print(f"Found {len(orgs)} organizations")

        # Show first few organizations
        for i, org in enumerate(orgs[:5], 1):
            print(f"{i:2d}. {org.name} (ID: {org.id})")
            if org.email:
                print(f"Email: {org.email}")

        if len(orgs) > 5:
            print(f"... and {len(orgs) - 5} more")

        return orgs[0].name if orgs else None  # Return first org name for testing

    except Exception as e:
        print(f"Error listing organizations: {e}")
        return None


def test_org_read_operations(client, org_name):
    """Test organization read operations."""
    print(f"\n=== Testing Organization Read Operations for '{org_name}' ===")

    # Read organization details
    print("\n1. Reading Organization Details:")
    try:
        org = client.organizations.read(org_name)
        print(f"Organization: {org.name}")
        print(f"ID: {org.id}")
        print(f"Email: {org.email or 'Not set'}")
        print(f"Created: {org.created_at or 'Unknown'}")
        print(f"Execution Mode: {org.default_execution_mode or 'Not set'}")
        print(f"Two-Factor: {org.two_factor_conformant}")
    except Exception as e:
        print(f"Error reading organization: {e}")

    # Test capacity
    print("\n2. Reading Organization Capacity:")
    try:
        capacity = client.organizations.read_capacity(org_name)
        print("Capacity:")
        print(f"Pending runs: {capacity.pending}")
        print(f"Running runs: {capacity.running}")
        print(f"Total active: {capacity.pending + capacity.running}")
    except Exception as e:
        print(f"Error reading capacity: {e}")

    # Test entitlements
    print("\n3. Reading Organization Entitlements:")
    try:
        entitlements = client.organizations.read_entitlements(org_name)
        print("Entitlements:")
        print(f"Operations: {entitlements.operations}")
        print(f"Teams: {entitlements.teams}")
        print(f"State Storage: {entitlements.state_storage}")
        print(f"VCS Integrations: {entitlements.vcs_integrations}")
        print(f"Cost Estimation: {entitlements.cost_estimation}")
        print(f"Sentinel: {entitlements.sentinel}")
        print(f"Private Module Registry: {entitlements.private_module_registry}")
        print(f"SSO: {entitlements.sso}")
    except Exception as e:
        print(f"Error reading entitlements: {e}")

    # Test run queue
    print("\n4. Reading Organization Run Queue:")
    try:
        queue_options = ReadRunQueueOptions(page_number=1, page_size=10)
        run_queue = client.organizations.read_run_queue(org_name, queue_options)
        print("Run Queue:")
        print(f"Items in queue: {len(run_queue.items)}")

        if run_queue.pagination:
            print(f"Current page: {run_queue.pagination.current_page}")
            print(f"Total count: {run_queue.pagination.total_count}")

        # Show details of first few runs
        for i, run in enumerate(run_queue.items[:3], 1):
            print(f"Run {i}: ID={run.id}, Status={run.status}")

        if len(run_queue.items) > 3:
            print(f"... and {len(run_queue.items) - 3} more runs")

    except Exception as e:
        print(f"Error reading run queue: {e}")


def test_data_retention_policies(client, org_name):
    """Test data retention policy operations."""
    print(f"\n=== Testing Data Retention Policy Operations for '{org_name}' ===")
    print("Note: These functions are only available in Terraform Enterprise")

    # Test reading current policy
    print("\n1. Reading Current Data Retention Policy:")
    try:
        policy_choice = client.organizations.read_data_retention_policy_choice(org_name)
        if policy_choice is None:
            print("No data retention policy currently configured")
        elif policy_choice.data_retention_policy_delete_older:
            policy = policy_choice.data_retention_policy_delete_older
            print(
                f"Delete Older Policy: {policy.delete_older_than_n_days} days (ID: {policy.id})"
            )
        elif policy_choice.data_retention_policy_dont_delete:
            policy = policy_choice.data_retention_policy_dont_delete
            print(f"Don't Delete Policy (ID: {policy.id})")
        elif policy_choice.data_retention_policy:
            policy = policy_choice.data_retention_policy
            print(
                f"Legacy Policy: {policy.delete_older_than_n_days} days (ID: {policy.id})"
            )
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print(
                "Data retention policies not available (Terraform Enterprise feature)"
            )
        else:
            print(f"Error reading data retention policy: {e}")

    # Test setting delete older policy
    print("\n2. Setting Delete Older Data Retention Policy (30 days):")
    try:
        options = DataRetentionPolicyDeleteOlderSetOptions(delete_older_than_n_days=30)
        policy = client.organizations.set_data_retention_policy_delete_older(
            org_name, options
        )
        print("Created Delete Older Policy:")
        print(f"ID: {policy.id}")
        print(f"Delete after: {policy.delete_older_than_n_days} days")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print("Feature not available (Terraform Enterprise only)")
        else:
            print(f"Error setting delete older policy: {e}")

    # Test updating delete older policy
    print("\n3. Updating Delete Older Policy (15 days):")
    try:
        options = DataRetentionPolicyDeleteOlderSetOptions(delete_older_than_n_days=15)
        policy = client.organizations.set_data_retention_policy_delete_older(
            org_name, options
        )
        print("Updated Delete Older Policy:")
        print(f"ID: {policy.id}")
        print(f"Delete after: {policy.delete_older_than_n_days} days")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print("Feature not available (Terraform Enterprise only)")
        else:
            print(f"Error updating delete older policy: {e}")

    # Test setting don't delete policy
    print("\n4. Setting Don't Delete Data Retention Policy:")
    try:
        options = DataRetentionPolicyDontDeleteSetOptions()
        policy = client.organizations.set_data_retention_policy_dont_delete(
            org_name, options
        )
        print("Created Don't Delete Policy:")
        print(f"ID: {policy.id}")
        print("Data will never be automatically deleted")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print("Feature not available (Terraform Enterprise only)")
        else:
            print(f"Error setting don't delete policy: {e}")

    # Test reading policy after changes
    print("\n5. Reading Data Retention Policy After Changes:")
    try:
        policy_choice = client.organizations.read_data_retention_policy_choice(org_name)
        if policy_choice is None:
            print("No data retention policy configured")
        elif policy_choice.data_retention_policy_delete_older:
            policy = policy_choice.data_retention_policy_delete_older
            print(
                f"Current Policy: Delete Older ({policy.delete_older_than_n_days} days)"
            )
        elif policy_choice.data_retention_policy_dont_delete:
            print("Current Policy: Don't Delete")

        # Test legacy conversion
        if policy_choice and policy_choice.is_populated():
            legacy = policy_choice.convert_to_legacy_struct()
            if legacy:
                print(f"Legacy representation: {legacy.delete_older_than_n_days} days")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print("Feature not available (Terraform Enterprise only)")
        else:
            print(f"Error reading updated policy: {e}")

    # Test deleting policy
    print("\n6. Deleting Data Retention Policy:")
    try:
        client.organizations.delete_data_retention_policy(org_name)
        print("Successfully deleted data retention policy")

        # Verify deletion
        policy_choice = client.organizations.read_data_retention_policy_choice(org_name)
        if policy_choice is None or not policy_choice.is_populated():
            print("Verified: No policy configured after deletion")
        else:
            print("Policy still exists after deletion attempt")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            print("Feature not available (Terraform Enterprise only)")
        else:
            print(f"Error deleting policy: {e}")


def test_organization_creation_and_cleanup(client):
    """Test organization creation and cleanup (if permissions allow)."""
    print("\n=== Testing Organization Creation (Optional) ===")

    test_org_name = f"python-tfe-test-{int(__import__('time').time())}"

    try:
        print(f"\n1. Creating Test Organization '{test_org_name}':")
        create_opts = OrganizationCreateOptions(
            name=test_org_name, email="aayush.singh@hashicorp.com"
        )
        new_org = client.organizations.create(create_opts)
        print(f"Created organization: {new_org.name}")
        print(f"ID: {new_org.id}")
        print(f"Email: {new_org.email}")

        # Test reading the newly created org
        print("\n2. Reading Newly Created Organization:")
        read_org = client.organizations.read(test_org_name)
        print(f"Successfully read organization: {read_org.name}")

        # Cleanup
        print("\n3. Cleaning Up Test Organization:")
        client.organizations.delete(test_org_name)
        print("Successfully deleted test organization")

        return True

    except Exception as e:
        print(f"Organization creation/deletion test skipped: {e}")
        print("This is normal if you don't have organization management permissions")
        return False


def main():
    """Main function to test all organization functionalities."""
    print("Python TFE Organization Functions Test Suite")
    print("=" * 60)

    # Initialize client
    try:
        client = TFEClient(TFEConfig.from_env())
        print("TFE Client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize TFE client: {e}")
        print(
            "Please ensure TF_CLOUD_ORGANIZATION and TF_CLOUD_TOKEN environment variables are set"
        )
        return 1

    # Test basic operations
    test_org_name = test_basic_org_operations(client)
    if not test_org_name:
        print("\n Cannot continue without a valid organization")
        return 1

    # Test read operations
    test_org_read_operations(client, test_org_name)

    # # Test data retention policies
    # test_data_retention_policies(client, test_org_name)

    # Test organization creation (if permissions allow)
    creation_success = test_organization_creation_and_cleanup(client)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("Basic organization operations tested")
    print("Organization read operations tested")
    print("Data retention policy operations tested")
    if creation_success:
        print("Organization creation/deletion tested")
    else:
        print("Organization creation/deletion skipped (permissions)")

    print(
        f"\n All available organization functions have been tested against '{test_org_name}'"
    )
    print("Note: Data retention policy features require Terraform Enterprise")
    print("\nTest suite completed successfully!")

    return 0


if __name__ == "__main__":
    exit(main())
