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

from tfe import Client
from tfe.errors import (
    InvalidOrgError,
    InvalidWorkspaceIDError,
    TFEError,
)
from tfe.types import (
    ExecutionMode,
    VCSRepo,
    WorkspaceCreateOptions,
    WorkspaceInclude,
    WorkspaceListOptions,
    WorkspaceLockOptions,
    WorkspaceReadOptions,
    WorkspaceRemoveVCSConnectionOptions,
    WorkspaceUpdateOptions,
)


class WorkspaceManager:
    """Comprehensive workspace management utility."""

    def __init__(self, token: str, address: str = "https://app.terraform.io"):
        """Initialize the workspace manager."""
        self.client = Client(token=token, address=address)
        self.workspaces = self.client.workspaces

    def demonstrate_all_operations(self, organization: str):
        """Demonstrate all workspace operations."""
        print("🚀 Starting Comprehensive Workspace Operations Demo")
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

            # 8. Cleanup - delete the test workspace
            self.demo_delete_operations(organization, workspace_name, workspace_id)

        except Exception as e:
            print(f"❌ Error during demo: {e}")
            raise

        print("\n🎉 Comprehensive workspace demo completed successfully!")

    def demo_list_operations(self, organization: str):
        """Demonstrate workspace listing operations."""
        print("\n📋 1. WORKSPACE LISTING OPERATIONS")
        print("-" * 40)

        # Basic listing
        print("🔍 Listing all workspaces...")
        options = WorkspaceListOptions()
        workspaces = list(self.workspaces.list(organization, options=options))
        print(f"   Found {len(workspaces)} workspaces")

        for ws in workspaces[:3]:  # Show first 3
            print(f"   • {ws.name} (ID: {ws.id[:10]}...)")
            print(f"     - Execution Mode: {ws.execution_mode}")
            print(f"     - Auto Apply: {ws.auto_apply}")
            print(f"     - Locked: {ws.locked}")

        # Advanced listing with filters
        print("\n🔍 Listing with search filters...")
        filtered_options = WorkspaceListOptions(
            search="prod",  # Search for workspaces containing "prod"
            tags="production,frontend",  # Filter by tags
            include=[WorkspaceInclude.current_run],  # Include current run info
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
        print("\n🏗️  2. WORKSPACE CREATION OPERATIONS")
        print("-" * 40)

        # Basic workspace creation
        print("🔨 Creating basic workspace...")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        workspace_name = f"demo-workspace-{timestamp}"

        basic_options = WorkspaceCreateOptions(
            name=workspace_name,
            description=f"Demo workspace created at {datetime.now()}",
            auto_apply=False,
            execution_mode=ExecutionMode.remote,
            terraform_version="1.5.0",
            working_directory="terraform/",
            file_triggers_enabled=True,
            queue_all_runs=False,
            speculative_enabled=True,
            operations=True,
            trigger_prefixes=["modules/", "shared/"],
            trigger_patterns=["**/*.tf", "**/*.tfvars"],
        )

        workspace = self.workspaces.create(organization, options=basic_options)
        print(f"   ✅ Created workspace: {workspace.name}")
        print(f"   📋 ID: {workspace.id}")
        print(f"   📝 Description: {workspace.description}")
        print(f"   ⚙️  Execution Mode: {workspace.execution_mode}")
        print(f"   🔄 Auto Apply: {workspace.auto_apply}")

        return workspace

    def demo_create_with_vcs(self, organization: str):
        """Demonstrate workspace creation with VCS integration."""
        print("\n🔗 Creating workspace with VCS integration...")

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
            print(f"   ✅ Created VCS workspace: {vcs_workspace.name}")
            return vcs_workspace
        except Exception as e:
            print(
                f"   ⚠️  VCS workspace creation failed (expected without valid OAuth token): {e}"
            )
            return None

    def demo_read_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace reading operations."""
        print("\n📖 3. WORKSPACE READ OPERATIONS")
        print("-" * 40)

        # Read by name
        print("📄 Reading workspace by name...")
        workspace_by_name = self.workspaces.read(organization, workspace_name)
        print(f"   📋 Name: {workspace_by_name.name}")
        print(f"   🆔 ID: {workspace_by_name.id}")
        print(f"   📅 Created: {workspace_by_name.created_at}")
        print(f"   📅 Updated: {workspace_by_name.updated_at}")

        # Read by ID
        print("\n📄 Reading workspace by ID...")
        workspace_by_id = self.workspaces.read_by_id(workspace_id)
        print(f"   📋 Name: {workspace_by_id.name}")
        print(f"   🔧 Terraform Version: {workspace_by_id.terraform_version}")
        print(f"   📁 Working Directory: {workspace_by_id.working_directory}")

        # Read with additional include options
        print("\n📄 Reading workspace with include options...")
        read_options = WorkspaceReadOptions(
            include=[WorkspaceInclude.current_run, WorkspaceInclude.outputs]
        )

        detailed_workspace = self.workspaces.read_with_options(
            workspace_name, organization, options=read_options
        )
        print(f"   🏃 Current Run ID: {detailed_workspace.locked_by}")
        print(f"   📊 Resource Count: {detailed_workspace.resource_count}")
        print(f"   🏷️  Tag Names: {detailed_workspace.tag_names}")

    def demo_update_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace update operations."""
        print("\n✏️  4. WORKSPACE UPDATE OPERATIONS")
        print("-" * 40)

        # Update by name
        print("🔧 Updating workspace by name...")
        update_options = WorkspaceUpdateOptions(
            description=f"Updated description at {datetime.now()}",
            auto_apply=True,  # Enable auto-apply
            terraform_version="1.6.0",  # Update Terraform version
            queue_all_runs=True,  # Enable queue all runs
            working_directory="terraform/updated/",
        )

        updated_workspace = self.workspaces.update(
            organization, workspace_name, options=update_options
        )
        print(f"   ✅ Updated workspace: {updated_workspace.name}")
        print(f"   📝 New description: {updated_workspace.description}")
        print(f"   🔄 Auto Apply: {updated_workspace.auto_apply}")
        print(f"   🔧 Terraform Version: {updated_workspace.terraform_version}")

        # Update by ID
        print("\n🔧 Updating workspace by ID...")
        id_update_options = WorkspaceUpdateOptions(
            speculative_enabled=False,  # Disable speculative plans
            operations=False,  # Switch to local execution
        )

        updated_by_id = self.workspaces.update_by_id(
            workspace_id, options=id_update_options
        )
        print(f"   ✅ Updated workspace operations: {updated_by_id.operations}")
        print(f"   🔍 Speculative enabled: {updated_by_id.speculative_enabled}")

    def demo_vcs_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate VCS connection operations."""
        print("\n🔗 5. VCS CONNECTION OPERATIONS")
        print("-" * 40)

        # Note: These operations require existing VCS connections
        print("🔌 VCS connection management...")

        try:
            # Remove VCS connection by name
            print("🗑️  Removing VCS connection by name...")
            remove_options = WorkspaceRemoveVCSConnectionOptions(
                id=workspace_id,
                vcs_repo=None,  # Set to None to remove
            )

            updated_workspace = self.workspaces.remove_vcs_connection(
                organization, workspace_name, options=remove_options
            )
            print(f"   ✅ VCS connection removed for: {updated_workspace.name}")

        except Exception as e:
            print(f"   ⚠️  VCS operation note: {e}")
            print("   (VCS operations require existing VCS configurations)")

    def demo_locking_operations(self, workspace_id: str):
        """Demonstrate workspace locking operations."""
        print("\n🔒 6. WORKSPACE LOCKING OPERATIONS")
        print("-" * 40)

        # Lock workspace
        print("🔐 Locking workspace...")
        lock_options = WorkspaceLockOptions(
            reason="Demo: Maintenance in progress - testing locking functionality"
        )

        try:
            locked_workspace = self.workspaces.lock(workspace_id, options=lock_options)
            print(f"   🔒 Workspace locked: {locked_workspace.name}")
            print("   📝 Lock reason: Demo maintenance")
            print(f"   🔓 Locked status: {locked_workspace.locked}")

            # Unlock workspace
            print("\n🔓 Unlocking workspace...")
            unlocked_workspace = self.workspaces.unlock(workspace_id)
            print(f"   🔓 Workspace unlocked: {unlocked_workspace.name}")
            print(f"   🔓 Locked status: {unlocked_workspace.locked}")

        except Exception as e:
            print(f"   ⚠️  Locking operation failed: {e}")
            print("   (This may be expected if workspace has active runs)")

    def demo_ssh_key_operations(self, workspace_id: str):
        """Demonstrate SSH key management operations."""
        print("\n🔑 7. SSH KEY MANAGEMENT OPERATIONS")
        print("-" * 40)

        # Note: This requires existing SSH keys in the organization
        print("🔐 SSH key management...")
        print("   ⚠️  SSH key operations require existing SSH keys")
        print("   📝 Skipping SSH key demo (requires SSH key setup)")

        # Uncomment and modify when you have SSH keys configured:
        """
        try:
            # Assign SSH key
            ssh_options = WorkspaceAssignSSHKeyOptions(
                ssh_key_id="sshkey-your-key-id"  # Replace with actual SSH key ID
            )

            workspace_with_ssh = self.workspaces.assign_ssh_key(workspace_id, options=ssh_options)
            print(f"   🔑 SSH key assigned to: {workspace_with_ssh.name}")

            # Unassign SSH key
            workspace_without_ssh = self.workspaces.unassign_ssh_key(workspace_id)
            print(f"   🔓 SSH key unassigned from: {workspace_without_ssh.name}")

        except Exception as e:
            print(f"   ⚠️  SSH key operation failed: {e}")
        """

    def demo_delete_operations(
        self, organization: str, workspace_name: str, workspace_id: str
    ):
        """Demonstrate workspace deletion operations."""
        print("\n🗑️  8. WORKSPACE DELETE OPERATIONS")
        print("-" * 40)

        print("🛡️  Performing safe delete...")
        try:
            # Safe delete (recommended)
            self.workspaces.safe_delete(organization, workspace_name)
            print(f"   ✅ Safe delete initiated for: {workspace_name}")
            print("   📝 Safe delete queues deletion after checking for dependencies")

        except Exception as e:
            print(f"   ⚠️  Safe delete failed, trying regular delete: {e}")

            # Regular delete (immediate)
            try:
                self.workspaces.delete(organization, workspace_name)
                print(f"   ✅ Workspace deleted: {workspace_name}")
            except Exception as delete_error:
                print(f"   ❌ Delete failed: {delete_error}")
                print("   🧹 Manual cleanup may be required")

    def demo_error_handling(self, organization: str):
        """Demonstrate error handling patterns."""
        print("\n⚠️  ERROR HANDLING DEMONSTRATIONS")
        print("-" * 40)

        # Invalid organization
        try:
            options = WorkspaceListOptions()
            list(self.workspaces.list("", options=options))
        except InvalidOrgError:
            print("   ✅ Caught InvalidOrgError for empty organization")

        # Invalid workspace ID
        try:
            self.workspaces.read_by_id("")
        except InvalidWorkspaceIDError:
            print("   ✅ Caught InvalidWorkspaceIDError for empty ID")

        # Nonexistent workspace
        try:
            self.workspaces.read(organization, "nonexistent-workspace-12345")
        except TFEError as e:
            print(f"   ✅ Caught TFEError for nonexistent workspace: {e}")


def main():
    """Main execution function."""
    # Configuration
    token = os.getenv("TFE_TOKEN")
    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    organization = os.getenv("TFE_ORG", "your-org-name")  # Replace with your org

    if not token:
        print("❌ Error: TFE_TOKEN environment variable is required")
        print("📝 Set it with: export TFE_TOKEN=your-token-here")
        sys.exit(1)

    if organization == "your-org-name":
        print("⚠️  Warning: Using default organization name")
        print("📝 Set TFE_ORG environment variable or update the script")

        # Allow user to input organization name
        org_input = input("Enter your organization name: ").strip()
        if org_input:
            organization = org_input
        else:
            print("❌ Organization name is required")
            sys.exit(1)

    print(f"🌐 Terraform Address: {address}")
    print(f"🏢 Organization: {organization}")
    print(
        f"🔑 Token: {'*' * (len(token) - 8) + token[-8:] if len(token) > 8 else '****'}"
    )

    try:
        # Initialize workspace manager
        manager = WorkspaceManager(token=token, address=address)

        # Run comprehensive demo
        manager.demonstrate_all_operations(organization)

        # Demonstrate error handling
        manager.demo_error_handling(organization)

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("💡 Common issues:")
        print("   • Invalid token or organization")
        print("   • Network connectivity problems")
        print("   • Insufficient permissions")
        raise


if __name__ == "__main__":
    main()
