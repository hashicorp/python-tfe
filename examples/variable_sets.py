"""Example demonstrating Variable Set operations with the TFE Python SDK.

This example shows how to:
1. Create a variable set
2. Create variables in the set
3. Apply the set to workspaces/projects
4. Update variables and sets
5. Clean up resources

Make sure to set the following environment variables:
- TFE_TOKEN: Your Terraform Cloud/Enterprise API token
- TFE_ADDRESS: Your Terraform Cloud/Enterprise URL (optional, defaults to https://app.terraform.io)
- TFE_ORG: Your organization name
"""

import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    CategoryType,
    Parent,
    Project,
    VariableSetApplyToProjectsOptions,
    VariableSetApplyToWorkspacesOptions,
    VariableSetCreateOptions,
    VariableSetIncludeOpt,
    VariableSetListOptions,
    VariableSetReadOptions,
    VariableSetRemoveFromProjectsOptions,
    VariableSetRemoveFromWorkspacesOptions,
    VariableSetUpdateOptions,
    VariableSetVariableCreateOptions,
    VariableSetVariableListOptions,
    VariableSetVariableUpdateOptions,
    Workspace,
    WorkspaceListOptions,
)


def variable_set_example():
    """Demonstrate Variable Set operations."""

    # Initialize client
    token = os.getenv("TFE_TOKEN")
    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    org_name = os.getenv("TFE_ORG")

    if not token or not org_name:
        print("Please set TFE_TOKEN and TFE_ORG environment variables")
        return

    config = TFEConfig(token=token, address=address)
    client = TFEClient(config=config)

    # Variable set and variable IDs for cleanup
    created_variable_set_id = None
    created_variable_ids = []

    try:
        print("=== Variable Set Operations Example ===\n")

        # 1. List existing variable sets
        print("1. Listing existing variable sets...")
        list_options = VariableSetListOptions(
            page_size=10, include=[VariableSetIncludeOpt.WORKSPACES]
        )
        variable_sets = client.variable_sets.list(org_name, list_options)
        print(f"Found {len(variable_sets)} existing variable sets")

        for vs in variable_sets[:3]:  # Show first 3
            print(f"  - {vs.name} (ID: {vs.id}, Global: {vs.global_})")
        print()

        # 2. Create a new variable set
        print("2. Creating a new variable set...")
        create_options = VariableSetCreateOptions.model_validate(
            {
                "name": "python-sdk-example-varset",
                "description": "Example variable set created with Python SDK",
                "global": False,  # Not global, will apply to specific workspaces/projects
                "priority": True,  # High priority
            }
        )

        new_variable_set = client.variable_sets.create(org_name, create_options)
        created_variable_set_id = new_variable_set.id
        print(
            f"Created variable set: {new_variable_set.name} (ID: {new_variable_set.id})"
        )
        print(f"  Description: {new_variable_set.description}")
        print(f"  Global: {new_variable_set.global_}")
        print(f"  Priority: {new_variable_set.priority}")
        print()

        # 3. Create variables in the variable set
        print("3. Creating variables in the variable set...")

        # Create a Terraform variable
        tf_var_options = VariableSetVariableCreateOptions(
            key="environment",
            value="production",
            description="Environment name",
            category=CategoryType.TERRAFORM,
            hcl=False,
            sensitive=False,
        )

        tf_variable = client.variable_set_variables.create(
            created_variable_set_id, tf_var_options
        )
        created_variable_ids.append(tf_variable.id)
        print(f"Created Terraform variable: {tf_variable.key} = {tf_variable.value}")

        # Create an environment variable
        env_var_options = VariableSetVariableCreateOptions(
            key="DATABASE_URL",
            value="postgres://prod-db:5432/myapp",
            description="Production database connection string",
            category=CategoryType.ENV,
            hcl=False,
            sensitive=True,  # Mark as sensitive
        )

        env_variable = client.variable_set_variables.create(
            created_variable_set_id, env_var_options
        )
        created_variable_ids.append(env_variable.id)
        print(f"Created environment variable: {env_variable.key} (sensitive)")

        # Create an HCL variable
        hcl_var_options = VariableSetVariableCreateOptions(
            key="instance_config",
            value='{"type": "t3.medium", "count": 2}',
            description="Instance configuration",
            category=CategoryType.TERRAFORM,
            hcl=True,  # HCL formatted
            sensitive=False,
        )

        hcl_variable = client.variable_set_variables.create(
            created_variable_set_id, hcl_var_options
        )
        created_variable_ids.append(hcl_variable.id)
        print(f"Created HCL variable: {hcl_variable.key} (HCL format)")
        print()

        # 4. List variables in the variable set
        print("4. Listing variables in the variable set...")
        var_list_options = VariableSetVariableListOptions(page_size=50)
        variables = client.variable_set_variables.list(
            created_variable_set_id, var_list_options
        )
        print(f"Found {len(variables)} variables in the set:")

        for var in variables:
            sensitive_note = " (sensitive)" if var.sensitive else ""
            hcl_note = " (HCL)" if var.hcl else ""
            print(f"  - {var.key}: {var.category.value}{sensitive_note}{hcl_note}")
            print(f"    Description: {var.description}")
        print()

        # 5. Update a variable
        print("5. Updating a variable...")
        update_var_options = VariableSetVariableUpdateOptions(
            key="environment",
            value="staging",
            description="Updated to staging environment",
        )

        updated_variable = client.variable_set_variables.update(
            created_variable_set_id, tf_variable.id, update_var_options
        )
        print(f"Updated variable: {updated_variable.key} = {updated_variable.value}")
        print(f"  New description: {updated_variable.description}")
        print()

        # 6. Update the variable set itself
        print("6. Updating the variable set...")
        update_set_options = VariableSetUpdateOptions(
            name="python-sdk-updated-varset",
            description="Updated variable set description",
            priority=False,  # Change priority
        )

        updated_variable_set = client.variable_sets.update(
            created_variable_set_id, update_set_options
        )
        print(f"Updated variable set: {updated_variable_set.name}")
        print(f"  New description: {updated_variable_set.description}")
        print(f"  Priority: {updated_variable_set.priority}")
        print()

        # 7. Example: Apply to workspaces (if any exist)
        print("7. Workspace operations example...")
        try:
            # List some workspaces first
            workspace_options = WorkspaceListOptions(page_size=5)
            workspaces = list(
                client.workspaces.list(org_name, options=workspace_options)
            )
            if workspaces:
                # Apply to first workspace as example
                first_workspace = workspaces[0]
                print(f"Applying variable set to workspace: {first_workspace.name}")

                apply_ws_options = VariableSetApplyToWorkspacesOptions(
                    workspaces=[Workspace(id=first_workspace.id)]
                )
                client.variable_sets.apply_to_workspaces(
                    created_variable_set_id, apply_ws_options
                )
                print("Successfully applied to workspace")

                # List variable sets for this workspace
                workspace_varsets = client.variable_sets.list_for_workspace(
                    first_workspace.id
                )
                print(f"Workspace now has {len(workspace_varsets)} variable sets")

                # Remove from workspace
                remove_ws_options = VariableSetRemoveFromWorkspacesOptions(
                    workspaces=[Workspace(id=first_workspace.id)]
                )
                client.variable_sets.remove_from_workspaces(
                    created_variable_set_id, remove_ws_options
                )
                print("Successfully removed from workspace")
            else:
                print("No workspaces found to demonstrate workspace operations")
        except Exception as e:
            print(f"Workspace operations example failed: {e}")
        print()

        # 8. Example: Apply to projects (if any exist)
        print("8. Project operations example...")
        try:
            # List projects
            projects = list(client.projects.list(org_name))
            if projects:
                # Apply to first project as example
                first_project = projects[0]
                print(f"Applying variable set to project: {first_project.name}")

                apply_proj_options = VariableSetApplyToProjectsOptions(
                    projects=[Project(id=first_project.id)]
                )
                client.variable_sets.apply_to_projects(
                    created_variable_set_id, apply_proj_options
                )
                print("Successfully applied to project")

                # List variable sets for this project
                project_varsets = client.variable_sets.list_for_project(
                    first_project.id
                )
                print(f"Project now has {len(project_varsets)} variable sets")

                # Remove from project
                remove_proj_options = VariableSetRemoveFromProjectsOptions(
                    projects=[Project(id=first_project.id)]
                )
                client.variable_sets.remove_from_projects(
                    created_variable_set_id, remove_proj_options
                )
                print("Successfully removed from project")
            else:
                print("No projects found to demonstrate project operations")
        except Exception as e:
            print(f"Project operations example failed: {e}")
        print()

        # 9. Read the variable set with includes
        print("9. Reading variable set with includes...")
        read_options = VariableSetReadOptions(
            include=[VariableSetIncludeOpt.VARS, VariableSetIncludeOpt.WORKSPACES]
        )

        detailed_varset = client.variable_sets.read(
            created_variable_set_id, read_options
        )
        print(f"Variable set: {detailed_varset.name}")
        print(f"  Variables count: {len(detailed_varset.vars or [])}")
        print(f"  Workspaces count: {len(detailed_varset.workspaces or [])}")
        print()

        print("=== Variable Set Operations Completed Successfully ===")

    except Exception as e:
        print(f"Error during example execution: {e}")
        raise

    finally:
        # Cleanup: Delete created resources
        print("\n=== Cleanup ===")

        if created_variable_ids and created_variable_set_id:
            print("Cleaning up created variables...")
            for var_id in created_variable_ids:
                try:
                    client.variable_set_variables.delete(
                        created_variable_set_id, var_id
                    )
                    print(f"Deleted variable: {var_id}")
                except Exception as e:
                    print(f"Failed to delete variable {var_id}: {e}")

        if created_variable_set_id:
            print("Cleaning up created variable set...")
            try:
                client.variable_sets.delete(created_variable_set_id)
                print(f"Deleted variable set: {created_variable_set_id}")
            except Exception as e:
                print(f"Failed to delete variable set {created_variable_set_id}: {e}")

        print("Cleanup completed")


