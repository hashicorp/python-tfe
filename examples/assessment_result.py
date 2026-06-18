# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Assessment results (workspace health / drift detection) demo.

Find an assessment result via a workspace's current assessment, then read its
summary and (optionally) the underlying JSON plan / log output.
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assessment results demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--id", help="Assessment result ID to read (e.g. asmtres-xxxxx)"
    )
    parser.add_argument(
        "--workspace-id",
        help="Workspace ID to discover the current assessment result from",
    )
    parser.add_argument(
        "--json-output", action="store_true", help="Also fetch the JSON plan output"
    )
    parser.add_argument(
        "--log-output", action="store_true", help="Also fetch the JSON log output"
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    ar_id = args.id
    if not ar_id and args.workspace_id:
        _print_header(f"Current assessment for workspace {args.workspace_id}")
        current = client.workspaces.current_assessment_result(args.workspace_id)
        if not current:
            print("Workspace has no assessment result (health assessments disabled?).")
            return 0
        ar_id = current.id
        print(f"Found assessment result: {ar_id}")

    if not ar_id:
        print("Provide --id or --workspace-id")
        return 2

    _print_header(f"Assessment result: {ar_id}")
    ar = client.assessment_results.read(ar_id)
    print(f"  drifted:    {ar.drifted}")
    print(f"  succeeded:  {ar.succeeded}")
    print(f"  created_at: {ar.created_at}")
    if ar.error_message:
        print(f"  error:      {ar.error_message}")

    # The output endpoints require a user or team token with workspace admin access.
    if args.json_output:
        _print_header("JSON plan output")
        out = client.assessment_results.json_output(ar_id)
        print(f"  format_version: {out.get('format_version') if out else None}")

    if args.log_output:
        _print_header("JSON log output (first 500 chars)")
        print(client.assessment_results.log_output(ar_id)[:500] or "(no log output)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
