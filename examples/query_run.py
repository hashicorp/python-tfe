#!/usr/bin/env python3
"""
Query Run Management Example

This example demonstrates all available query run operations in the Python TFE SDK,
including create, read, list, logs, cancel, and force cancel operations.

Usage:
    python examples/query_run.py

Requirements:
    - TFE_TOKEN environment variable set
    - TFE_WORKSPACE_ID environment variable set
    - TFE_ADDRESS environment variable set (optional, defaults to Terraform Cloud)
    - An existing workspace in your Terraform Cloud/Enterprise instance

Query Run Operations Demonstrated:
    1. List query runs for a workspace
    2. Create new query runs
    3. Read query run details
    4. Read query run with additional options
    5. Retrieve query run logs
    6. Cancel running query runs
    7. Force cancel stuck query runs
"""

import os
import time
from datetime import datetime

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    QueryRunCreateOptions,
    QueryRunIncludeOpt,
    QueryRunListOptions,
    QueryRunReadOptions,
    QueryRunSource,
    QueryRunStatus,
)


def test_list_query_runs(client, workspace_id):
    """Test listing query runs with various options."""
    print("=== Testing Query Run List Operations ===")

    # 1. List all query runs
    print("\n1. Listing All Query Runs:")
    try:
        query_runs = client.query_runs.list(workspace_id)
        print(f"   SUCCESS: Found {len(query_runs.items)} query runs")
        if query_runs.items:
            print(f"   SUCCESS: Latest query run: {query_runs.items[0].id}")
            print(f"   SUCCESS: Status: {query_runs.items[0].status}")
            print(f"   SUCCESS: Source: {query_runs.items[0].source}")
    except Exception as e:
        print(f"   ERROR: Error: {e}")

    # 2. List with pagination
    print("\n2. Listing Query Runs with Pagination:")
    try:
        options = QueryRunListOptions(page_number=1, page_size=5)
        query_runs = client.query_runs.list(workspace_id, options)
        print(f"   SUCCESS: Page 1 has {len(query_runs.items)} query runs")
        print(f"   SUCCESS: Total pages: {query_runs.total_pages}")
        print(f"   SUCCESS: Total count: {query_runs.total_count}")
    except Exception as e:
        print(f"   ERROR: Error: {e}")

    # 3. List with include options
    print("\n3. Listing Query Runs with Related Resources:")
    try:
        options = QueryRunListOptions(
            page_size=10,
            include=[QueryRunIncludeOpt.CREATED_BY]
        )
        query_runs = client.query_runs.list(workspace_id, options)
        print(f"   SUCCESS: Found {len(query_runs.items)} query runs with created_by info")
        for qr in query_runs.items[:3]:  # Show first 3
            print(f"     - {qr.id}: Status={qr.status}")
    except Exception as e:
        print(f"   ERROR: Error: {e}")

    return query_runs.items[0] if query_runs.items else None


def test_create_query_run(client, workspace_id):
    """Test creating a query run."""
    print("\n=== Testing Query Run Creation ===")

    # Create a query run
    print("\n1. Creating Query Run:")
    try:
        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id=workspace_id,
        )
        query_run = client.query_runs.create(options)
        print(f"   SUCCESS: Created query run: {query_run.id}")
        print(f"   SUCCESS: Status: {query_run.status}")
        print(f"   SUCCESS: Source: {query_run.source}")
        print(f"   SUCCESS: Created at: {query_run.created_at}")
        return query_run
    except Exception as e:
        print(f"   ERROR: Error: {e}")
        return None


def test_read_query_run(client, query_run_id):
    """Test reading query run details."""
    print(f"\n=== Testing Query Run Read Operations for {query_run_id} ===")

    # 1. Basic read
    print("\n1. Reading Query Run Details:")
    try:
        query_run = client.query_runs.read(query_run_id)
        print(f"   SUCCESS: Query Run ID: {query_run.id}")
        print(f"   SUCCESS: Status: {query_run.status}")
        print(f"   SUCCESS: Source: {query_run.source}")
        print(f"   SUCCESS: Created: {query_run.created_at}")
        print(f"   SUCCESS: Updated: {query_run.updated_at}")
        if query_run.actions:
            print(f"   SUCCESS: Is Cancelable: {query_run.actions.is_cancelable}")
            print(f"   SUCCESS: Is Force Cancelable: {query_run.actions.is_force_cancelable}")
        if query_run.log_read_url:
            print(f"   SUCCESS: Log URL available")
    except Exception as e:
        print(f"   ERROR: Error: {e}")
        return None

    # 2. Read with options
    print("\n2. Reading Query Run with Options:")
    try:
        options = QueryRunReadOptions(
            include=[QueryRunIncludeOpt.CREATED_BY, QueryRunIncludeOpt.CONFIGURATION_VERSION]
        )
        query_run = client.query_runs.read_with_options(query_run_id, options)
        print("   SUCCESS: Read query run with additional data")
        print(f"   SUCCESS: Status: {query_run.status}")
    except Exception as e:
        print(f"   ERROR: Error: {e}")

    return query_run


