#!/usr/bin/env python3
"""Workspace health-assessment example.

Demonstrates two new workspace endpoints:

  * ``client.workspaces.current_assessment_result(workspace_id)``
  * ``client.workspaces.list_applicable_varsets(workspace_id)``

Run with:

    TFE_TOKEN=... python examples/workspace_assessment.py \\
        --workspace-id ws-XXXXXXXXXXXX

The POST /workspaces/{id}/actions/assess endpoint is intentionally NOT
exposed by the SDK — HCP Terraform restricts it to browser sessions and
rejects API-token callers with HTTP 403.
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def _header(title: str) -> None:
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument(
        "--workspace-id",
        required=True,
        help="Workspace id (assessments must be enabled to see a result)",
    )
    args = p.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    _header("Current assessment result")
    result = client.workspaces.current_assessment_result(args.workspace_id)
    if result is None:
        print(
            "  no assessment result yet — assessments may be disabled on this "
            "workspace, or none have run."
        )
    else:
        print(f"  id:                  {result.id}")
        print(f"  succeeded:           {result.succeeded}")
        print(f"  all_checks_succeeded:{result.all_checks_succeeded}")
        print(f"  drifted:             {result.drifted}")
        print(f"  resources_drifted:   {result.resources_drifted}")
        print(f"  resources_undrifted: {result.resources_undrifted}")
        print(f"  checks_passed:       {result.checks_passed}")
        print(f"  checks_failed:       {result.checks_failed}")
        print(f"  checks_errored:      {result.checks_errored}")
        print(f"  created_at:          {result.created_at}")
        if result.error_message:
            print(f"  error_message:       {result.error_message}")

    _header("Applicable variable sets for this workspace")
    count = 0
    for vs in client.workspaces.list_applicable_varsets(args.workspace_id):
        count += 1
        print(
            f"  - {vs.get('id'):<24} {vs.get('name'):<30} "
            f"global={vs.get('global')} priority={vs.get('priority')} "
            f"vars={vs.get('var-count')}"
        )
    if count == 0:
        print("  (none)")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