def global_variable_set_example():
    """Example of creating and managing a global variable set."""

    token = os.getenv("TFE_TOKEN")
    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    org_name = os.getenv("TFE_ORG")

    if not token or not org_name:
        print("Please set TFE_TOKEN and TFE_ORG environment variables")
        return

    config = TFEConfig(token=token, address=address)
    client = TFEClient(config=config)
    created_variable_set_id = None

    try:
        print("\n=== Global Variable Set Example ===\n")

        # Create a global variable set
        print("Creating a global variable set...")
        global_create_options = VariableSetCreateOptions.model_validate(
            {
                "name": "python-sdk-global-varset",
                "description": "Global variable set for common settings",
                "global": True,  # Make it global
                "priority": False,
            }
        )

        global_varset = client.variable_sets.create(org_name, global_create_options)
        created_variable_set_id = global_varset.id
        print(f"Created global variable set: {global_varset.name}")
        print(f"  Global: {global_varset.global_}")
        print(f"  Priority: {global_varset.priority}")

        # Add some common variables
        print("\nAdding common variables...")

        # Common Terraform variables
        common_vars = [
            {
                "key": "default_tags",
                "value": '{"Environment": "shared", "ManagedBy": "terraform"}',
                "description": "Default tags for all resources",
                "category": CategoryType.TERRAFORM,
                "hcl": True,
            },
            {
                "key": "TERRAFORM_VERSION",
                "value": "1.5.0",
                "description": "Terraform version requirement",
                "category": CategoryType.ENV,
                "hcl": False,
            },
        ]

        for var_config in common_vars:
            var_options = VariableSetVariableCreateOptions(**var_config)
            variable = client.variable_set_variables.create(
                created_variable_set_id, var_options
            )
            print(f"  Added {variable.category.value} variable: {variable.key}")

        print(f"\nGlobal variable set is now available to all workspaces in {org_name}")

    except Exception as e:
        print(f"Error in global variable set example: {e}")

    finally:
        # Cleanup
        if created_variable_set_id:
            try:
                print("\nCleaning up global variable set...")
                client.variable_sets.delete(created_variable_set_id)
                print("Global variable set deleted")
            except Exception as e:
                print(f"Failed to delete global variable set: {e}")


