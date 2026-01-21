#!/usr/bin/env python3
"""
Query Run Individual Function Tests

This file provides individual test functions for each query run operation.
You can run specific functions to test individual parts of the API.

Functions available:
- run_list() - List query runs in a workspace
- run_create() - Create a new query run
- run_read() - Read a specific query run
- run_logs() - Retrieve logs for a query run
- run_cancel() - Cancel a query run
- run_force_cancel() - Force cancel a query run

Usage:
    python query_run.py

Note: Query Runs require Terraform ~>1.14 which includes the 'terraform query' command.
      These tests may fail with error status since the feature is not fully available yet.
"""

import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    QueryRunCreateOptions,
    QueryRunListOptions,
    QueryRunSource,
)


def get_client_and_workspace():
    """Initialize client and get workspace ID."""
    client = TFEClient(TFEConfig.from_env())
    organization = os.getenv("TFE_ORG", "aayush-test")
    workspace_name = "query-test"  # Default workspace for testing

    # Get workspace
    workspace = client.workspaces.read(workspace_name, organization=organization)
    return client, workspace


def run_list():
    """Test 1: List query runs in a workspace."""
    print("=== Test 1: List Query Runs ===")

    client, workspace = get_client_and_workspace()

    try:
        # Simple list
        query_runs = list(client.query_runs.list(workspace.id))
        print(f"Found {len(query_runs)} query runs in workspace '{workspace.name}'")

        for i, qr in enumerate(query_runs[:5], 1):
            print(f"  {i}. {qr.id}")
            print(f"     Status: {qr.status}")
            print(f"     Created: {qr.created_at}")
            print()

        # List with options
        options = QueryRunListOptions(page_size=5)
        limited_runs = list(client.query_runs.list(workspace.id, options))
        print(f"Retrieved {len(limited_runs)} query runs (page_size=5)")

        return query_runs

    except Exception as e:
        print(f"Error: {e}")
        return []


def run_create():
    """Test 2: Create a new query run."""
    print("\n=== Test 2: Create Query Run ===")

    client, workspace = get_client_and_workspace()

    try:
        # Get the latest configuration version
        config_versions = list(client.configuration_versions.list(workspace.id))
        if not config_versions:
            print("ERROR: No configuration versions found in workspace")
            return None

        config_version = config_versions[0]
        print(f"Using configuration version: {config_version.id}")

        # Create query run
        options = QueryRunCreateOptions(
            source=QueryRunSource.API,
            workspace_id=workspace.id,
            configuration_version_id=config_version.id,
        )

        query_run = client.query_runs.create(options)
        print(f"Created query run: {query_run.id}")
        print(f"  Status: {query_run.status}")
        print(f"  Source: {query_run.source}")
        print(f"  Created: {query_run.created_at}")

        return query_run

    except Exception as e:
        print(f"Error: {e}")
        return None


def run_read(query_run_id=None):
    """Test 3: Read a specific query run."""
    print("\n=== Test 3: Read Query Run ===")

    client, workspace = get_client_and_workspace()

    try:
        # If no query_run_id provided, get the first one from the list
        if not query_run_id:
            query_runs = list(client.query_runs.list(workspace.id))
            if not query_runs:
                print("ERROR: No query runs found to read")
                return None
            query_run_id = query_runs[0].id
            print(f"Using first query run from list: {query_run_id}")

        # Read the query run
        query_run = client.query_runs.read(query_run_id)
        print(f"Read query run: {query_run.id}")
        print(f"  Status: {query_run.status}")
        print(f"  Source: {query_run.source}")
        print(f"  Created: {query_run.created_at}")

        if query_run.status_timestamps:
            print("  Status Timestamps:")
            if query_run.status_timestamps.queued_at:
                print(f"    Queued: {query_run.status_timestamps.queued_at}")
            if query_run.status_timestamps.running_at:
                print(f"    Running: {query_run.status_timestamps.running_at}")
            if query_run.status_timestamps.finished_at:
                print(f"    Finished: {query_run.status_timestamps.finished_at}")
            if query_run.status_timestamps.errored_at:
                print(f"    Errored: {query_run.status_timestamps.errored_at}")

        return query_run

    except Exception as e:
        print(f"Error: {e}")
        return None


