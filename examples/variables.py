#!/usr/bin/env python3
"""
Comprehensive example testing all variable functions in TFE workspace.
Tests: list, list_all, create, read, update, and delete operations.
"""

import os
import sys
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tfe import TFEClient, TFEConfig
from tfe.types import CategoryType, VariableCreateOptions, VariableUpdateOptions


def main():
    """Test all variable operations in a workspace."""

    # Initialize the TFE client
    client = TFEClient(TFEConfig.from_env())

    # Replace this with your actual workspace ID
    workspace_id = "ws-example123456789"  # Get this from your TFE workspace

    print(f"Testing all variable operations in workspace: {workspace_id}")
    print("=" * 60)

    # Track created variables for cleanup
    created_variables = []

    try:
        # 1. Test CREATE function - COMMENTED OUT (already have variables from previous run)
        print("\n1. Testing CREATE operation:")
        print("-" * 30)

        # Create a Terraform variable
        terraform_var = VariableCreateOptions(
            key="test_terraform_var",
            value="production",
            description="Test Terraform variable",
            category=CategoryType.TERRAFORM,
            hcl=False,
            sensitive=False,
        )

        try:
            variable = client.variables.create(workspace_id, terraform_var)
            created_variables.append(variable.id)
            print(f"✓ Created Terraform variable: {variable.key} = {variable.value}")
            print(f"  ID: {variable.id}, Category: {variable.category}")
        except Exception as e:
            print(f"✗ Error creating Terraform variable: {e}")

        # Create an environment variable
        env_var = VariableCreateOptions(
            key="TEST_LOG_LEVEL",
            value="DEBUG",
            description="Test environment variable",
            category=CategoryType.ENV,
            hcl=False,
            sensitive=False,
        )

        try:
            variable = client.variables.create(workspace_id, env_var)
            created_variables.append(variable.id)
            print(f"✓ Created environment variable: {variable.key} = {variable.value}")
            print(f"  ID: {variable.id}, Category: {variable.category}")
        except Exception as e:
            print(f"✗ Error creating environment variable: {e}")

        # Create a sensitive variable
        secret_var = VariableCreateOptions(
            key="TEST_API_KEY",
            value="super-secret-key-12345",
            description="Test sensitive variable",
            category=CategoryType.ENV,
            hcl=False,
            sensitive=True,
        )

        try:
            variable = client.variables.create(workspace_id, secret_var)
            created_variables.append(variable.id)
            print(f"✓ Created sensitive variable: {variable.key} = ***HIDDEN***")
            print(f"  ID: {variable.id}, Category: {variable.category}")
        except Exception as e:
            print(f"✗ Error creating sensitive variable: {e}")

        # Small delay to ensure variables are created
        time.sleep(1)

        # 2. Test LIST function (workspace-only variables) - COMMENTED OUT
        print("\n2. Testing LIST operation (workspace variables only):")
        print("-" * 50)

        try:
            variables = list(client.variables.list(workspace_id))
            print(f"Found {len(variables)} workspace variables:")
            for var in variables:
                value_display = "***SENSITIVE***" if var.sensitive else var.value
                print(
                    f"  • {var.key} = {value_display} ({var.category}) [ID: {var.id}]"
                )
        except Exception as e:
            print(f"✗ Error listing variables: {e}")

        # 3. Test LIST_ALL function (includes inherited variables from variable sets)
        print("\n3. Testing LIST_ALL operation (includes variable sets):")
        print("-" * 55)

        try:
            all_variables = list(client.variables.list_all(workspace_id))
            print(f"Found {len(all_variables)} total variables (including inherited):")
            for var in all_variables:
                value_display = "***SENSITIVE***" if var.sensitive else var.value
                print(
                    f"  • {var.key} = {value_display} ({var.category}) [ID: {var.id}]"
                )
        except Exception as e:
            print(f"✗ Error listing all variables: {e}")

        # Test READ function with specific variable ID - COMMENTED OUT
        print("\n4. Testing READ operation with specific variable ID:")
        print("-" * 50)

        # Replace this with actual variable ID to test reading
        test_variable_id = "var-example123456789"
        print(f"Testing READ with variable ID: {test_variable_id}")

        try:
            variable = client.variables.read(workspace_id, test_variable_id)
            # For testing, show actual values even for sensitive variables
            if variable.sensitive:
                print(f"✓ Read variable: {variable.key} = {variable.value} (SENSITIVE)")
            else:
                print(f"✓ Read variable: {variable.key} = {variable.value}")
            print(f"  ID: {variable.id}")
            print(f"  Description: {variable.description}")
            print(f"  Category: {variable.category}")
            print(f"  HCL: {variable.hcl}")
            print(f"  Sensitive: {variable.sensitive}")
            if hasattr(variable, "version_id"):
                print(f"  Version ID: {variable.version_id}")
        except Exception as e:
            print(f"✗ Error reading variable {test_variable_id}: {e}")

        # Test UPDATE function with specific variable ID - COMMENTED OUT
        print("\n5. Testing UPDATE operation with specific variable ID:")
        print("-" * 55)

        # Replace this with actual variable ID to test  updating
        test_variable_id = "var-example123456789"
        print(f"Testing UPDATE with variable ID: {test_variable_id}")
        print("Setting value to: 'npe'")

        try:
            # First read the current variable to get its details
            current_var = client.variables.read(workspace_id, test_variable_id)
            print(f"Current value: {current_var.value}")
            print(f"Current key: {current_var.key}")

            # Update the variable value to "npe"
            update_options = VariableUpdateOptions(
                key=current_var.key,
                value="npe",
                description=current_var.description,
                hcl=current_var.hcl,
                sensitive=current_var.sensitive,
            )

            updated_variable = client.variables.update(
                workspace_id, test_variable_id, update_options
            )
            print(
                f"✓ Updated variable: {updated_variable.key} = {updated_variable.value}"
            )
            print(f"  Description: {updated_variable.description}")
            print(f"  Category: {updated_variable.category}")
            print(f"  HCL: {updated_variable.hcl}")
            print(f"  Sensitive: {updated_variable.sensitive}")
            print(f"  ID: {updated_variable.id}")
        except Exception as e:
            print(f"✗ Error updating variable {test_variable_id}: {e}")

        # Test DELETE function with specific variable ID
        print("\n6. Testing DELETE operation with specific variable ID:")
        print("-" * 55)

        # Replace this with actual variable ID to test deletion
        test_variable_id = "var-example123456789"
        print(f"Testing DELETE with variable ID: {test_variable_id}")

        try:
            # First read the variable to confirm it exists before deletion
            variable = client.variables.read(workspace_id, test_variable_id)
            print(f"Variable to delete: {variable.key} = {variable.value}")
            print(f"  ID: {variable.id}")

            # Delete the variable
            client.variables.delete(workspace_id, test_variable_id)
            print(f"✓ Successfully deleted variable with ID: {test_variable_id}")

            # Try to read it again to verify deletion
            print("Verifying deletion...")
            try:
                client.variables.read(workspace_id, test_variable_id)
                print("✗ Warning: Variable still exists after deletion!")
            except Exception as read_error:
                if "not found" in str(read_error).lower() or "404" in str(read_error):
                    print("✓ Confirmed: Variable no longer exists")
                else:
                    print(f"✗ Unexpected error verifying deletion: {read_error}")

        except Exception as e:
            print(f"✗ Error deleting variable {test_variable_id}: {e}")

        # 4. Test READ function
        print("\n4. Testing READ operation:")
        print("-" * 25)

        if created_variables:
            test_var_id = created_variables[0]  # Use the first created variable
            try:
                variable = client.variables.read(workspace_id, test_var_id)
                value_display = (
                    "***SENSITIVE***" if variable.sensitive else variable.value
                )
                print(f"✓ Read variable: {variable.key} = {value_display}")
                print(f"  ID: {variable.id}")
                print(f"  Description: {variable.description}")
                print(f"  Category: {variable.category}")
                print(f"  HCL: {variable.hcl}")
                print(f"  Sensitive: {variable.sensitive}")
            except Exception as e:
                print(f"✗ Error reading variable {test_var_id}: {e}")
        else:
            print("No variables available to read")

        # 5. Test UPDATE function
        print("\n5. Testing UPDATE operation:")
        print("-" * 27)

        if created_variables:
            test_var_id = created_variables[0]  # Use the first created variable
            try:
                # First read the current variable to get its details
                current_var = client.variables.read(workspace_id, test_var_id)

                # Update the variable
                update_options = VariableUpdateOptions(
                    key=current_var.key,
                    value="updated_value_123",
                    description="Updated test variable description",
                    hcl=False,
                    sensitive=False,
                )

                updated_variable = client.variables.update(
                    workspace_id, test_var_id, update_options
                )
                print(
                    f"✓ Updated variable: {updated_variable.key} = {updated_variable.value}"
                )
                print(f"  New description: {updated_variable.description}")
                print(f"  ID: {updated_variable.id}")
            except Exception as e:
                print(f"✗ Error updating variable {test_var_id}: {e}")
        else:
            print("No variables available to update")

        # 6. Test DELETE function
        print("\n6. Testing DELETE operation:")
        print("-" * 27)

        # Delete all created variables
        for var_id in created_variables:
            try:
                client.variables.delete(workspace_id, var_id)
                print(f"✓ Deleted variable with ID: {var_id}")
            except Exception as e:
                print(f"✗ Error deleting variable {var_id}: {e}")

        # Verify deletion by listing variables again
        print("\nVerifying deletion - listing variables after cleanup:")
        try:
            remaining_variables = list(client.variables.list(workspace_id))
            # Filter out the variables we just deleted
            remaining_test_vars = [
                v
                for v in remaining_variables
                if v.key.startswith("test_") or v.key.startswith("TEST_")
            ]
            if remaining_test_vars:
                print(
                    f"Warning: {len(remaining_test_vars)} test variables still exist:"
                )
                for var in remaining_test_vars:
                    print(f"  • {var.key} [ID: {var.id}]")
            else:
                print("✓ All test variables successfully deleted")
        except Exception as e:
            print(f"✗ Error verifying deletion: {e}")

    except Exception as e:
        print(f"✗ Unexpected error during testing: {e}")

    print("\n" + "=" * 60)
    print("Variable testing complete!")


if __name__ == "__main__":
    main()
