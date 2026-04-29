# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os
import uuid

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    ProjectAddTagBindingsOptions,
    ProjectCreateOptions,
    ProjectListOptions,
    ProjectSettingOverwrites,
    ProjectUpdateOptions,
    TagBinding,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _org_display(project) -> str:
    """Render organization safely for both string and object representations."""
    org = getattr(project, "organization", None)
    if org is None:
        return ""
    if isinstance(org, str):
        return org
    return getattr(org, "id", str(org))


def _parse_tag_pairs(tag_pairs: list[str] | None) -> list[TagBinding]:
    """Convert --tag key=value args into TagBinding models."""
    if not tag_pairs:
        return []

    tags: list[TagBinding] = []
    for pair in tag_pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                raise ValueError(f"Invalid tag format '{pair}'. Key is empty.")
            tags.append(TagBinding(key=key, value=value))
        else:
            key = pair.strip()
            if not key:
                raise ValueError(f"Invalid tag format '{pair}'.")
            tags.append(TagBinding(key=key, value=None))
    return tags


def main() -> None:
    parser = argparse.ArgumentParser(description="Projects demo for python-tfe SDK")

    parser.add_argument(
        "--address",
        default=os.getenv("TFE_ADDRESS", "https://app.terraform.io"),
        help="TFE/TFC address",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("TFE_TOKEN", ""),
        help="TFE/TFC API token",
    )
    parser.add_argument(
        "--organization",
        default=os.getenv("TFE_ORG", ""),
        help="Organization name",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=20,
        help="Page size for project listing",
    )

    parser.add_argument("--list", action="store_true", help="List projects")
    parser.add_argument("--create", action="store_true", help="Create a project")
    parser.add_argument("--read", action="store_true", help="Read a project")
    parser.add_argument("--update", action="store_true", help="Update a project")
    parser.add_argument("--delete", action="store_true", help="Delete a project")

    parser.add_argument(
        "--list-tag-bindings",
        action="store_true",
        help="List project tag bindings",
    )
    parser.add_argument(
        "--list-effective-tag-bindings",
        action="store_true",
        help="List project effective tag bindings",
    )
    parser.add_argument(
        "--add-tag-bindings",
        action="store_true",
        help="Add/replace tag bindings on project",
    )
    parser.add_argument(
        "--delete-tag-bindings",
        action="store_true",
        help="Delete all tag bindings from project",
    )

    parser.add_argument(
        "--project-id",
        help="Project ID for read/update/delete/tag operations",
    )
    parser.add_argument("--name", help="Project name for create/update")
    parser.add_argument("--description", help="Project description for create/update")
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Tag binding in key=value format (repeatable)",
    )
    parser.add_argument(
        "--create-random",
        action="store_true",
        help="Append a short random suffix to --name for create",
    )

    args = parser.parse_args()

    if not args.token:
        raise SystemExit("Error: --token or TFE_TOKEN is required")

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    has_org_op = args.list or args.create
    has_project_op = (
        args.read
        or args.update
        or args.delete
        or args.list_tag_bindings
        or args.list_effective_tag_bindings
        or args.add_tag_bindings
        or args.delete_tag_bindings
    )

    if has_org_op and not args.organization:
        raise SystemExit("Error: --organization or TFE_ORG is required")

    if has_project_op and not args.project_id:
        raise SystemExit("Error: --project-id is required for selected operation")

    # 1) List projects
    if args.list:
        _print_header(f"Listing projects for organization: {args.organization}")
        list_options = ProjectListOptions(page_size=args.page_size)

        count = 0
        for project in client.projects.list(args.organization, list_options):
            count += 1
            print(f"- {project.name} (ID: {project.id})")
            print(f"  Description: {project.description}")
            print(f"  Workspaces: {project.workspace_count}")
            print(f"  Default execution mode: {project.default_execution_mode}")
            print(
                f"  Auto destroy activity duration: {project.auto_destroy_activity_duration}"
            )
            print(f"  Created at: {project.created_at}")
            print(f"  Updated at: {project.updated_at}")
            print(f"  Setting overwrites: {project.setting_overwrites}")
            print(f"  Default agent pool: {project.default_agent_pool}")
            print(f"  Organization: {_org_display(project)}")

            print()

        if count == 0:
            print("No projects found.")
        else:
            print(f"Total: {count} projects")

    # 2) Create project
    if args.create:
        if not args.name:
            raise SystemExit("Error: --name is required for create")

        name = args.name
        if args.create_random:
            name = f"{name}-{uuid.uuid4().hex[:8]}"

        _print_header(f"Creating project: {name}")

        tags = _parse_tag_pairs(args.tag)
        create_options = ProjectCreateOptions(
            name=name,
            description=args.description,
            auto_destroy_activity_duration="14d",
            default_execution_mode="remote",
            default_agent_pool_id=None,
            setting_overwrites=ProjectSettingOverwrites(
                execution_mode=False,
                agent_pool=False,
            ),
            tag_bindings=tags,
        )

        project = client.projects.create(args.organization, create_options)
        print(f"Created project: {project.id}")
        print(f"Name: {project.name}")
        print(f"Description: {project.description}")
        print(f"Workspaces: {project.workspace_count}")
        print(f"Default execution mode: {project.default_execution_mode}")
        print(
            f"Auto destroy activity duration: {project.auto_destroy_activity_duration}"
        )
        print(f"Created at: {project.created_at}")
        print(f"Updated at: {project.updated_at}")
        print(f"Setting overwrites: {project.setting_overwrites}")
        print(f"Default agent pool: {project.default_agent_pool}")
        print(f"Organization: {_org_display(project)}")

    # 3) Read project
    if args.read:
        _print_header(f"Reading project: {args.project_id}")
        project = client.projects.read(args.project_id)
        print(f"ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Description: {project.description}")
        print(f"Organization: {_org_display(project)}")
        print(f"Created at: {project.created_at}")
        print(f"Updated at: {project.updated_at}")
        print(f"Workspace count: {project.workspace_count}")
        print(f"Default execution mode: {project.default_execution_mode}")
        print(
            f"Auto destroy activity duration: {project.auto_destroy_activity_duration}"
        )

    # 4) Update project
    if args.update:
        if args.name is None and args.description is None and not args.tag:
            raise SystemExit(
                "Error: provide at least one of --name, --description or --tag for update"
            )

        _print_header(f"Updating project: {args.project_id}")

        tags = _parse_tag_pairs(args.tag)
        update_options = ProjectUpdateOptions(
            name=args.name,
            description=args.description,
            tag_bindings=tags if tags else None,
        )

        updated = client.projects.update(args.project_id, update_options)
        print("Project updated successfully")
        print(f"ID: {updated.id}")
        print(f"Name: {updated.name}")
        print(f"Description: {updated.description}")

    # 5) Delete project
    if args.delete:
        _print_header(f"Deleting project: {args.project_id}")
        client.projects.delete(args.project_id)
        print("Project deleted successfully")

    # 6) List tag bindings
    if args.list_tag_bindings:
        _print_header(f"Listing tag bindings for project: {args.project_id}")
        bindings = client.projects.list_tag_bindings(args.project_id)

        if not bindings:
            print("No tag bindings found.")
        else:
            for tag in bindings:
                print(f"- {tag.key}={tag.value}")
            print(f"Total: {len(bindings)} tag bindings")

    # 7) List effective tag bindings
    if args.list_effective_tag_bindings:
        _print_header(f"Listing effective tag bindings for project: {args.project_id}")
        bindings = client.projects.list_effective_tag_bindings(args.project_id)

        if not bindings:
            print("No effective tag bindings found.")
        else:
            for tag in bindings:
                print(f"- {tag.key}={tag.value}")
            print(f"Total: {len(bindings)} effective tag bindings")

    # 8) Add tag bindings
    if args.add_tag_bindings:
        tags = _parse_tag_pairs(args.tag)
        if not tags:
            raise SystemExit(
                "Error: at least one --tag key=value is required for --add-tag-bindings"
            )

        _print_header(f"Adding tag bindings to project: {args.project_id}")
        options = ProjectAddTagBindingsOptions(tag_bindings=tags)
        updated_tags = client.projects.add_tag_bindings(args.project_id, options)
        for tag in updated_tags:
            print(f"- {tag.key}={tag.value}")
        print(f"Total returned: {len(updated_tags)} tag bindings")

    # 9) Delete tag bindings
    if args.delete_tag_bindings:
        _print_header(f"Deleting all tag bindings from project: {args.project_id}")
        client.projects.delete_tag_bindings(args.project_id)
        print("Deleted all project tag bindings")


if __name__ == "__main__":
    main()