def project_scoped_variable_set_example():
    """Example of creating a project-scoped variable set."""

    token = os.getenv("TFE_TOKEN")
    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    org_name = os.getenv("TFE_ORG")

    if not token or not org_name:
        print("Please set TFE_TOKEN and TFE_ORG environment variables")
        return

    config = TFEConfig(token=token, address=address)
    client = TFEClient(config=config)
    created_variable_set_id = None

    try:
        print("\n=== Project-Scoped Variable Set Example ===\n")

        # First, get a project to scope to
        projects = list(client.projects.list(org_name))
        if not projects:
            print(
                "No projects found. Creating a project-scoped variable set requires an existing project."
            )
            return

        target_project = projects[0]
        print(f"Using project: {target_project.name} (ID: {target_project.id})")

        # Create a project-scoped variable set
        print("Creating a project-scoped variable set...")
        parent = Parent(project=Project(id=target_project.id))

        project_create_options = VariableSetCreateOptions.model_validate(
            {
                "name": "python-sdk-project-varset",
                "description": f"Project-specific variables for {target_project.name}",
                "global": False,  # Not global
                "parent": parent.model_dump(),  # Scope to specific project
            }
        )

        project_varset = client.variable_sets.create(org_name, project_create_options)
        created_variable_set_id = project_varset.id
        print(f"Created project-scoped variable set: {project_varset.name}")

        # Add project-specific variables
        project_vars = [
            {
                "key": "PROJECT_NAME",
                "value": target_project.name,
                "description": "Project name",
                "category": CategoryType.ENV,
                "hcl": False,
            },
            {
                "key": "project_config",
                "value": f'{{"name": "{target_project.name}", "id": "{target_project.id}"}}',
                "description": "Project configuration",
                "category": CategoryType.TERRAFORM,
                "hcl": True,
            },
        ]

        for var_config in project_vars:
            var_options = VariableSetVariableCreateOptions(**var_config)
            variable = client.variable_set_variables.create(
                created_variable_set_id, var_options
            )
            print(f"  Added variable: {variable.key}")

        print(
            f"\nProject-scoped variable set is available to workspaces in project: {target_project.name}"
        )

    except Exception as e:
        print(f"Error in project-scoped variable set example: {e}")

    finally:
        # Cleanup
        if created_variable_set_id:
            try:
                print("\nCleaning up project-scoped variable set...")
                client.variable_sets.delete(created_variable_set_id)
                print("Project-scoped variable set deleted")
            except Exception as e:
                print(f"Failed to delete project-scoped variable set: {e}")


if __name__ == "__main__":
    print("TFE Python SDK - Variable Set Examples")
    print("=" * 50)

    try:
        # Run the main example
        variable_set_example()

        # Run additional examples
        global_variable_set_example()
        project_scoped_variable_set_example()

    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed with error: {e}")
        import traceback

        traceback.print_exc()
