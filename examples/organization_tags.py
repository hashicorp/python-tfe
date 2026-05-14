#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Organization tags operations example.

Demonstrates:
1. list()           - list tags in an organization
2. add_workspaces() - associate a workspace with a tag
3. delete()         - delete a tag from an organization

Usage:
    python examples/organization_tags.py --org my-org
    python examples/organization_tags.py --org my-org --tag-id tag-abc123 --workspace-id ws-xyz
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.models.organization_tags import AddWorkspacesToTagOptions, OrganizationTagsDeleteOptions


def main() -> None:
    parser = argparse.ArgumentParser(description="Organization Tags demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--org",
        default=os.getenv("TFE_ORG", ""),
        help="Organization name",
    )
    parser.add_argument(
        "--tag-id",
        default=os.getenv("TFE_TAG_ID", ""),
        help="Tag ID for add/delete operations",
    )
    parser.add_argument(
        "--workspace-id",
        default=os.getenv("TFE_WORKSPACE_ID", ""),
        help="Workspace ID to associate with tag",
    )
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token required")
        return

    if not args.org:
        print("Error: TFE_ORG environment variable or --org required")
        return

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List tags
    try:
        print("[LIST] Listing organization tags")
        print(f"[LIST] organization={args.org}")
        tags = list(client.organization_tags.list(args.org))
        print(f"[LIST] total_tags={len(tags)}")
        for tag in tags:
            print(
                f"[LIST] id={tag.id}, name={tag.name}, instance_count={tag.instance_count}"
            )
        if not tags:
            print("[LIST] no tags found")
    except TFEError as exc:
        print(f"[LIST] API error: {exc}")
        return

    if not args.tag_id:
        print("[ADD_WORKSPACES] skipped: set --tag-id or TFE_TAG_ID")
        print("[DELETE] skipped: set --tag-id or TFE_TAG_ID")
        return

    # 2) Add workspace to tag
    if args.workspace_id:
        print("[ADD_WORKSPACES] Associating a workspace to a tag")
        print(
            f"[ADD_WORKSPACES] organization={args.org}, tag_id={args.tag_id}, workspace_id={args.workspace_id}"
        )
        try:
            client.organization_tags.add_workspaces(
                args.org,
                args.tag_id,
                AddWorkspacesToTagOptions(workspace_ids=[args.workspace_id]),
            )
            print("[ADD_WORKSPACES] workspace associated")
        except TFEError as exc:
            print(f"[ADD_WORKSPACES] API error: {exc}")
    else:
        print("[ADD_WORKSPACES] skipped: set --workspace-id or TFE_WORKSPACE_ID")

    # 3) Delete tag
    print("[DELETE] Deleting a tag from the organization")
    print(f"[DELETE] organization={args.org}, tag_id={args.tag_id}")
    try:
        client.organization_tags.delete(
            args.org,
            OrganizationTagsDeleteOptions(ids=[args.tag_id]),
        )
        print("[DELETE] tag deleted")
    except TFEError as exc:
        print(f"[DELETE] API error: {exc}")


if __name__ == "__main__":
    main()
