#!/usr/bin/env python3
"""Organization tags operations example.

Demonstrates:
1. list() - list tags in an organization

This phase intentionally uses only organization-level parameters.
Tag IDs and workspace IDs can be passed in a later phase.
"""

import os

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.models.organization_tags import (
    AddWorkspacesToTagOptions,
    OrganizationTagsDeleteOptions,
)


def main() -> None:
    client = TFEClient(TFEConfig.from_env())

    organization_name = os.getenv("TFE_ORG", "example-org")
    tag_id = os.getenv("TFE_TAG_ID", "")
    workspace_id = os.getenv("TFE_WORKSPACE_ID", "")
    operation = "list"

    try:
        print("[LIST] Listing organization tags")
        print(f"[LIST] organization={organization_name}")
        tags = client.organization_tags.list(organization_name)
        print(f"[LIST] total_tags={len(tags.items)}")
        for item in tags.items:
            print(
                f"[LIST] id={item.id}, name={item.name}, instance_count={item.instance_count}"
            )

        # Guard: ensure env vars are set
        if not tag_id or not workspace_id:
            print("Skipping add/delete: set TFE_TAG_ID and TFE_WORKSPACE_ID first.")
            return

        # ---- Add workspace ----
        operation = "add_workspaces"
        print("[ADD_WORKSPACES] Associating a workspace to a tag")
        print(
            f"[ADD_WORKSPACES] organization={organization_name}, tag_id={tag_id}, workspace_id={workspace_id}"
        )
        try:
            client.organization_tags.add_workspaces(
                organization_name,
                tag_id,
                AddWorkspacesToTagOptions(workspace_ids=[workspace_id]),
            )
            print("[ADD_WORKSPACES] workspace associated")
        except TFEError as exc:
            print(f"[ADD_WORKSPACES] API error: {exc}")
            print(f"[ADD_WORKSPACES] failed operation={operation}")

        # ---- Delete tag ----
        operation = "delete"
        print("[DELETE] Deleting a tag from the organization")
        print(f"[DELETE] organization={organization_name}, tag_id={tag_id}")
        try:
            client.organization_tags.delete(
                organization_name,
                OrganizationTagsDeleteOptions(ids=[tag_id]),
            )
            print("[DELETE] tag deleted")
        except TFEError as exc:
            print(f"[DELETE] API error: {exc}")
            print(f"[DELETE] failed operation={operation}")
    except TFEError as exc:
        print(f"API error: {exc}")
        print(f"Failed during operation: {operation}")
        print("Check TFE_TOKEN, TFE_ADDRESS, and organization/tag/workspace IDs.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
