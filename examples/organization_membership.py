#!/usr/bin/env python3
"""
Example and test script for organization membership list functionality.

Requirements:
- TFE_TOKEN environment variable set
- TFE_ADDRESS environment variable set (optional, defaults to Terraform Cloud)
- An organization with members to list

Usage:
    python examples/organization_membership.py <organization-name>
"""

import sys

from pytfe import TFEClient
from pytfe.models import (
    OrganizationMembershipListOptions,
    OrganizationMembershipReadOptions,
    OrganizationMembershipStatus,
    OrgMembershipIncludeOpt,
)


def main():
    """Demonstrate organization membership list functionality."""

    organization_name = "aayush-test"

    # Initialize the client (reads TFE_TOKEN and TFE_ADDRESS from environment)
    try:
        client = TFEClient()
        print("Connected to Terraform Cloud/Enterprise")
    except Exception as e:
        print(f"Error connecting: {e}")
        print("\nMake sure TFE_TOKEN environment variable is set:")
        print("export TFE_TOKEN='your-token-here'")
        sys.exit(1)

    print(f"\nTesting Organization Membership List for: {organization_name}")
    print("=" * 70)

    # Test 1: List all organization memberships (no options)
    print("\n[Test 1] List all organization memberships:")
    try:
        count = 0
        memberships_list = []
        for membership in client.organization_memberships.list(organization_name):
            count += 1
            memberships_list.append(membership)
            if count <= 5:  # Show first 5
                print(
                    f"{membership.email} (ID: {membership.id[:8]}..., Status: {membership.status.value})"
                )

        print(memberships_list)
        print(f"Total memberships: {count}")

        if count == 0:
            print("No memberships found - organization may not exist or has no members")
        else:
            print(f"Success: Retrieved {count} membership(s)")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 2: Iterate with custom page size
    print("\n[Test 2] Iterate with custom page size (3 items per page):")
    try:
        options = OrganizationMembershipListOptions(
            page_size=3,  # Fetch 3 items per page
        )
        count = 0
        for membership in client.organization_memberships.list(
            organization_name, options
        ):
            count += 1
            if count <= 3:
                print(f"{membership.email}")

        print(f"Processed {count} memberships (fetched in batches of 3)")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 3: Iterate with user relationships included
    print("\n[Test 3] Iterate with user relationships included:")
    try:
        options = OrganizationMembershipListOptions(
            include=[OrgMembershipIncludeOpt.USER],
        )
        count = 0
        users_found = 0
        for membership in client.organization_memberships.list(
            organization_name, options
        ):
            count += 1
            if membership.user:
                users_found += 1
            if count <= 3:  # Show first 3
                user_id = membership.user.id if membership.user else "N/A"
                print(f"{membership.email} (User ID: {user_id})")

        print(f"Processed {count} memberships, {users_found} with user data")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 4: Filter by status (invited)
    print("\n[Test 4] Filter by status (invited only):")
    try:
        options = OrganizationMembershipListOptions(
            status=OrganizationMembershipStatus.INVITED,
        )
        invited = []
        for membership in client.organization_memberships.list(
            organization_name, options
        ):
            invited.append(membership.email)
            if membership.status != OrganizationMembershipStatus.INVITED:
                print(f"ERROR: Found non-invited member: {membership.email}")

        print(f"Found {len(invited)} invited membership(s)")
        for email in invited[:5]:  # Show first 5
            print(f"{email}")

        if len(invited) == 0:
            print("No invited members found")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 5: Filter by email addresses (using first member found in Test 1)
    print("\n[Test 5] Filter by specific email address:")
    try:
        if count > 0 and len(memberships_list) > 0:
            test_email = memberships_list[0].email
            print(f"Testing with email: {test_email}")

            options = OrganizationMembershipListOptions(
                emails=[test_email],
            )
            matching = []
            for membership in client.organization_memberships.list(
                organization_name, options
            ):
                matching.append(membership.email)

            print(f"Found {len(matching)} matching membership(s)")
            for email in matching:
                print(f"{email}")

            if len(matching) == 1 and matching[0] == test_email:
                print("Success: Email filter working correctly")
            else:
                print(f"Warning: Expected 1 result with email {test_email}")
        else:
            print("Skipped: No memberships available from Test 1")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 6: Search by query string
    print("\n[Test 6] Search memberships by query string:")
    try:
        if count > 0 and len(memberships_list) > 0:
            # Extract domain from first email for testing
            test_email = memberships_list[0].email
            domain = test_email.split("@")[1] if "@" in test_email else None

            if domain:
                print(f"Searching for: {domain}")
                options = OrganizationMembershipListOptions(
                    query=domain,  # Searches in user name and email
                )
                results = []
                for membership in client.organization_memberships.list(
                    organization_name, options
                ):
                    results.append(membership.email)

                print(f"Found {len(results)} membership(s) matching query")
                for email in results[:5]:  # Show first 5
                    print(f"{email}")

                if len(results) > 0:
                    print("Success: Query filter working")
                else:
                    print(f"Warning: No results found for query '{domain}'")
            else:
                print("Skipped: Could not extract domain from email")
        else:
            print("Skipped: No memberships available from Test 1")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 7: Combined filters (active + includes)
    print("\n[Test 7] Combined filters: active members with user & teams included:")
    try:
        options = OrganizationMembershipListOptions(
            status=OrganizationMembershipStatus.ACTIVE,
            include=[OrgMembershipIncludeOpt.USER, OrgMembershipIncludeOpt.TEAMS],
            page_size=5,
        )
        active_members = []
        for membership in client.organization_memberships.list(
            organization_name, options
        ):
            team_count = len(membership.teams) if membership.teams else 0
            has_user = membership.user is not None
            active_members.append((membership.email, team_count, has_user))

        print(f"Found {len(active_members)} active membership(s)")
        for email, team_count, has_user in active_members[:5]:  # Show first 5
            user_str = " User" if has_user else " No User"
            print(f"{email} (Teams: {team_count}, {user_str})")

        if len(active_members) > 0:
            print("Success: Combined filters working")
        else:
            print("No active members found")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 8: Read a specific organization membership
    print("\n[Test 8] Read a specific organization membership:")
    try:
        if count > 0 and len(memberships_list) > 0:
            test_membership_id = memberships_list[0].id
            print(f"Reading membership ID: {test_membership_id}")

            membership = client.organization_memberships.read(test_membership_id)
            print(f"Email: {membership.email}")
            print(f"Status: {membership.status.value}")
            print(f"ID: {membership.id}")
            print("Success: Read membership successfully")
        else:
            print("Skipped: No memberships available from Test 1")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Test 9: Read with options (include user and teams)
    print("\n[Test 9] Read membership with options (include user & teams):")
    try:
        if count > 0 and len(memberships_list) > 0:
            test_membership_id = memberships_list[0].id
            print(f"Reading membership ID: {test_membership_id}")

            read_options = OrganizationMembershipReadOptions(
                include=[OrgMembershipIncludeOpt.USER, OrgMembershipIncludeOpt.TEAMS]
            )
            membership = client.organization_memberships.read_with_options(
                test_membership_id, read_options
            )

            print(f"Email: {membership.email}")
            print(f"Status: {membership.status.value}")
            user_id = membership.user.id if membership.user else "N/A"
            print(f"User ID: {user_id}")
            team_count = len(membership.teams) if membership.teams else 0
            print(f"Teams: {team_count}")
        else:
            print("Skipped: No memberships available from Test 1")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # CREATE EXAMPLES
    print("\n[Create Example] Add a new organization membership:")
    try:
        from pytfe.models import OrganizationMembershipCreateOptions, Team

        # Replace with a valid email for your organization
        new_member_email = "sivaselvan.i@hashicorp.com"

        # Create membership with teams (uncomment to use)
        from pytfe.models import OrganizationAccess

        team = Team(
            id="team-dx24FR9xQUuwNTHA",
            organization_access=OrganizationAccess(read_workspaces=True),
        )  # Replace with actual team ID
        create_options = OrganizationMembershipCreateOptions(
            email=new_member_email, teams=[team]
        )

        created_membership = client.organization_memberships.create(
            organization_name, create_options
        )
        print(f"Created membership for: {created_membership.email}")
        print(f"ID: {created_membership.id}")
        print(f"Status: {created_membership.status.value}")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

    # Delete membership example
    print("\n[Delete Example] Delete an organization membership:")
    try:
        from pytfe.errors import NotFound

        membership_id = "ou-9mG77c6uE5GScg9k"  # Replace with actual membership ID
        print(f"Attempting to delete membership: {membership_id}")

        client.organization_memberships.delete(membership_id)
        print(f"Successfully deleted membership {membership_id}")

    except NotFound as e:
        print(f"Membership not found: {e}")
        print("The membership may have already been deleted or the ID is invalid")
    except Exception as e:
        print(f"Error deleting membership: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