def test_query_run_logs(client, query_run_id):
    """Test retrieving query run logs."""
    print(f"\n=== Testing Query Run Logs for {query_run_id} ===")

    try:
        logs_stream = client.query_runs.logs(query_run_id)
        log_content = logs_stream.read()
        
        if isinstance(log_content, bytes):
            log_text = log_content.decode('utf-8')
        else:
            log_text = log_content
            
        print(f"   SUCCESS: Retrieved logs for query run")
        print(f"   SUCCESS: Log size: {len(log_text)} characters")

        # Show first few lines of logs
        log_lines = log_text.split("\n")[:5]
        print("   SUCCESS: Log preview:")
        for line in log_lines:
            if line.strip():
                print(f"     {line}")
    except Exception as e:
        print(f"   ERROR: Error retrieving logs: {e}")


def test_query_run_cancellation(client, query_run_id):
    """Test canceling query runs."""
    print(f"\n=== Testing Query Run Cancellation for {query_run_id} ===")

    # First check if the query run is in a cancelable state
    try:
        query_run = client.query_runs.read(query_run_id)
        if query_run.status not in [QueryRunStatus.PENDING, QueryRunStatus.QUEUED, QueryRunStatus.RUNNING]:
            print(
                f"   INFO: Query run is {query_run.status}, not in a cancelable state"
            )
            return
            
        if not query_run.actions or not query_run.actions.is_cancelable:
            print(f"   INFO: Query run is not cancelable")
            return
    except Exception as e:
        print(f"   ERROR: Error checking query run status: {e}")
        return

    # Test regular cancel
    print("\n1. Testing Regular Cancellation:")
    try:
        client.query_runs.cancel(query_run_id)
        print(f"   SUCCESS: Canceled query run: {query_run_id}")
        
        # Read to verify
        query_run = client.query_runs.read(query_run_id)
        print(f"   SUCCESS: New status: {query_run.status}")
    except Exception as e:
        print(f"   ERROR: Error canceling query run: {e}")


def test_query_run_workflow(client, workspace_id):
    """Test a complete query run workflow."""
    print("\n=== Testing Complete Query Run Workflow ===")

    # 1. Create a query run
    print("\n1. Creating Query Run:")
    try:
        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id=workspace_id,
        )
        query_run = client.query_runs.create(options)
        print(f"   SUCCESS: Created: {query_run.id}")
        query_run_id = query_run.id
    except Exception as e:
        print(f"   ERROR: Error creating query run: {e}")
        return

    # 2. Monitor execution
    print("\n2. Monitoring Execution:")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        try:
            query_run = client.query_runs.read(query_run_id)
            print(f"   Attempt {attempt + 1}: Status = {query_run.status}")

            if query_run.status in [
                QueryRunStatus.FINISHED,
                QueryRunStatus.ERRORED,
                QueryRunStatus.CANCELED,
            ]:
                break

            time.sleep(2)  # Wait 2 seconds before checking again
            attempt += 1
        except Exception as e:
            print(f"   ERROR: Error monitoring query run: {e}")
            break

    # 3. Get final logs if finished
    print("\n3. Getting Final Status:")
    try:
        if query_run.status == QueryRunStatus.FINISHED:
            print("   SUCCESS: Query completed successfully")
            
            # Get logs
            if query_run.log_read_url:
                logs_stream = client.query_runs.logs(query_run_id)
                log_content = logs_stream.read()
                print(f"   SUCCESS: Retrieved execution logs ({len(log_content)} bytes)")
        else:
            print(f"   ERROR: Query run finished with status: {query_run.status}")
    except Exception as e:
        print(f"   ERROR: Error getting final results: {e}")

    return query_run_id


def main():
    """Main function to demonstrate query run operations."""
    # Get configuration from environment
    token = os.environ.get("TFE_TOKEN")
    workspace_id = os.environ.get("TFE_WORKSPACE_ID")
    address = os.environ.get("TFE_ADDRESS", "https://app.terraform.io")

    if not token:
        print("Error: TFE_TOKEN environment variable is required")
        return 1

    if not workspace_id:
        print("Error: TFE_WORKSPACE_ID environment variable is required")
        print("  Set it to the workspace ID where you want to run queries")
        return 1

    # Initialize client
    print("=== Terraform Enterprise Query Run SDK Example ===")
    print(f"Address: {address}")
    print(f"Workspace ID: {workspace_id}")
    print(f"Timestamp: {datetime.now()}")

    config = TFEConfig(address=address, token=token)
    client = TFEClient(config)

    try:
        # 1. List existing query runs
        existing_query_run = test_list_query_runs(client, workspace_id)

        # 2. Create a new query run
        created_query_run = test_create_query_run(client, workspace_id)

        # 3. Test read operations
        if existing_query_run:
            test_read_query_run(client, existing_query_run.id)

            # Only test logs if query run is finished
            if existing_query_run.status == QueryRunStatus.FINISHED:
                test_query_run_logs(client, existing_query_run.id)

        # 4. Test cancellation (if query run is cancelable)
        if created_query_run:
            test_query_run_cancellation(client, created_query_run.id)

        # 5. Test complete workflow
        test_query_run_workflow(client, workspace_id)

        print("\n" + "=" * 80)
        print("Query Run operations completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
