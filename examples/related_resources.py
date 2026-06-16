# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Accessing related resources: ?include=, relationships and the included block.

HCP Terraform returns related data in two places (JSON:API):
  * `relationships` — linkage refs (type + id) for every related resource
  * `included`      — full bodies of relations you ask for with ?include=

pyTFE hydrates the relations it models into typed fields, AND keeps both raw
blocks so nothing is ever lost. This example shows both.

Prerequisites:
    export TFE_TOKEN=...          # your API token
    python examples/related_resources.py ws-abc123     # a workspace id
"""

from __future__ import annotations

import sys

from pytfe import TFEClient
from pytfe.models.workspace import WorkspaceIncludeOpt, WorkspaceReadOptions


def main(workspace_id: str) -> None:
    client = TFEClient()

    # Ask the API to include the workspace's outputs and project.
    ws = client.workspaces.read_by_id_with_options(
        workspace_id,
        WorkspaceReadOptions(
            include=[WorkspaceIncludeOpt.OUTPUTS, WorkspaceIncludeOpt.PROJECT]
        ),
    )

    # 1) Typed hydration — modelled relations are filled from `included`.
    print(f"workspace: {ws.name}")
    if ws.project:
        print(f"  project (hydrated): {ws.project.name}")
    for o in ws.outputs:
        print(f"  output (hydrated):  {o.name} = {o.value!r}  ({o.output_type})")

    # 2) Lossless raw access — works for ANY relation, even unmodelled ones.
    print(f"\n  all relationships returned: {sorted(ws.relationships)}")

    # Resolve a relationship by name to full bodies (or bare refs if not included)
    for out in ws.related("outputs"):
        attrs = out.get("attributes", {})
        print(f"  related('outputs'): {attrs.get('name')} -> {attrs.get('value')!r}")

    # Look up a single included resource by type + id
    if ws.outputs:
        raw = ws.included_by("workspace-outputs", ws.outputs[0].id)
        print(f"\n  included_by(...): {raw and raw.get('attributes', {}).get('name')}")

    # The raw blocks are private — they never leak into serialized output:
    assert "included" not in ws.model_dump()
    assert "relationships" not in ws.model_dump()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python examples/related_resources.py <workspace-id>")
        raise SystemExit(2)
    main(sys.argv[1])
