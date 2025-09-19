import time
import traceback

from tfe import TFEClient, TFEConfig
from tfe.models.run_task import (
    RunTaskCreateOptions,
    RunTaskIncludeOptions,
    RunTaskListOptions,
    RunTaskReadOptions,
    RunTaskUpdateOptions,
)


def run_task_list(client, org_name):
    """Test run task list with all options combined."""
    print(f"=== Testing Run Task List Comprehensive Options for '{org_name}' ===")

    # List run tasks with all options
    print("\n1. Listing Run Tasks with All Options Combined:")
    try:
        options = RunTaskListOptions(
            page_number=1,
            page_size=10,
            include=[
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS,
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE,
            ],
        )

        run_task_list = client.run_tasks.list(org_name, options)
        run_tasks = list(run_task_list)
        print(f"   ✓ Found {len(run_tasks)} run tasks with comprehensive options")

        for i, task in enumerate(run_tasks, 1):
            print(f"   {i:2d}. {task.name}")
            print(f"       URL: {task.url}")
            print(f"       Category: {task.category}")
            print(f"       Enabled: {task.enabled}")

            # Show description if available
            if task.description:
                print(f"       Description: {task.description}")

            # Show global configuration details
            if task.global_configuration:
                gc = task.global_configuration
                print("       Global Config:")
                print(f"         - Enabled: {gc.enabled}")
                print(f"         - Enforcement: {gc.enforcement_level.value}")
                if gc.stages:
                    stages = [stage.value for stage in gc.stages]
                    print(f"         - Stages: {', '.join(stages)}")

            # Show relationships
            if task.organization:
                print(f"       Organization: {task.organization.id}")

            if task.workspace_run_tasks:
                print(
                    f"       Workspace Run Tasks: {len(task.workspace_run_tasks)} items"
                )

            if task.agent_pool:
                print(f"       Agent Pool: {task.agent_pool.id}")

    except Exception as e:
        print(f"   Error listing run tasks comprehensively: {e}")
        traceback.print_exc()


def run_task_create(client, org_name):
    """Create a comprehensive run task that demonstrates all available features."""
    print("\n=== Creating Comprehensive Demonstration Run Task ===")

    try:
        timestamp = int(time.time())

        # Create the most comprehensive example possible
        options = RunTaskCreateOptions(
            name=f"comprehensive-demo-{timestamp}",
            url="https://httpbin.org/post",
            category="task",
            description="A comprehensive demonstration task showcasing all available features and configurations",
            enabled=True,
            hmac_key=f"demo-secret-key-{timestamp}",
        )

        print("\n2. Creating task with the following configuration:")
        created_task = client.run_tasks.create(org_name, options)

        print("\n   ✓ Successfully created comprehensive run task!")
        print(f"     Task Name: {created_task.name}")
        print(f"     Task ID: {created_task.id}")
        print(f"     URL: {created_task.url}")
        print(f"     Enabled: {created_task.enabled}")
        print(f"     Description: {created_task.description}")

        # Display additional details
        if created_task.organization:
            print(f"     Organization: {created_task.organization.id}")

        if created_task.hmac_key:
            print("     HMAC Key: ***configured***")

        return created_task.id, created_task.name

    except Exception as e:
        print(f"   ✗ Error creating comprehensive run task: {e}")
        return None, None


def run_task_read(client, task_id, task_name):
    """Read and display details of a specific run task."""
    try:
        print(f"\n4. Reading Run Task '{task_name}' (ID: {task_id})")
        read_task = client.run_tasks.read(task_id)

        print("\n   ✓ Successfully read run task:")
        print(f"     Task Name: {read_task.name}")
        print(f"     Task ID: {read_task.id}")
        print(f"     URL: {read_task.url}")
        print(f"     Category: {read_task.category}")
        print(f"     Enabled: {read_task.enabled}")
        print(f"     Description: {read_task.description or 'None'}")
        print(f"     HMAC Key: {'[SET]' if read_task.hmac_key else 'None'}")

        if read_task.organization:
            print(f"     Organization: {read_task.organization.id}")

    except Exception as e:
        print(f"   ✗ Error reading run task '{task_name}': {e}")
        traceback.print_exc()


def run_task_read_with_options(client, task_id, task_name):
    """Read a specific run task with include options."""
    try:
        options = RunTaskReadOptions(
            include=[RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS]
        )
        print(
            f"\n5. Reading Run Task '{task_name}' (ID: {task_id}) with includes: {options}"
        )
        read_task_with_option = client.run_tasks.read_with_options(task_id, options)

        print("\n   ✓ Successfully read run task with includes:")
        print(f"     Task Name: {read_task_with_option.name}")
        print(f"     Task ID: {read_task_with_option.id}")
        print(f"     URL: {read_task_with_option.url}")
        print(f"     Category: {read_task_with_option.category}")

        if RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS in options.include:
            print(
                "     (Workspace tasks relationship data would be included in API response)"
            )

        if RunTaskIncludeOptions.RUN_TASK_WORKSPACE in options.include:
            print("     (Workspace data would be included in API response)")

    except Exception as e:
        print(f"   ✗ Error reading run task '{task_name}' with includes: {e}")
        traceback.print_exc()


def run_task_update(client, task_id):
    """Update various fields of a specific run task."""
    print(f"\n=== Updating Run Task (ID: {task_id}) with Various Configurations ===")

    try:
        # Update basic fields
        print("\n3. Updating basic fields (name, description, url)...")
        update_options = RunTaskUpdateOptions(
            name=f"updated-name-{int(time.time())}",
            description="Updated description for the run task",
            url="https://httpbin.org/anything",
        )
        updated_task = client.run_tasks.update(task_id, update_options)

        print(" Successfully updated basic fields:")
        print(f"   Name: {updated_task.name}")
        print(f"   Description: {updated_task.description}")
        print(f"   URL: {updated_task.url}")

    except Exception as e:
        print(f" Error updating basic fields: {e}")


def run_task_delete(client, task_id, task_name):
    """Delete a specific run task."""
    try:
        print(f"\n6. Deleting Run Task '{task_name}' (ID: {task_id})")
        client.run_tasks.delete(task_id)
        print(f"\n   ✓ Successfully deleted run task: {task_name} (ID: {task_id})")
        return True

    except Exception as e:
        print(f"   ✗ Error deleting run task '{task_name}': {e}")
        return False


def main():
    """Main function to demonstrate comprehensive run task list operations."""
    print("Run Task List - Comprehensive Example")
    print("=" * 50)

    # Initialize client
    config = TFEConfig()
    client = TFEClient(config)

    # Replace 'your-org-name' with an actual organization name
    org_name = "your-org-name"

    print(f"Using organization: {org_name}")

    try:
        # Test comprehensive list operations
        run_task_list(client, org_name)
        task_id, task_name = run_task_create(client, org_name)
        if task_id:
            run_task_update(client, task_id)
        if task_id and task_name:
            run_task_read(client, task_id, task_name)
            run_task_read_with_options(client, task_id, task_name)
        run_task_delete(client, task_id, task_name)

    except Exception as e:
        print(f"\n Example failed: {e}")


if __name__ == "__main__":
    main()