def run_logs(query_run_id=None):
    """Test 4: Retrieve logs for a query run."""
    print("\n=== Test 4: Get Query Run Logs ===")

    client, workspace = get_client_and_workspace()

    try:
        # If no query_run_id provided, get the first one from the list
        if not query_run_id:
            query_runs = list(client.query_runs.list(workspace.id))
            if not query_runs:
                print("ERROR: No query runs found to get logs")
                return None
            query_run_id = query_runs[0].id
            print(f"Using first query run from list: {query_run_id}")

        # Get logs
        logs = client.query_runs.logs(query_run_id)
        log_content = logs.read().decode("utf-8")

        print(f"Retrieved logs for query run: {query_run_id}")
        print(f"  Log size: {len(log_content)} bytes")
        print("\n--- Log Preview (first 500 chars) ---")
        print(log_content[:500])
        if len(log_content) > 500:
            print(f"\n... ({len(log_content) - 500} more characters)")
        print("--- End of Log Preview ---")

        return log_content

    except Exception as e:
        print(f"Error: {e}")
        print("  Note: Logs may not be available if the query run hasn't started yet")
        return None


def run_cancel(query_run_id=None):
    """Test 5: Cancel a query run."""
    print("\n=== Test 5: Cancel Query Run ===")

    client, workspace = get_client_and_workspace()

    try:
        # If no query_run_id provided, create a new one
        if not query_run_id:
            print("Creating a new query run to cancel...")
            new_run = run_create()
            if not new_run:
                print("ERROR: Could not create query run to cancel")
                return False
            query_run_id = new_run.id
            time.sleep(1)  # Give it a moment to start

        # Cancel the query run
        client.query_runs.cancel(query_run_id)
        print(f"Cancel requested for query run: {query_run_id}")

        # Verify cancellation
        time.sleep(2)
        query_run = client.query_runs.read(query_run_id)
        print(f"  Status after cancel: {query_run.status}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        print("  Note: Query run may not be in a cancelable state")
        return False


def run_force_cancel(query_run_id=None):
    """Test 6: Force cancel a query run."""
    print("\n=== Test 6: Force Cancel Query Run ===")

    client, workspace = get_client_and_workspace()

    try:
        # If no query_run_id provided, create a new one
        if not query_run_id:
            print("Creating a new query run to force cancel...")
            new_run = run_create()
            if not new_run:
                print("ERROR: Could not create query run to force cancel")
                return False
            query_run_id = new_run.id
            time.sleep(1)  # Give it a moment to start

        # Force cancel the query run
        client.query_runs.force_cancel(query_run_id)
        print(f"Force cancel requested for query run: {query_run_id}")

        # Verify force cancellation
        time.sleep(2)
        query_run = client.query_runs.read(query_run_id)
        print(f"  Status after force cancel: {query_run.status}")

        return True

    except Exception as e:
        print(f"Error: {e}")
        print("  Note: Query run may not be in a force-cancelable state")
        return False


def main():
    """Run all tests in sequence."""
    print("=" * 80)
    print("QUERY RUN FUNCTION TESTS")
    print("=" * 80)
    print("Testing all Query Run API operations")
    print()
    print("NOTE: Query Runs require Terraform 1.10+ with 'terraform query' command.")
    print("      Most query runs will error since this feature is not yet available.")
    print("=" * 80)

    # Test 1: List query runs
    query_runs = run_list()

    # Test 2: Create a query run
    new_query_run = run_create()

    # Test 3: Read a query run
    if query_runs:
        run_read(query_runs[0].id)
    elif new_query_run:
        run_read(new_query_run.id)

    # Test 4: Get logs (use first query run from list)
    if query_runs:
        run_logs(query_runs[0].id)

    # Test 5: Cancel a query run (creates new one)
    run_cancel()

    # Test 6: Force cancel a query run (creates new one)
    run_force_cancel()


if __name__ == "__main__":
    main()
