#!/usr/bin/env python3
"""
Comprehensive Workspace Management Example

This example demonstrates all available workspace operations in the Python TFE SDK,
including CRUD operations, VCS management, locking/unlocking, SSH key management,
and advanced configuration options.

Usage:
    python examples/workspace_comprehensive_example.py

Requirements:
    - TFE_TOKEN environment variable set
    - TFE_ADDRESS environment variable set (optional, defaults to Terraform Cloud)
    - An existing organization in your Terraform Cloud/Enterprise instance
"""

import os
import sys
from datetime import datetime

# Add the source directory to the path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tfe import TFEClient, TFEConfig
from tfe.types import (
    DataRetentionPolicyDeleteOlderSetOptions,
    DataRetentionPolicyDontDeleteSetOptions,
    ExecutionMode,
    Tag,
    TagBinding,
    VCSRepo,
    WorkspaceAddRemoteStateConsumersOptions,
    WorkspaceAddTagBindingsOptions,
    WorkspaceAddTagsOptions,
    WorkspaceCreateOptions,
    WorkspaceIncludeOpt,
    WorkspaceListOptions,
    WorkspaceListRemoteStateConsumersOptions,
    WorkspaceLockOptions,
    WorkspaceReadOptions,
    WorkspaceRemoveRemoteStateConsumersOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
    WorkspaceUpdateRemoteStateConsumersOptions,
)


