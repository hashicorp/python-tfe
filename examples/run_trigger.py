import time
import traceback

from tfe import TFEClient, TFEConfig
from tfe.models.run_trigger import (
    RunTriggerCreateOptions,
    RunTriggerFilterOp,
    RunTriggerIncludeOp,
    RunTriggerListOptions,
)
from tfe.models.workspace import Workspace


def run_trigger_list(client, workspace_id):
    """Test run trigger list with all options combined."""
    print(
        f"=== Testing Run Trigger List Comprehensive Options for workspace '{workspace_id}' ==="
    )

    print("\n1. Listing Run Triggers with options:")
    try:
        options = RunTriggerListOptions(
            page_number=1,
            page_size=10,
            run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND,
            include=[
                RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE,
                RunTriggerIncludeOp.RUN_TRIGGER_SOURCEABLE,
            ],
        )

        run_trigger_list = client.run_triggers.list(workspace_id, options)
        run_triggers = list(run_trigger_list)
        print(
            f"   ✓ Found {len(run_triggers)} inbound run triggers with comprehensive options"
        )

        for i, trigger in enumerate(run_triggers, 1):
            print(
                f"   {i:2d}. Source: {trigger.sourceable_name} → Target: {trigger.workspace_name}"
            )
            print(f"       Trigger ID: {trigger.id}")
            print(f"       Created: {trigger.created_at}")

            # Show sourceable workspace details if available
            if trigger.sourceable:
                print(
                    f"       Source Workspace: {trigger.sourceable.name} (ID: {trigger.sourceable.id})"
                )
                if trigger.sourceable.organization:
                    print(
                        f"       Source Organization: {trigger.sourceable.organization}"
                    )

            # Show target workspace details if available
            if trigger.workspace:
                print(
                    f"       Target Workspace: {trigger.workspace.name} (ID: {trigger.workspace.id})"
                )
                if trigger.workspace.organization:
                    print(
                        f"       Target Organization: {trigger.workspace.organization}"
                    )

        # Also try listing outbound triggers (without include params - not supported)
        print("\n   Listing Outbound Run Triggers:")
        outbound_options = RunTriggerListOptions(
            page_number=1,
            page_size=5,
            run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND,
        )

        outbound_triggers = list(
            client.run_triggers.list(workspace_id, outbound_options)
        )
        print(f"   ✓ Found {len(outbound_triggers)} outbound run triggers")

        for i, trigger in enumerate(outbound_triggers, 1):
            print(
                f"   {i:2d}. Source: {trigger.sourceable_name} → Target: {trigger.workspace_name}"
            )

    except Exception as e:
        print(f"   Error listing run triggers comprehensively: {e}")
        traceback.print_exc()


def run_trigger_create(client, workspace_id, source_workspace_id):
    """Create a comprehensive run trigger that demonstrates all available features."""
    print(
        f"\n=== Creating Run Trigger from workspace '{source_workspace_id}' to '{workspace_id}' ==="
    )

    try:
        source_workspace = Workspace(
            id=source_workspace_id,
            name=f"source-workspace-{int(time.time())}",
            organization="prab-sandbox01",  # This would typically be the actual org name
        )

        options = RunTriggerCreateOptions(sourceable=source_workspace)

        print("\n2. Creating run trigger with the following configuration:")

        created_trigger = client.run_triggers.create(workspace_id, options)

        print("\n   ✓ Successfully created run trigger!")
        print(f"     Trigger ID: {created_trigger.id}")
        print(f"     Source: {created_trigger.sourceable_name}")
        print(f"     Target: {created_trigger.workspace_name}")
        print(f"     Created At: {created_trigger.created_at}")

        # Display additional details
        if created_trigger.sourceable:
            print(
                f"     Source Workspace: {created_trigger.sourceable.name} (ID: {created_trigger.sourceable.id})"
            )

        if created_trigger.workspace:
            print(
                f"     Target Workspace: {created_trigger.workspace.name} (ID: {created_trigger.workspace.id})"
            )

        return (
            created_trigger.id,
            created_trigger.sourceable_name,
            created_trigger.workspace_name,
        )

    except Exception as e:
        print(f"   Error creating run trigger: {e}")
        traceback.print_exc()
        return None, None, None


def run_trigger_read(client, trigger_id, source_name, target_name):
    """Read and display details of a specific run trigger."""
    try:
        print(
            f"\n3. Reading Run Trigger '{source_name} → {target_name}' (ID: {trigger_id})"
        )
        read_trigger = client.run_triggers.read(trigger_id)

        print("\n   ✓ Successfully read run trigger:")
        print(f"     Trigger ID: {read_trigger.id}")
        print(f"     Type: {read_trigger.type}")
        print(f"     Source: {read_trigger.sourceable_name}")
        print(f"     Target: {read_trigger.workspace_name}")
        print(f"     Created At: {read_trigger.created_at}")

        # Show detailed workspace information
        if read_trigger.sourceable:
            print("     Source Workspace Details:")
            print(f"       - Name: {read_trigger.sourceable.name}")
            print(f"       - ID: {read_trigger.sourceable.id}")
            if read_trigger.sourceable.organization:
                print(f"       - Organization: {read_trigger.sourceable.organization}")

        if read_trigger.workspace:
            print("     Target Workspace Details:")
            print(f"       - Name: {read_trigger.workspace.name}")
            print(f"       - ID: {read_trigger.workspace.id}")
            if read_trigger.workspace.organization:
                print(f"       - Organization: {read_trigger.workspace.organization}")

        # Show sourceable choice if available
        if read_trigger.sourceable_choice and read_trigger.sourceable_choice.workspace:
            choice_ws = read_trigger.sourceable_choice.workspace
            print("     Sourceable Choice Workspace:")
            print(f"       - Name: {choice_ws.name}")
            print(f"       - ID: {choice_ws.id}")

    except Exception as e:
        print(f"   Error reading run trigger '{source_name} → {target_name}': {e}")
        traceback.print_exc()


def run_trigger_delete(client, trigger_id, source_name, target_name):
    """Delete a specific run trigger."""
    try:
        print(
            f"\n4. Deleting Run Trigger '{source_name} → {target_name}' (ID: {trigger_id})"
        )
        client.run_triggers.delete(trigger_id)
        print(
            f"\n   ✓ Successfully deleted run trigger: {source_name} → {target_name} (ID: {trigger_id})"
        )
        return True

    except Exception as e:
        print(f"   Error deleting run trigger '{source_name} → {target_name}': {e}")
        traceback.print_exc()
        return False


def main():
    """Main function to demonstrate comprehensive run trigger operations."""
    print("Run Trigger - Comprehensive Example")
    print("=" * 50)

    # Initialize client
    config = TFEConfig()
    client = TFEClient(config)

    # Replace these with actual workspace IDs from your organization
    target_workspace_id = "target_workspace_id"  # Workspace that will receive triggers
    source_workspace_id = "source_workspace_id"  # Workspace that will trigger runs

    print(f"Using target workspace: {target_workspace_id}")
    print(f"Using source workspace: {source_workspace_id}")
    print(
        "\nNOTE: Please replace these with actual workspace IDs from your organization"
    )

    try:
        # Test comprehensive list operations
        run_trigger_list(client, target_workspace_id)

        # Create a new run trigger
        trigger_id, source_name, target_name = run_trigger_create(
            client, target_workspace_id, source_workspace_id
        )

        # Read the created trigger
        if trigger_id:
            run_trigger_read(client, trigger_id, source_name, target_name)

            # Clean up - delete the created trigger
            run_trigger_delete(client, trigger_id, source_name, target_name)

    except Exception as e:
        print(f"\nExample failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
