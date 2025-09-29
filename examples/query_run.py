#!/usr/bin/env python3
"""
Query Run Management Example

This example demonstrates all available query run operations in the Python TFE SDK,
including create, read, list, logs, results, cancel, and force cancel operations.

Usage:
    python examples/query_run.py

Requirements:
    - TFE_TOKEN environment variable set
    - TFE_ADDRESS             # Get logs
            logs = client.query_runs.logs(query_run_id)
            print(f"   ✓ Retrieved execution logs ({len(logs.logs)} characters)")ironment variable set (optional, defaults to Terraform Cloud)
    - An existing organization in your Terraform Cloud/Enterprise instance

Query Run Operations Demonstrated:
    1. List query runs with various filters
    2. Create new query runs with different types
    3. Read query run details
    4. Read query run with additional options
    5. Retrieve query run logs
    6. Retrieve query run results
    7. Cancel running query runs
    8. Force cancel stuck query runs
"""

import os
import time
from datetime import datetime

from tfe import TFEClient, TFEConfig
from tfe.models.query_run import (
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunListOptions,
    QueryRunReadOptions,
    QueryRunStatus,
    QueryRunType,
)


def test_list_query_runs(client, organization_name):
    """Test listing query runs with various options."""
    print("=== Testing Query Run List Operations ===")

    # 1. List all query runs
    print("\n1. Listing All Query Runs:")
    try:
        query_runs = client.query_runs.list(organization_name)
        print(f"   ✓ Found {len(query_runs.items)} query runs")
        if query_runs.items:
            print(f"   ✓ Latest query run: {query_runs.items[0].id}")
            print(f"   ✓ Status: {query_runs.items[0].status}")
            print(f"   ✓ Query type: {query_runs.items[0].query_type}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 2. List with pagination
    print("\n2. Listing Query Runs with Pagination:")
    try:
        options = QueryRunListOptions(page_number=1, page_size=5)
        query_runs = client.query_runs.list(organization_name, options)
        print(f"   ✓ Page 1 has {len(query_runs.items)} query runs")
        print(f"   ✓ Total pages: {query_runs.total_pages}")
        print(f"   ✓ Total count: {query_runs.total_count}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 3. List with filters
    print("\n3. Listing Query Runs with Filters:")
    try:
        options = QueryRunListOptions(
            query_type=QueryRunType.FILTER,
            status=QueryRunStatus.COMPLETED,
            page_size=10,
        )
        query_runs = client.query_runs.list(organization_name, options)
        print(f"   ✓ Found {len(query_runs.items)} completed filter query runs")
        for qr in query_runs.items[:3]:  # Show first 3
            print(f"     - {qr.id}: {qr.query[:50]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    return query_runs.items[0] if query_runs.items else None


def test_create_query_runs(client, organization_name):
    """Test creating different types of query runs."""
    print("\n=== Testing Query Run Creation ===")

    created_query_runs = []

    # 1. Create a filter query run
    print("\n1. Creating Filter Query Run:")
    try:
        options = QueryRunCreateOptions(
            query="SELECT id, status, created_at FROM runs WHERE status = 'completed' ORDER BY created_at DESC",
            query_type=QueryRunType.FILTER,
            organization_name=organization_name,
            timeout_seconds=300,
            max_results=100,
        )
        query_run = client.query_runs.create(organization_name, options)
        created_query_runs.append(query_run)
        print(f"   ✓ Created filter query run: {query_run.id}")
        print(f"   ✓ Status: {query_run.status}")
        print(f"   ✓ Query: {query_run.query}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 2. Create a search query run
    print("\n2. Creating Search Query Run:")
    try:
        options = QueryRunCreateOptions(
            query="SEARCH workspaces WHERE name CONTAINS 'production'",
            query_type=QueryRunType.SEARCH,
            organization_name=organization_name,
            timeout_seconds=180,
            max_results=50,
        )
        query_run = client.query_runs.create(organization_name, options)
        created_query_runs.append(query_run)
        print(f"   ✓ Created search query run: {query_run.id}")
        print(f"   ✓ Status: {query_run.status}")
        print(f"   ✓ Query type: {query_run.query_type}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # 3. Create an analytics query run
    print("\n3. Creating Analytics Query Run:")
    try:
        options = QueryRunCreateOptions(
            query="ANALYZE run_durations GROUP BY workspace_id ORDER BY avg_duration DESC",
            query_type=QueryRunType.ANALYTICS,
            organization_name=organization_name,
            timeout_seconds=600,
            max_results=200,
            filters={"time_range": "last_30_days", "include_failed": False},
        )
        query_run = client.query_runs.create(organization_name, options)
        created_query_runs.append(query_run)
        print(f"   ✓ Created analytics query run: {query_run.id}")
        print(f"   ✓ Status: {query_run.status}")
        print(f"   ✓ Timeout: {query_run.timeout_seconds}s")
        print(f"   ✓ Max results: {query_run.max_results}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    return created_query_runs


def test_read_query_run(client, query_run_id):
    """Test reading query run details."""
    print(f"\n=== Testing Query Run Read Operations for {query_run_id} ===")

    # 1. Basic read
    print("\n1. Reading Query Run Details:")
    try:
        query_run = client.query_runs.read(query_run_id)
        print(f"   ✓ Query Run ID: {query_run.id}")
        print(f"   ✓ Status: {query_run.status}")
        print(f"   ✓ Query Type: {query_run.query_type}")
        print(f"   ✓ Created: {query_run.created_at}")
        print(f"   ✓ Updated: {query_run.updated_at}")
        if query_run.results_count:
            print(f"   ✓ Results Count: {query_run.results_count}")
        if query_run.error_message:
            print(f"   ✗ Error: {query_run.error_message}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None

    # 2. Read with options
    print("\n2. Reading Query Run with Options:")
    try:
        options = QueryRunReadOptions(include_results=True, include_logs=True)
        query_run = client.query_runs.read_with_options(query_run_id, options)
        print("   ✓ Read query run with additional data")
        print(f"   ✓ Status: {query_run.status}")
        if query_run.logs_url:
            print(f"   ✓ Logs URL available: {query_run.logs_url[:50]}...")
        if query_run.results_url:
            print(f"   ✓ Results URL available: {query_run.results_url[:50]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    return query_run


def test_query_run_logs(client, query_run_id):
    """Test retrieving query run logs."""
    print(f"\n=== Testing Query Run Logs for {query_run_id} ===")

    try:
        logs = client.query_runs.logs(query_run_id)
        print(f"   ✓ Retrieved logs for query run: {logs.query_run_id}")
        print(f"   ✓ Log level: {logs.log_level}")
        if logs.timestamp:
            print(f"   ✓ Log timestamp: {logs.timestamp}")

        # Show first few lines of logs
        log_lines = logs.logs.split("\n")[:5]
        print("   ✓ Log preview:")
        for line in log_lines:
            if line.strip():
                print(f"     {line}")
    except Exception as e:
        print(f"   ✗ Error retrieving logs: {e}")


def test_query_run_results(client, query_run_id):
    """Test retrieving query run results."""
    print(f"\n=== Testing Query Run Results for {query_run_id} ===")

    try:
        results = client.query_runs.results(query_run_id)
        print(f"   ✓ Retrieved results for query run: {results.query_run_id}")
        print(f"   ✓ Total results: {results.total_count}")
        print(f"   ✓ Truncated: {results.truncated}")

        # Show first few results
        if results.results:
            print("   ✓ Sample results:")
            for i, result in enumerate(results.results[:3]):
                print(f"     {i + 1}. {result}")
        else:
            print("   ℹ No results available")
    except Exception as e:
        print(f"   ✗ Error retrieving results: {e}")


def test_query_run_cancellation(client, query_run_id):
    """Test canceling query runs."""
    print(f"\n=== Testing Query Run Cancellation for {query_run_id} ===")

    # First check if the query run is in a cancelable state
    try:
        query_run = client.query_runs.read(query_run_id)
        if query_run.status not in [QueryRunStatus.PENDING, QueryRunStatus.RUNNING]:
            print(
                f"   ℹ Query run is {query_run.status}, creating new one for cancellation test"
            )

            # Create a new query run for cancellation test
            options = QueryRunCreateOptions(
                query="SELECT * FROM runs LIMIT 10000",  # Large query to ensure it runs long enough
                query_type=QueryRunType.FILTER,
                organization_name=query_run.organization_name,
                timeout_seconds=300,
            )
            query_run = client.query_runs.create(query_run.organization_name, options)
            query_run_id = query_run.id
            print(f"   ✓ Created new query run for cancellation: {query_run_id}")
    except Exception as e:
        print(f"   ✗ Error checking query run status: {e}")
        return

    # 1. Test regular cancel
    print("\n1. Testing Regular Cancellation:")
    try:
        cancel_options = QueryRunCancelOptions(
            reason="User requested cancellation for testing"
        )
        canceled_query_run = client.query_runs.cancel(query_run_id, cancel_options)
        print(f"   ✓ Canceled query run: {canceled_query_run.id}")
        print(f"   ✓ New status: {canceled_query_run.status}")
    except Exception as e:
        print(f"   ✗ Error canceling query run: {e}")

        # If regular cancel fails, try force cancel
        print("\n2. Testing Force Cancellation:")
        try:
            force_cancel_options = QueryRunForceCancelOptions(
                reason="Force cancel after regular cancel failed"
            )
            force_canceled_query_run = client.query_runs.force_cancel(
                query_run_id, force_cancel_options
            )
            print(f"   ✓ Force canceled query run: {force_canceled_query_run.id}")
            print(f"   ✓ New status: {force_canceled_query_run.status}")
        except Exception as e:
            print(f"   ✗ Error force canceling query run: {e}")


def test_query_run_workflow(client, organization_name):
    """Test a complete query run workflow."""
    print("\n=== Testing Complete Query Run Workflow ===")

    # 1. Create a query run
    print("\n1. Creating Query Run:")
    try:
        options = QueryRunCreateOptions(
            query="SELECT id, name, status FROM workspaces ORDER BY created_at DESC LIMIT 10",
            query_type=QueryRunType.FILTER,
            organization_name=organization_name,
            timeout_seconds=120,
            max_results=50,
        )
        query_run = client.query_runs.create(organization_name, options)
        print(f"   ✓ Created: {query_run.id}")
        query_run_id = query_run.id
    except Exception as e:
        print(f"   ✗ Error creating query run: {e}")
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
                QueryRunStatus.COMPLETED,
                QueryRunStatus.ERRORED,
                QueryRunStatus.CANCELED,
            ]:
                break

            time.sleep(2)  # Wait 2 seconds before checking again
            attempt += 1
        except Exception as e:
            print(f"   ✗ Error monitoring query run: {e}")
            break

    # 3. Get final results
    print("\n3. Getting Final Results:")
    try:
        if query_run.status == QueryRunStatus.COMPLETED:
            results = client.query_runs.results(query_run_id)
            print("   ✓ Query completed successfully")
            print(f"   ✓ Total results: {results.total_count}")
            print(f"   ✓ Truncated: {results.truncated}")

            # Get logs
            logs = client.query_runs.logs(query_run_id)
            print(f"   ✓ Retrieved execution logs ({len(logs.logs)} characters)")
        else:
            print(f"   ✗ Query run finished with status: {query_run.status}")
            if query_run.error_message:
                print(f"   ✗ Error message: {query_run.error_message}")
    except Exception as e:
        print(f"   ✗ Error getting final results: {e}")

    return query_run_id


def main():
    """Main function to demonstrate query run operations."""
    # Get configuration from environment
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")
    address = os.environ.get("TFE_ADDRESS", "https://app.terraform.io")

    if not token:
        print("Error: TFE_TOKEN environment variable is required")
        return 1

    if not org:
        print("Error: TFE_ORG environment variable is required")
        return 1

    # Initialize client
    print("=== Terraform Enterprise Query Run SDK Example ===")
    print(f"Address: {address}")
    print(f"Organization: {org}")
    print(f"Timestamp: {datetime.now()}")

    config = TFEConfig(address=address, token=token)
    client = TFEClient(config)

    try:
        # 1. List existing query runs
        existing_query_run = test_list_query_runs(client, org)

        # 2. Create new query runs
        created_query_runs = test_create_query_runs(client, org)

        # 3. Test read operations
        if existing_query_run:
            test_read_query_run(client, existing_query_run.id)

            # Only test logs and results if query run is completed
            if existing_query_run.status == QueryRunStatus.COMPLETED:
                test_query_run_logs(client, existing_query_run.id)
                test_query_run_results(client, existing_query_run.id)

        # 4. Test cancellation (with a new query run if needed)
        if created_query_runs:
            test_query_run_cancellation(client, created_query_runs[0].id)

        # 5. Test complete workflow
        test_query_run_workflow(client, org)

        print("\n" + "=" * 80)
        print("Query Run operations completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
