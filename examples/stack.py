# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    AgentPool,
    Project,
    StackCreateOptions,
    StackListOptions,
    StackSortColumn,
    StackUpdateOptions,
    StackVcsRepoOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_stack(item):
    print(f"- id: {item.id}")
    print(f"- name: {item.name}")
    print(f"- description: {item.description}")
    print(f"- created_at: {item.created_at}")
    print(f"- updated_at: {item.updated_at}")
    print(f"- speculative_enabled: {item.speculative_enabled}")
    print(f"- project_id: {item.project.id if item.project else None}")
    print(f"- agent_pool_id: {item.agent_pool.id if item.agent_pool else None}")

    if item.vcs_repo:
        print("- vcs_repo:")
        print(f"  identifier={item.vcs_repo.identifier}")
        print(f"  branch={item.vcs_repo.branch}")
        print(f"  github_app_installation_id={item.vcs_repo.gha_installation_id}")
        print(f"  oauth_token_id={item.vcs_repo.oauth_token_id}")


def _build_vcs_repo_options(args) -> StackVcsRepoOptions | None:
    if not args.vcs_identifier:
        return None

    return StackVcsRepoOptions(
        identifier=args.vcs_identifier,
        branch=args.vcs_branch,
        gha_installation_id=args.vcs_github_app_installation_id,
        oauth_token_id=args.vcs_oauth_token_id,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Stacks operations demo for python-tfe"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", help="Organization name (required for list)")
    parser.add_argument(
        "--operation",
        required=True,
        choices=["create", "read", "update", "list", "delete", "force-delete"],
        help="Operation to execute",
    )

    parser.add_argument(
        "--stack-id", help="Stack ID (required for read/update/delete/force-delete)"
    )

    parser.add_argument("--name", help="Stack name (required for create)")
    parser.add_argument("--description", help="Stack description")
    parser.add_argument(
        "--speculative-enabled",
        type=lambda v: str(v).lower() in ("1", "true", "yes", "y"),
        default=None,
        help="Enable speculation (true/false)",
    )

    parser.add_argument(
        "--project-id",
        help="Project ID (required for create, optional for list filter)",
    )
    parser.add_argument(
        "--agent-pool-id", help="Agent pool ID (optional for create/update)"
    )

    parser.add_argument(
        "--vcs-identifier",
        help="VCS repo identifier (e.g. org/repo), optional for create/update",
    )
    parser.add_argument("--vcs-branch", help="VCS branch")
    parser.add_argument(
        "--vcs-github-app-installation-id",
        help="GitHub App installation ID for VCS repo",
    )
    parser.add_argument("--vcs-oauth-token-id", help="OAuth token ID for VCS repo")

    parser.add_argument("--page-size", type=int, default=20, help="Page size for list")
    parser.add_argument(
        "--sort",
        choices=[item.value for item in StackSortColumn],
        default=None,
        help="Sort column for list",
    )
    parser.add_argument(
        "--search-name",
        default=None,
        help="Search stacks by name",
    )

    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    if args.operation == "create":
        if not args.name:
            parser.error("--name is required for operation=create")
        if not args.project_id:
            parser.error("--project-id is required for operation=create")

        _print_header("Creating stack")
        options = StackCreateOptions(
            name=args.name,
            description=args.description,
            speculative_enabled=args.speculative_enabled,
            vcs_repo=_build_vcs_repo_options(args),
            project=Project(id=args.project_id),
            agent_pool=AgentPool(id=args.agent_pool_id) if args.agent_pool_id else None,
        )
        result = client.stacks.create(options)
        print("Created stack")
        _print_stack(result)
        return

    if args.operation == "read":
        if not args.stack_id:
            parser.error("--stack-id is required for operation=read")

        _print_header("Reading stack")
        result = client.stacks.read(args.stack_id)
        print("Retrieved stack")
        _print_stack(result)
        return

    if args.operation == "update":
        if not args.stack_id:
            parser.error("--stack-id is required for operation=update")
        if not any(
            [
                args.name,
                args.description,
                args.speculative_enabled is not None,
                args.agent_pool_id,
                args.vcs_identifier,
                args.vcs_branch,
                args.vcs_github_app_installation_id,
                args.vcs_oauth_token_id,
                args.project_id,
            ]
        ):
            parser.error("Provide at least one field to update")

        _print_header("Updating stack")
        options = StackUpdateOptions(
            name=args.name,
            description=args.description,
            speculative_enabled=args.speculative_enabled,
            vcs_repo=_build_vcs_repo_options(args),
            agent_pool=AgentPool(id=args.agent_pool_id) if args.agent_pool_id else None,
            project=Project(id=args.project_id) if args.project_id else None,
        )
        result = client.stacks.update(args.stack_id, options)
        print("Updated stack")
        _print_stack(result)
        return

    if args.operation == "list":
        if not args.organization:
            parser.error("--organization is required for operation=list")

        _print_header("Listing stacks")
        list_options = StackListOptions(
            page_size=args.page_size,
            project_id=args.project_id,
            sort=StackSortColumn(args.sort) if args.sort else None,
            search_by_name=args.search_name,
        )

        items = list(client.stacks.list(args.organization, list_options))
        print(f"Found {len(items)} stacks")
        for item in items:
            print("-")
            _print_stack(item)
        return

    if args.operation == "delete":
        if not args.stack_id:
            parser.error("--stack-id is required for operation=delete")

        _print_header("Deleting stack")
        client.stacks.delete(args.stack_id)
        print(f"Deleted stack: {args.stack_id}")
        return

    if args.operation == "force-delete":
        if not args.stack_id:
            parser.error("--stack-id is required for operation=force-delete")

        _print_header("Force deleting stack")
        client.stacks.force_delete(args.stack_id)
        print(f"Force deleted stack: {args.stack_id}")
        return


if __name__ == "__main__":
    main()
