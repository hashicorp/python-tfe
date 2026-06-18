# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Accessing related resources: ?include=, relationships and the included block.

HCP Terraform returns related data in two places (JSON:API):
  * `relationships` — linkage refs (type + id) for every related resource
  * `included`      — full bodies of relations you ask for with ?include=

pyTFE hydrates the relations it models into typed fields, AND keeps both raw
blocks so nothing is ever lost. The one rule: a typed relationship field always
carries at least the `id`; pass ?include= to fill in the rest. This example shows
both a workspace and a team.

Prerequisites:
    export TFE_TOKEN=...          # your API token
    export TFE_ORG=...            # org to look up a team in (optional)
    python examples/related_resources.py ws-abc123     # a workspace id
"""

from __future__ import annotations

import os
import sys

from pytfe import TFEClient
from pytfe.models.team import TeamIncludeOpt, TeamReadOptions
from pytfe.models.workspace import WorkspaceIncludeOpt, WorkspaceReadOptions


def workspace_demo(client: TFEClient, workspace_id: str) -> None:
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


def team_demo(client: TFEClient, org: str) -> None:
    # Grab any team in the org, then read it back asking for its users.
    teams = list(client.teams.list(org))
    if not teams:
        print(f"\n(no teams in {org} to demo)")
        return

    team = client.teams.read(
        teams[0].id,
        TeamReadOptions(include=[TeamIncludeOpt.TEAM_USERS]),
    )

    # Typed hydration: team.users carries the full user bodies, not just ids.
    print(f"\nteam: {team.name}  ({team.user_count} members)")
    for user in team.users or []:
        # Without include=users this would be an id-only stub (username == None).
        print(f"  user (hydrated): {user.id}  {user.username}")

    # The raw escape hatch is populated too, for relations not modelled as fields.
    print(
        f"  has_included={team.has_included}  relationships={sorted(team.relationships)}"
    )
    assert "included" not in team.model_dump()


def main(workspace_id: str) -> None:
    client = TFEClient()
    workspace_demo(client, workspace_id)

    org = os.environ.get("TFE_ORG")
    if org:
        team_demo(client, org)
    else:
        print("\n(set TFE_ORG to also run the team include demo)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python examples/related_resources.py <workspace-id>")
        raise SystemExit(2)
    main(sys.argv[1])
