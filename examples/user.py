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

    try:
        client = TFEClient(TFEConfig.from_env())

        current_user = client.users.read_current()
        print("=== Current Terraform Cloud User ===")
        print(f"User ID: {current_user.id}")
        print(f"Username: {current_user.username}")
        print(f"Email: {current_user.email or 'N/A'}")
        print(f"Auth Method: {current_user.auth_method or 'N/A'}")

        if not user_id:
            print("\nTFE_USER_ID not set. Skipping client.users.read(user_id).")
            return

        user = client.users.read(user_id)

        print("\n=== Terraform Cloud User By ID ===")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email or 'N/A'}")
        print(f"Auth Method: {user.auth_method or 'N/A'}")
    except Exception as e:
        print(f"Error running user example: {e}")


if __name__ == "__main__":
    main()
