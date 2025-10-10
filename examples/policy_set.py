from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    Policy,
    PolicyKind,
    PolicySetAddPoliciesOptions,
    PolicySetAddProjectsOptions,
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetListOptions,
    PolicySetRemovePoliciesOptions,
    PolicySetRemoveProjectsOptions,
    PolicySetRemoveWorkspacesOptions,
    PolicySetUpdateOptions,
    Project,
    Workspace,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_policy_set_info(ps):
    """Helper function to print policy set information."""
    print(f"ID: {ps.id}")
    print(f"Name: {ps.name}")
    print(f"Description: {ps.description}")
    print(f"Kind: {ps.kind}")
    print(f"Global: {ps.Global}")
    print(f"Overridable: {ps.overridable}")
    print(f"Agent Enabled: {ps.agent_enabled}")
    print(f"Policy Tool Version: {ps.policy_tool_version}")
    print(f"Policies Path: {ps.policies_path}")
    print(f"Policy Count: {ps.policy_count}")
    print(f"Workspace Count: {ps.workspace_count}")
    print(f"Project Count: {ps.project_count}")
    print(f"Created At: {ps.created_at}")
    print(f"Updated At: {ps.updated_at}")

    if ps.vcs_repo:
        print(f"VCS Repo: {ps.vcs_repo.identifier}")

    if ps.workspaces:
        print(
            f"Workspaces: {[w.id if hasattr(w, 'id') else str(w) for w in ps.workspaces]}"
        )

    if ps.projects:
        print(
            f"Projects: {[p.id if hasattr(p, 'id') else str(p) for p in ps.projects]}"
        )

    if ps.policies:
        print(
            f"Policies: {[p.id if hasattr(p, 'id') else str(p) for p in ps.policies]}"
        )

    if ps.workspace_exclusions:
        print(
            f"Workspace Exclusions: {[w.id if hasattr(w, 'id') else str(w) for w in ps.workspace_exclusions]}"
        )


