#!/usr/bin/env python3
"""Example usage of the Users API.

This example demonstrates how to read a user by ID using the Python TFE SDK.
"""

import os
import sys

# Add the src directory to the Python path so we can import the local package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig


def main() -> None:
    """Read and print user details from Terraform Cloud."""
    user_id = os.getenv("TFE_USER_ID")
    if not user_id:
        print("TFE_USER_ID is not set. Please export TFE_USER_ID and retry.")
        return

    try:
        client = TFEClient(TFEConfig.from_env())
        user = client.users.read(user_id)

        print("=== Terraform Cloud User ===")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Auth Method: {user.auth_method}")
    except Exception as e:
        print(f"Error reading user '{user_id}': {e}")


if __name__ == "__main__":
    main()