class WorkspaceManager:
    """Comprehensive workspace management utility."""

    def __init__(self):
        """Initialize the workspace manager."""
        self.client = TFEClient(TFEConfig.from_env())
        self.workspaces = self.client.workspaces

    def demonstrate_all_operations(self, organization: str):
        """Demonstrate all workspace operations."""
        print("Starting Comprehensive Workspace Operations Demo")
        print("=" * 60)

        try:
            # 1. List existing workspaces
            self.demo_list_operations(organization)

            # 2. Create new workspace
            workspace = self.demo_create_operations(organization)
            workspace_id = workspace.id
            workspace_name = workspace.name

            # 3. Read operations
            self.demo_read_operations(organization, workspace_name, workspace_id)

            # 4. Update operations
            self.demo_update_operations(organization, workspace_name, workspace_id)

            # 5. VCS operations
            self.demo_vcs_operations(organization, workspace_name, workspace_id)

            # 6. Locking operations
            self.demo_locking_operations(workspace_id)

            # 7. SSH key operations (commented out as it requires existing SSH keys)
            # self.demo_ssh_key_operations(workspace_id)

            # 8. Remote state consumer operations
            self.demo_remote_state_consumer_operations(organization, workspace_id)

            # 9. Tag operations
            self.demo_tag_operations(workspace_id)

            # 9B. Tag binding operations
            self.demo_tag_binding_operations(workspace_id)

            # 9C. Data retention policy operations
            self.demo_data_retention_policy_operations(workspace_id)

            # 10. Cleanup - delete the test workspace
            self.demo_delete_operations(organization, workspace_name, workspace_id)

        except Exception as e:
            print(f"Error during demo: {e}")
            raise

        print("\n Comprehensive workspace demo completed successfully!")

    def demo_list_operations(self, organization: str):
        """Demonstrate workspace listing operations."""
        print("\n 1. WORKSPACE LISTING OPERATIONS")
        print("-" * 40)

        # Basic listing
        print(" Listing all workspaces...")
        options = WorkspaceListOptions()
        workspaces = list(self.workspaces.list(organization, options=options))
        print(f"   Found {len(workspaces)} workspaces")

        for ws in workspaces[:3]:  # Show first 3
            print(f"   • {ws.name} (ID: {ws.id[:10]}...)")
            print(f"     - Execution Mode: {ws.execution_mode}")
            print(f"     - Auto Apply: {ws.auto_apply}")
            print(f"     - Locked: {ws.locked}")

        # Advanced listing with filters
        print("\n Listing with search filters...")
        filtered_options = WorkspaceListOptions(
            search="prod",  # Search for workspaces containing "prod"
            tags="production,frontend",  # Filter by tags
            include=[WorkspaceIncludeOpt.CURRENT_RUN],  # Include current run info
            page_size=5,  # Limit results
        )

        try:
            filtered_workspaces = list(
                self.workspaces.list(organization, options=filtered_options)
            )
            print(f"   Found {len(filtered_workspaces)} workspaces matching filters")
        except Exception as e:
            print(f"   Filter search failed (expected if no matching workspaces): {e}")

    def demo_create_operations(self, organization: str):
        """Demonstrate workspace creation operations."""
        print("\n 2. WORKSPACE CREATION OPERATIONS")
        print("-" * 40)

        # Basic workspace creation
        print("🔨 Creating basic workspace...")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        workspace_name = f"demo-workspace-{timestamp}"

        basic_options = WorkspaceCreateOptions(
            name=workspace_name,
            description=f"Demo workspace created at {datetime.now()}",
            auto_apply=False,
            execution_mode=ExecutionMode.REMOTE,
            terraform_version="1.5.0",
            working_directory="terraform/",
            file_triggers_enabled=True,
            queue_all_runs=False,
            speculative_enabled=True,
            trigger_prefixes=["modules/", "shared/"],
        )

        workspace = self.workspaces.create(organization, options=basic_options)
        print(f"    Created workspace: {workspace.name}")
        print(f"    ID: {workspace.id}")
        print(f"    Description: {workspace.description}")
        print(f"    Execution Mode: {workspace.execution_mode}")
        print(f"    Auto Apply: {workspace.auto_apply}")

        return workspace

    def demo_create_with_vcs(self, organization: str):
        """Demonstrate workspace creation with VCS integration."""
        print("\n Creating workspace with VCS integration...")

        # VCS repository configuration
        vcs_repo = VCSRepo(
            identifier="your-org/your-repo",  # Replace with actual repo
            branch="main",
            oauth_token_id="ot-your-token-id",  # Replace with actual OAuth token
            ingress_submodules=False,
            tags_regex=r"v\d+\.\d+\.\d+",  # Version tag pattern
        )

        vcs_options = WorkspaceCreateOptions(
            name=f"vcs-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            description="Demo workspace with VCS integration",
            vcs_repo=vcs_repo,
            working_directory="terraform/production/",
            trigger_prefixes=["terraform/production/"],
            auto_apply=True,  # Enable auto-apply for VCS-driven workflows
        )

        try:
            vcs_workspace = self.workspaces.create(organization, options=vcs_options)
            print(f"    Created VCS workspace: {vcs_workspace.name}")
            return vcs_workspace
        except Exception as e:
            print(
                f"     VCS workspace creation failed (expected without valid OAuth token): {e}"
            )
            return None

    def demo_read_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace reading operations."""
        print("\n 3. WORKSPACE READ OPERATIONS")
        print("-" * 40)

        # Read by name
        print("📄 Reading workspace by name...")
        workspace_by_name = self.workspaces.read(organization, workspace_name)
        print(f"   Name: {workspace_by_name.name}")
        print(f"   ID: {workspace_by_name.id}")
        print(f"   Created: {workspace_by_name.created_at}")
        print(f"   Updated: {workspace_by_name.updated_at}")

        # Read by ID
        print("\n Reading workspace by ID...")
        workspace_by_id = self.workspaces.read_by_id(workspace_id)
        print(f"    Name: {workspace_by_id.name}")
        print(f"    Terraform Version: {workspace_by_id.terraform_version}")
        print(f"    Working Directory: {workspace_by_id.working_directory}")

        # Read with additional include options
        print("\n Reading workspace with include options...")
        read_options = WorkspaceReadOptions(
            include=[WorkspaceIncludeOpt.CURRENT_RUN, WorkspaceIncludeOpt.OUTPUTS]
        )

        detailed_workspace = self.workspaces.read_with_options(
            workspace_name, organization, options=read_options
        )
        print(f"    Current Run ID: {detailed_workspace.locked_by}")
        print(f"    Resource Count: {detailed_workspace.resource_count}")
        print(f"    Tag Names: {detailed_workspace.tag_names}")

    def demo_update_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace update operations."""
        print("\n 4. WORKSPACE UPDATE OPERATIONS")
        print("-" * 40)

        # Update by name
        print(" Updating workspace by name...")
        update_options = WorkspaceUpdateOptions(
            name=workspace_name,  # Required field
            description=f"Updated description at {datetime.now()}",
            auto_apply=True,  # Enable auto-apply
            terraform_version="1.6.0",  # Update Terraform version
            queue_all_runs=True,  # Enable queue all runs
            working_directory="terraform/updated/",
        )

        updated_workspace = self.workspaces.update(
            organization, workspace_name, options=update_options
        )
        print(f"    Updated workspace: {updated_workspace.name}")
        print(f"    New description: {updated_workspace.description}")
        print(f"    Auto Apply: {updated_workspace.auto_apply}")
        print(f"    Terraform Version: {updated_workspace.terraform_version}")

        # Update by ID
        print("\n Updating workspace by ID...")
        id_update_options = WorkspaceUpdateOptions(
            name=workspace_name,  # Required field
            speculative_enabled=False,  # Disable speculative plans
            operations=False,  # Switch to local execution
        )

        updated_by_id = self.workspaces.update_by_id(
            workspace_id, options=id_update_options
        )
        print(f"    Updated workspace operations: {updated_by_id.operations}")
        print(f"    Speculative enabled: {updated_by_id.speculative_enabled}")

    def demo_vcs_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate VCS connection operations."""
        print("\n 5. VCS CONNECTION OPERATIONS")
        print("-" * 40)

        # Note: These operations require existing VCS connections
        print(" VCS connection management...")

        try:
            # Remove VCS connection by name
            print("  Removing VCS connection by name...")
            remove_options = WorkspaceRemoveVCSConnectionOptions(
                id=workspace_id,
                vcs_repo=None,  # Set to None to remove
            )

            updated_workspace = self.workspaces.remove_vcs_connection(
                organization, workspace_name, options=remove_options
            )
            print(f"    VCS connection removed for: {updated_workspace.name}")

        except Exception as e:
            print(f"     VCS operation note: {e}")
            print("   (VCS operations require existing VCS configurations)")

    def demo_locking_operations(self, workspace_id: str):
        """Demonstrate workspace locking operations."""
        print("\n 6. WORKSPACE LOCKING OPERATIONS")
        print("-" * 40)

        # Lock workspace
        print(" Locking workspace...")
        lock_options = WorkspaceLockOptions(
            reason="Demo: Maintenance in progress - testing locking functionality"
        )

        try:
            locked_workspace = self.workspaces.lock(workspace_id, options=lock_options)
            print(f"    Workspace locked: {locked_workspace.name}")
            print("     Lock reason: Demo maintenance")
            print(f"    Locked status: {locked_workspace.locked}")

            # Unlock workspace
            print("\n Unlocking workspace...")
            unlocked_workspace = self.workspaces.unlock(workspace_id)
            print(f"    Workspace unlocked: {unlocked_workspace.name}")
            print(f"    Locked status: {unlocked_workspace.locked}")

        except Exception as e:
            print(f"     Locking operation failed: {e}")
            print("   (This may be expected if workspace has active runs)")

    def demo_ssh_key_operations(self, workspace_id: str):
        """Demonstrate SSH key management operations."""
        print("\n 7. SSH KEY MANAGEMENT OPERATIONS")
        print("-" * 40)

        # Note: This requires existing SSH keys in the organization
        print(" SSH key management...")
        print("     SSH key operations require existing SSH keys")
        print("     Skipping SSH key demo (requires SSH key setup)")

        # Uncomment and modify when you have SSH keys configured:
        """
        try:
            # Assign SSH key
            ssh_options = WorkspaceAssignSSHKeyOptions(
                ssh_key_id="sshkey-your-key-id"  # Replace with actual SSH key ID
            )

            workspace_with_ssh = self.workspaces.assign_ssh_key(workspace_id, options=ssh_options)
            print(f"    SSH key assigned to: {workspace_with_ssh.name}")

            # Unassign SSH key
            workspace_without_ssh = self.workspaces.unassign_ssh_key(workspace_id)
            print(f"    SSH key unassigned from: {workspace_without_ssh.name}")

        except Exception as e:
            print(f"     SSH key operation failed: {e}")
        """

    def demo_remote_state_consumer_operations(
        self, organization: str, workspace_id: str
    ):
        """Demonstrate remote state consumer management operations."""
        print("\n 7. REMOTE STATE CONSUMER OPERATIONS")
        print("-" * 40)

        try:
            # 1. List current remote state consumers
            print(" Listing current remote state consumers...")
            list_options = WorkspaceListRemoteStateConsumersOptions(page_size=10)

            current_consumers = list(
                self.workspaces.list_remote_state_consumers(workspace_id, list_options)
            )
            print(f"    Found {len(current_consumers)} current consumer(s)")

            for consumer in current_consumers:
                print(f"    Consumer: {consumer.name} (ID: {consumer.id})")

            # 2. Get real workspaces from organization for demonstration
            print("\n  Getting real workspaces for consumer demonstration...")

            # Get existing workspaces from the organization to use as examples
            from tfe.types import WorkspaceListOptions

            org_list_options = WorkspaceListOptions(page_size=5)

            try:
                # Get list of existing workspaces (excluding the current one)
                all_workspaces = list(
                    self.workspaces.list(organization, options=org_list_options)
                )

                # Filter out the current workspace and get up to 2 others for demo
                available_workspaces = [
                    ws for ws in all_workspaces if ws.id != workspace_id
                ]

                if len(available_workspaces) >= 2:
                    demo_consumer_1 = available_workspaces[0]
                    demo_consumer_2 = available_workspaces[1]

                    print("    Using real workspaces for demonstration:")
                    print(
                        f"    Consumer 1: {demo_consumer_1.name} (ID: {demo_consumer_1.id})"
                    )
                    print(
                        f"    Consumer 2: {demo_consumer_2.name} (ID: {demo_consumer_2.id})"
                    )

                    use_real_workspaces = True
                else:
                    print(
                        f"     Only {len(available_workspaces)} other workspaces available"
                    )
                    print("    Need at least 2 other workspaces for full demonstration")
                    print("     Creating minimal demo with available workspaces...")
                    use_real_workspaces = False

            except Exception as ws_error:
                print(f"    Could not fetch organization workspaces: {ws_error}")
                use_real_workspaces = False

            if not use_real_workspaces:
                # Fallback to showing the concept with mock data
                print("    Using mock workspace references for concept demonstration")
                print(
                    "    In practice, use actual workspace IDs from your organization"
                )

                # Create mock workspaces for demonstration only
                from tfe.types import Workspace

                demo_consumer_1 = Workspace(
                    id="ws-demo-consumer-1",
                    name="demo-consumer-1",
                    organization="demo-org",
                )
                demo_consumer_2 = Workspace(
                    id="ws-demo-consumer-2",
                    name="demo-consumer-2",
                    organization="demo-org",
                )

            # 3. Add remote state consumers
            print("\n Adding remote state consumers...")
            add_options = WorkspaceAddRemoteStateConsumersOptions(
                workspaces=[demo_consumer_1, demo_consumer_2]
            )

            # Note: This will fail in demo since we're using mock workspaces
            try:
                self.workspaces.add_remote_state_consumers(workspace_id, add_options)
                print("    Successfully added remote state consumers")
                print(f"    Added consumer: {demo_consumer_1.name}")
                print(f"    Added consumer: {demo_consumer_2.name}")
            except Exception as add_error:
                expected_msg = (
                    "(expected with mock data)" if not use_real_workspaces else ""
                )
                print(f"     Add operation failed {expected_msg}: {add_error}")
                if not use_real_workspaces:
                    print("    This is expected when using non-existent workspace IDs")

            # 4. List consumers after adding (would show updated list in real scenario)
            print("\n Listing consumers after adding...")
            updated_consumers = list(
                self.workspaces.list_remote_state_consumers(workspace_id, list_options)
            )
            print(f"    Current consumer count: {len(updated_consumers)}")

            # 5. Remove a remote state consumer
            print("\n Removing a remote state consumer...")
            remove_options = WorkspaceRemoveRemoteStateConsumersOptions(
                workspaces=[demo_consumer_1]
            )

            try:
                self.workspaces.remove_remote_state_consumers(
                    workspace_id, remove_options
                )
                print(f"    Successfully removed consumer: {demo_consumer_1.name}")
            except Exception as remove_error:
                expected_msg = (
                    "(expected with mock data)" if not use_real_workspaces else ""
                )
                print(f"     Remove operation failed {expected_msg}: {remove_error}")

            # 6. Update remote state consumers (replace all)
            print("\n Updating remote state consumers (replacing all)...")

            if use_real_workspaces and len(available_workspaces) >= 3:
                # Use a third real workspace if available
                demo_consumer_3 = available_workspaces[2]
                print(
                    f"    Consumer 3: {demo_consumer_3.name} (ID: {demo_consumer_3.id})"
                )
            else:
                # Create mock workspace for demonstration
                demo_consumer_3 = Workspace(
                    id="ws-demo-consumer-3",
                    name="demo-consumer-3",
                    organization="demo-org",
                )

            update_options = WorkspaceUpdateRemoteStateConsumersOptions(
                workspaces=[
                    demo_consumer_2,
                    demo_consumer_3,
                ]  # Keep consumer 2, add consumer 3
            )

            try:
                self.workspaces.update_remote_state_consumers(
                    workspace_id, update_options
                )
                print("    Successfully updated remote state consumers")
                print(
                    f"    New consumer set: {demo_consumer_2.name}, {demo_consumer_3.name}"
                )
            except Exception as update_error:
                expected_msg = (
                    "(expected with mock data)" if not use_real_workspaces else ""
                )
                print(f"     Update operation failed {expected_msg}: {update_error}")

            # 7. Final listing to show results
            print("\n Final remote state consumer listing...")
            final_consumers = list(
                self.workspaces.list_remote_state_consumers(workspace_id, list_options)
            )
            print(f"    Final consumer count: {len(final_consumers)}")

            for consumer in final_consumers:
                print(f"    Final consumer: {consumer.name} (ID: {consumer.id})")

        except Exception as e:
            print(f"    Remote state consumer operations failed: {e}")

    def demo_tag_operations(self, workspace_id: str):
        """Demonstrate comprehensive workspace tag management operations."""
        print("\n 8. WORKSPACE TAG OPERATIONS")
        print("-" * 40)

        try:
            # 8.1 List existing tags
            print(" Listing current workspace tags...")
            list_options = WorkspaceTagListOptions(page_size=20)
            current_tags = list(self.workspaces.list_tags(workspace_id, list_options))

            print(f"    Found {len(current_tags)} existing tags:")
            for tag in current_tags:
                print(f"     Tag: {tag.name} (ID: {tag.id})")

            # 8.2 List tags with search query
            print("\n Searching for tags with 'env' in name...")
            search_options = WorkspaceTagListOptions(query="env", page_size=10)
            search_results = list(
                self.workspaces.list_tags(workspace_id, search_options)
            )

            print(f"    Found {len(search_results)} tags matching 'env':")
            for tag in search_results:
                print(f"     Matching tag: {tag.name}")

            # 8.3 Add new tags
            print("\n Adding new tags to workspace...")
            new_tags = [
                Tag(name="environment-production"),  # Add by name
                Tag(name="team-backend"),
                Tag(name="version-v2-1-0"),  # Fixed: no dots, use hyphens
                Tag(id="tag-existing-123")
                if current_tags
                else Tag(name="cost-center-engineering"),  # Add by ID if exists
            ]

            add_options = WorkspaceAddTagsOptions(tags=new_tags)
            self.workspaces.add_tags(workspace_id, add_options)
            print(f"    Successfully added {len(new_tags)} tags")

            for tag in new_tags:
                if tag.id:
                    print(f"     Added tag by ID: {tag.id}")
                else:
                    print(f"     Added tag by name: {tag.name}")

            # 8.4 List updated tags
            print("\n Listing updated workspace tags...")
            updated_tags = list(self.workspaces.list_tags(workspace_id, list_options))
            print(f"    Total tags after addition: {len(updated_tags)}")

            for tag in updated_tags:
                print(f"     Tag: {tag.name} (ID: {tag.id})")

            # 8.5 List tags with pagination
            print("\n Demonstrating tag pagination...")
            paginated_options = WorkspaceTagListOptions(page_number=1)
            page_tags = list(self.workspaces.list_tags(workspace_id, paginated_options))

            print(f"    Page 1 results: {len(page_tags)} tags")
            for i, tag in enumerate(page_tags, 1):
                print(f"   {i}. {tag.name}")

            # 8.6 Remove specific tags
            print("\n Removing specific tags...")
            tags_to_remove = [
                Tag(
                    name="version-v2-1-0"
                ),  # Fixed: Remove by name (matching what we added)
                Tag(id=updated_tags[0].id)
                if updated_tags
                else Tag(name="team-backend"),  # Remove by ID
            ]

            remove_options = WorkspaceRemoveTagsOptions(tags=tags_to_remove)
            self.workspaces.remove_tags(workspace_id, remove_options)
            print(f"    Successfully removed {len(tags_to_remove)} tags")

            for tag in tags_to_remove:
                if tag.id:
                    print(f"     Removed tag by ID: {tag.id}")
                else:
                    print(f"     Removed tag by name: {tag.name}")

            # 8.7 Final tag list
            print("\n Final workspace tags...")
            final_tags = list(self.workspaces.list_tags(workspace_id, list_options))
            print(f"    Final tag count: {len(final_tags)}")

            for tag in final_tags:
                print(f"     Final tag: {tag.name} (ID: {tag.id})")

        except Exception as e:
            print(f"    Tag operations failed: {e}")

    def demo_tag_binding_operations(self, workspace_id: str):
        """Demonstrate comprehensive workspace tag binding management operations."""
        print("\n 8B. WORKSPACE TAG BINDING OPERATIONS")
        print("-" * 45)

        try:
            # 8B.1 List existing tag bindings
            print(" Listing current workspace tag bindings...")
            current_bindings = list(self.workspaces.list_tag_bindings(workspace_id))

            print(f"    Found {len(current_bindings)} existing tag bindings:")
            for binding in current_bindings:
                print(
                    f"    Binding: {binding.key} = {binding.value} (ID: {binding.id})"
                )

            # 8B.2 List effective tag bindings (including inherited)
            print("\n Listing effective tag bindings (including inherited)...")
            effective_bindings = list(
                self.workspaces.list_effective_tag_bindings(workspace_id)
            )

            print(f"    Found {len(effective_bindings)} effective tag bindings:")
            for binding in effective_bindings:
                links_info = (
                    f" (Links: {len(binding.links)} entries)" if binding.links else ""
                )
                print(f"    Effective: {binding.key} = {binding.value}{links_info}")

            # 8B.3 Add new tag bindings
            print("\n Adding new tag bindings to workspace...")
            new_bindings = [
                TagBinding(key="environment", value="production"),
                TagBinding(key="team", value="infrastructure"),
                TagBinding(key="cost-center", value="engineering"),
                TagBinding(key="project", value="terraform-automation"),
                TagBinding(key="owner", value="devops-team"),
            ]

            add_options = WorkspaceAddTagBindingsOptions(tag_bindings=new_bindings)
            result_bindings = list(
                self.workspaces.add_tag_bindings(workspace_id, add_options)
            )
            print(f"    Successfully added {len(result_bindings)} tag bindings")

            for binding in result_bindings:
                print(f"    Added: {binding.key} = {binding.value} (ID: {binding.id})")

            # 8B.4 Update existing tag bindings (same key, new value)
            print("\n  Updating existing tag bindings...")
            update_bindings = [
                TagBinding(key="environment", value="staging"),  # Update existing
                TagBinding(key="version", value="v2.1.0"),  # Add new
            ]

            update_options = WorkspaceAddTagBindingsOptions(
                tag_bindings=update_bindings
            )
            updated_result = list(
                self.workspaces.add_tag_bindings(workspace_id, update_options)
            )
            print(f"    Successfully updated/added {len(updated_result)} tag bindings")

            for binding in updated_result:
                print(f"     Updated: {binding.key} = {binding.value}")

            # 8B.5 Delete all tag bindings
            print("\n  Removing all tag bindings...")
            self.workspaces.delete_all_tag_bindings(workspace_id)
            print("    Successfully removed all tag bindings")

            # 8B.6 Verify deletion
            print("\n Verifying tag binding deletion...")
            final_bindings = list(self.workspaces.list_tag_bindings(workspace_id))
            print(f"    Remaining tag bindings: {len(final_bindings)}")

            if final_bindings:
                print("     Some bindings remain:")
                for binding in final_bindings:
                    print(f"       {binding.key} = {binding.value}")
            else:
                print("    All tag bindings successfully removed")

        except Exception as e:
            print(f"    Tag binding operations failed: {e}")

    def demo_data_retention_policy_operations(self, workspace_id: str):
        """Demonstrate workspace data retention policy management operations."""
        print("\n Data Retention Policy Operations")
        print("-" * 50)

        try:
            # Read current data retention policy choice (should be None initially)
            print("1. Reading current data retention policy...")
            current_policy = self.workspaces.read_data_retention_policy_choice(
                workspace_id
            )
            if current_policy is None or not current_policy.is_populated():
                print("    No data retention policy currently set")
            else:
                print(f"    Current policy: {current_policy}")

            # Set a "delete older" data retention policy
            print("\n2. Setting 'delete older' data retention policy (30 days)...")
            delete_older_options = DataRetentionPolicyDeleteOlderSetOptions(
                delete_older_than_n_days=30
            )
            delete_older_policy = (
                self.workspaces.set_data_retention_policy_delete_older(
                    workspace_id, options=delete_older_options
                )
            )
            print(f"    Set delete older policy: ID={delete_older_policy.id}")
            print(
                f"   Delete after: {delete_older_policy.delete_older_than_n_days} days"
            )

            # Read the updated data retention policy choice
            print("\n3. Reading updated data retention policy choice...")
            updated_policy = self.workspaces.read_data_retention_policy_choice(
                workspace_id
            )
            if updated_policy and updated_policy.is_populated():
                print("    Data retention policy choice retrieved successfully")
                if updated_policy.data_retention_policy_delete_older:
                    drp = updated_policy.data_retention_policy_delete_older
                    print("     Policy Type: Delete Older")
                    print(f"    Policy ID: {drp.id}")
                    print(f"    Delete after: {drp.delete_older_than_n_days} days")

                # Test legacy conversion
                legacy_policy = updated_policy.convert_to_legacy_struct()
                if legacy_policy:
                    print(
                        f"    Legacy conversion: ID={legacy_policy.id}, Days={legacy_policy.delete_older_than_n_days}"
                    )

            # Update to a different retention period
            print("\n4. Updating retention period to 60 days...")
            updated_delete_older_options = DataRetentionPolicyDeleteOlderSetOptions(
                delete_older_than_n_days=60
            )
            updated_delete_older_policy = (
                self.workspaces.set_data_retention_policy_delete_older(
                    workspace_id, options=updated_delete_older_options
                )
            )
            print(f"    Updated policy: ID={updated_delete_older_policy.id}")
            print(
                f"    New retention period: {updated_delete_older_policy.delete_older_than_n_days} days"
            )

            # Switch to "don't delete" policy
            print("\n5. Switching to 'don't delete' data retention policy...")
            dont_delete_options = DataRetentionPolicyDontDeleteSetOptions()
            dont_delete_policy = self.workspaces.set_data_retention_policy_dont_delete(
                workspace_id, options=dont_delete_options
            )
            print(f"    Set don't delete policy: ID={dont_delete_policy.id}")
            print("     Data will never be automatically deleted")

            # Read the don't delete policy
            print("\n6. Reading 'don't delete' policy...")
            dont_delete_choice = self.workspaces.read_data_retention_policy_choice(
                workspace_id
            )
            if (
                dont_delete_choice
                and dont_delete_choice.data_retention_policy_dont_delete
            ):
                dnd = dont_delete_choice.data_retention_policy_dont_delete
                print(f"    Don't delete policy confirmed: ID={dnd.id}")
                print("     Data retention: Indefinite (never delete)")

                # Test legacy conversion (should return None for don't delete policies)
                legacy_policy = dont_delete_choice.convert_to_legacy_struct()
                if legacy_policy is None:
                    print(
                        "   Legacy conversion: None (don't delete policies can't be represented as legacy)"
                    )

            # Clean up - delete the data retention policy
            print("\n7. Cleaning up - deleting data retention policy...")
            self.workspaces.delete_data_retention_policy(workspace_id)
            print("    Data retention policy deleted successfully")

            # Verify deletion
            print("\n8. Verifying policy deletion...")
            final_policy = self.workspaces.read_data_retention_policy_choice(
                workspace_id
            )
            if final_policy is None or not final_policy.is_populated():
                print("    Confirmed: No data retention policy set")
            else:
                print(f"     Unexpected: Policy still exists: {final_policy}")

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg:
                print(f"     Data retention policy feature not available: {e}")
            else:
                print(f"    Data retention policy operations failed: {e}")

    def demo_delete_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace deletion operations."""
        print("\n  9. WORKSPACE DELETE OPERATIONS")
        print("-" * 40)

        print("  Performing safe delete...")
        try:
            # Safe delete (recommended)
            self.workspaces.safe_delete(organization, workspace_name)
            print(f"    Safe delete initiated for: {workspace_name}")
            print("    Safe delete queues deletion after checking for dependencies")

        except Exception as e:
            print(f"     Safe delete failed, trying regular delete: {e}")

            # Regular delete (immediate)
            try:
                self.workspaces.delete(organization, workspace_name)
                print(f"   Workspace deleted: {workspace_name}")
            except Exception as delete_error:
                print(f"   Delete failed: {delete_error}")


def main():
    """Main execution function."""
    # Configuration
    token = os.getenv("TFE_TOKEN")
    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    organization = os.getenv("TFE_ORG", "your-org-name")  # Replace with your org

    print(f" Terraform Address: {address}")
    print(f" Organization: {organization}")
    print(
        f" Token: {'*' * (len(token) - 8) + token[-8:] if len(token) > 8 else '****'}"
    )

    try:
        # Initialize workspace manager
        manager = WorkspaceManager()

        # Run comprehensive demo
        manager.demonstrate_all_operations(organization)

    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