def main():
    parser = argparse.ArgumentParser(description="Policy Sets demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument(
        "--policy-set-id", help="Policy Set ID for read/update/delete operations"
    )
    parser.add_argument(
        "--policy-set-name", help="Policy Set name for create operation"
    )
    parser.add_argument(
        "--description", help="Policy Set description for create operation"
    )
    parser.add_argument(
        "--kind", choices=["opa", "sentinel"], help="Policy Set kind (opa or sentinel)"
    )
    parser.add_argument("--global", action="store_true", help="Make policy set global")
    parser.add_argument(
        "--overridable", action="store_true", help="Make policy set overridable"
    )
    parser.add_argument(
        "--agent-enabled", action="store_true", help="Enable agent for policy set"
    )
    parser.add_argument(
        "--workspace-ids", nargs="+", help="Workspace IDs to associate with policy set"
    )
    parser.add_argument(
        "--project-ids", nargs="+", help="Project IDs to associate with policy set"
    )
    parser.add_argument(
        "--policy-ids", nargs="+", help="Policy IDs to associate with policy set"
    )
    parser.add_argument("--create", action="store_true", help="Create a new policy set")
    parser.add_argument("--read", action="store_true", help="Read a policy set")
    parser.add_argument("--update", action="store_true", help="Update a policy set")
    parser.add_argument("--delete", action="store_true", help="Delete a policy set")
    parser.add_argument(
        "--add-workspaces", action="store_true", help="Add workspaces to policy set"
    )
    parser.add_argument(
        "--remove-workspaces",
        action="store_true",
        help="Remove workspaces from policy set",
    )
    parser.add_argument(
        "--add-projects", action="store_true", help="Add projects to policy set"
    )
    parser.add_argument(
        "--remove-projects", action="store_true", help="Remove projects from policy set"
    )
    parser.add_argument(
        "--add-policies", action="store_true", help="Add policies to policy set"
    )
    parser.add_argument(
        "--remove-policies", action="store_true", help="Remove policies from policy set"
    )
    parser.add_argument("--search", help="Search policy sets by name")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument is required")
        return

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List all policy sets for the organization
    _print_header(f"Listing policy sets for organization: {args.org}")

    list_options = PolicySetListOptions(
        page_number=args.page,
        page_size=args.page_size,
    )

    # Only add includes if we want to test them
    # list_options.include = [
    #     PolicySetIncludeOpt.POLICY_SET_WORKSPACES,
    #     PolicySetIncludeOpt.POLICY_SET_PROJECTS,
    #     PolicySetIncludeOpt.POLICY_SET_POLICIES,
    # ]

    if args.search:
        list_options.search = args.search

    if args.kind:
        list_options.kind = (
            PolicyKind.OPA if args.kind == "opa" else PolicyKind.SENTINEL
        )

    try:
        ps_list = client.policy_sets.list(args.org, list_options)

        print(f"Total policy sets: {ps_list.total_count}")
        print(f"Page {ps_list.current_page} of {ps_list.total_pages}")
        print()

        if not ps_list.items:
            print("No policy sets found for this organization.")
        else:
            for ps in ps_list.items:
                print(
                    f"- ID: {ps.id} | Name: {ps.name} | Kind: {ps.kind} | Global: {ps.Global}"
                )
                print(
                    f"  Policy Count: {ps.policy_count} | Workspace Count: {ps.workspace_count}"
                )
                print(f"  Created: {ps.created_at}")
                print()

    except Exception as e:
        print(f"Error listing policy sets: {e}")
        return

    # 2) Create a new policy set
    if args.create:
        if not args.policy_set_name:
            print("Error: --policy-set-name is required for create operation")
            return

        _print_header(f"Creating policy set: {args.policy_set_name}")

        try:
            create_options = PolicySetCreateOptions(
                name=args.policy_set_name,
                description=args.description,
                Global=args.global_policy if hasattr(args, "global_policy") else False,
                overridable=args.overridable,
                agent_enabled=args.agent_enabled,
            )

            if args.kind:
                create_options.kind = (
                    PolicyKind.OPA if args.kind == "opa" else PolicyKind.SENTINEL
                )

            # Add workspaces if provided
            if args.workspace_ids:
                create_options.workspaces = [
                    Workspace(id=ws_id) for ws_id in args.workspace_ids
                ]

            # Add projects if provided
            if args.project_ids:
                create_options.projects = [
                    Project(id=proj_id) for proj_id in args.project_ids
                ]

            # Add policies if provided
            if args.policy_ids:
                create_options.policies = [
                    Policy(id=pol_id) for pol_id in args.policy_ids
                ]

            new_ps = client.policy_sets.create(args.org, create_options)
            print("Successfully created policy set!")
            _print_policy_set_info(new_ps)

        except Exception as e:
            print(f"Error creating policy set: {e}")

    # 3) Read a specific policy set
    if args.read:
        if not args.policy_set_id:
            print("Error: --policy-set-id is required for read operation")
            return

        _print_header(f"Reading policy set: {args.policy_set_id}")

        try:
            # read_options = PolicySetReadOptions(
            #     include=[
            #         PolicySetIncludeOpt.POLICY_SET_WORKSPACES,
            #         PolicySetIncludeOpt.POLICY_SET_PROJECTS,
            #         PolicySetIncludeOpt.POLICY_SET_POLICIES,
            #         PolicySetIncludeOpt.POLICY_SET_WORKSPACE_EXCLUSIONS,
            #     ]
            # )

            ps = client.policy_sets.read(args.policy_set_id)
            _print_policy_set_info(ps)

        except Exception as e:
            print(f"Error reading policy set: {e}")

    # 4) Update a policy set
    if args.update:
        if not args.policy_set_id:
            print("Error: --policy-set-id is required for update operation")
            return

        _print_header(f"Updating policy set: {args.policy_set_id}")

        try:
            update_options = PolicySetUpdateOptions()

            if args.policy_set_name:
                update_options.name = args.policy_set_name
            if args.description:
                update_options.description = args.description
            if hasattr(args, "global_policy"):
                update_options.Global = args.global_policy
            if args.overridable:
                update_options.overridable = args.overridable
            if args.agent_enabled:
                update_options.agent_enabled = args.agent_enabled

            updated_ps = client.policy_sets.update(args.policy_set_id, update_options)
            print("Successfully updated policy set!")
            _print_policy_set_info(updated_ps)

        except Exception as e:
            print(f"Error updating policy set: {e}")

    # 5) Add workspaces to policy set
    if args.add_workspaces:
        if not args.policy_set_id or not args.workspace_ids:
            print(
                "Error: --policy-set-id and --workspace-ids are required for add-workspaces operation"
            )
            return

        _print_header(f"Adding workspaces to policy set: {args.policy_set_id}")

        try:
            add_ws_options = PolicySetAddWorkspacesOptions(
                workspaces=[Workspace(id=ws_id) for ws_id in args.workspace_ids]
            )

            client.policy_sets.add_workspaces(args.policy_set_id, add_ws_options)
            print(
                f"Successfully added {len(args.workspace_ids)} workspaces to policy set!"
            )

        except Exception as e:
            print(f"Error adding workspaces: {e}")

    # 6) Remove workspaces from policy set
    if args.remove_workspaces:
        if not args.policy_set_id or not args.workspace_ids:
            print(
                "Error: --policy-set-id and --workspace-ids are required for remove-workspaces operation"
            )
            return

        _print_header(f"Removing workspaces from policy set: {args.policy_set_id}")

        try:
            remove_ws_options = PolicySetRemoveWorkspacesOptions(
                workspaces=[Workspace(id=ws_id) for ws_id in args.workspace_ids]
            )

            client.policy_sets.remove_workspaces(args.policy_set_id, remove_ws_options)
            print(
                f"Successfully removed {len(args.workspace_ids)} workspaces from policy set!"
            )

        except Exception as e:
            print(f"Error removing workspaces: {e}")

    # 7) Add projects to policy set
    if args.add_projects:
        if not args.policy_set_id or not args.project_ids:
            print(
                "Error: --policy-set-id and --project-ids are required for add-projects operation"
            )
            return

        _print_header(f"Adding projects to policy set: {args.policy_set_id}")

        try:
            add_proj_options = PolicySetAddProjectsOptions(
                projects=[Project(id=proj_id) for proj_id in args.project_ids]
            )

            client.policy_sets.add_projects(args.policy_set_id, add_proj_options)
            print(f"Successfully added {len(args.project_ids)} projects to policy set!")

        except Exception as e:
            print(f"Error adding projects: {e}")

    # 8) Remove projects from policy set
    if args.remove_projects:
        if not args.policy_set_id or not args.project_ids:
            print(
                "Error: --policy-set-id and --project-ids are required for remove-projects operation"
            )
            return

        _print_header(f"Removing projects from policy set: {args.policy_set_id}")

        try:
            remove_proj_options = PolicySetRemoveProjectsOptions(
                projects=[Project(id=proj_id) for proj_id in args.project_ids]
            )

            client.policy_sets.remove_projects(args.policy_set_id, remove_proj_options)
            print(
                f"Successfully removed {len(args.project_ids)} projects from policy set!"
            )

        except Exception as e:
            print(f"Error removing projects: {e}")

    # 9) Add policies to policy set
    if args.add_policies:
        if not args.policy_set_id or not args.policy_ids:
            print(
                "Error: --policy-set-id and --policy-ids are required for add-policies operation"
            )
            return

        _print_header(f"Adding policies to policy set: {args.policy_set_id}")

        try:
            add_pol_options = PolicySetAddPoliciesOptions(
                policies=[Policy(id=pol_id) for pol_id in args.policy_ids]
            )

            client.policy_sets.add_policies(args.policy_set_id, add_pol_options)
            print(f"Successfully added {len(args.policy_ids)} policies to policy set!")

        except Exception as e:
            print(f"Error adding policies: {e}")

    # 10) Remove policies from policy set
    if args.remove_policies:
        if not args.policy_set_id or not args.policy_ids:
            print(
                "Error: --policy-set-id and --policy-ids are required for remove-policies operation"
            )
            return

        _print_header(f"Removing policies from policy set: {args.policy_set_id}")

        try:
            remove_pol_options = PolicySetRemovePoliciesOptions(
                policies=[Policy(id=pol_id) for pol_id in args.policy_ids]
            )

            client.policy_sets.remove_policies(args.policy_set_id, remove_pol_options)
            print(
                f"Successfully removed {len(args.policy_ids)} policies from policy set!"
            )

        except Exception as e:
            print(f"Error removing policies: {e}")

    # 11) Delete a policy set
    if args.delete:
        if not args.policy_set_id:
            print("Error: --policy-set-id is required for delete operation")
            return

        _print_header(f"Deleting policy set: {args.policy_set_id}")

        try:
            confirmation = input(
                f"Are you sure you want to delete policy set {args.policy_set_id}? (y/N): "
            )
            if confirmation.lower() == "y":
                client.policy_sets.delete(args.policy_set_id)
                print(f"Successfully deleted policy set: {args.policy_set_id}")
            else:
                print("Delete operation cancelled.")

        except Exception as e:
            print(f"Error deleting policy set: {e}")


if __name__ == "__main__":
    main()
