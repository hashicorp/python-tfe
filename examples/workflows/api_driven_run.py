# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
API-driven run using pytfe.workflows

The same job as docs/scenarios/api-driven-run.md, but without the hand-rolled
polling loop: upload a configuration directory, wait for the plan, show what it
would do, and apply only after an explicit approval.

Prerequisites:
    - TFE_TOKEN   API token
    - TFE_ADDRESS (optional) defaults to https://app.terraform.io

Quick Start:
    python examples/workflows/api_driven_run.py --help

1. Plan only (never applies, safe to run anywhere):
    python examples/workflows/api_driven_run.py \\
        --org my-org --workspace web --dir ./terraform --speculative

2. Plan, then ask before applying:
    python examples/workflows/api_driven_run.py \\
        --org my-org --workspace web --dir ./terraform --interactive

3. Non-interactive apply (a human has already approved):
    python examples/workflows/api_driven_run.py \\
        --org my-org --workspace web --dir ./terraform --confirmed

4. Allow a plan that destroys or replaces resources:
    python examples/workflows/api_driven_run.py \\
        --org my-org --workspace web --dir ./terraform \\
        --confirmed --allow-destroy

5. Read-only client - every write raises ReadOnlyViolation:
    python examples/workflows/api_driven_run.py \\
        --org my-org --workspace web --dir ./terraform --read-only
"""

from __future__ import annotations

import argparse
import os
import sys

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.workflows import (
    PlanSummary,
    WorkspaceSpec,
    apply_with_gate,
    ensure_workspace,
    read_outputs,
    run_from_directory,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def ask(plan: PlanSummary) -> bool:
    """Show the plan and ask a human whether to apply it."""
    _print_header("Plan")
    print(plan)
    for address in plan.destroy_addresses:
        print(f"  - DESTROY {address}")
    for address in plan.replace_addresses:
        print(f"  ~ REPLACE {address}")
    if plan.monthly_cost_delta:
        print(f"  monthly cost delta: {plan.monthly_cost_delta}")
    return input("\nApply this plan? [y/N] ").strip().lower() == "y"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="API-driven run demo for the python-tfe workflows layer"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--workspace", required=True, help="Workspace name")
    parser.add_argument("--dir", required=True, help="Configuration directory")
    parser.add_argument(
        "--terraform-version", help="Pin the workspace to this Terraform version"
    )
    parser.add_argument(
        "--speculative",
        action="store_true",
        help="Plan only; the run can never be applied",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Prompt before applying"
    )
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Assert that a human has already approved the apply",
    )
    parser.add_argument(
        "--allow-destroy",
        action="store_true",
        help="Permit a plan that destroys or replaces resources",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Build a client that cannot mutate anything",
    )
    args = parser.parse_args()

    config = TFEConfig(
        address=args.address,
        token=args.token,
        read_only=args.read_only,
        user_agent_suffix="pytfe-workflows-example/1.0",
    )

    with TFEClient(config) as tfe:
        try:
            _print_header("Ensure workspace")
            spec = WorkspaceSpec(
                terraform_version=args.terraform_version,
                auto_apply=False,
            )
            ensured = ensure_workspace(tfe, args.org, args.workspace, spec=spec)
            print(ensured)

            _print_header("Run")
            result = run_from_directory(
                tfe,
                args.dir,
                organization=args.org,
                workspace_name=args.workspace,
                speculative=args.speculative,
                confirm=ask if args.interactive else None,
                confirmed=args.confirmed,
                allow_destroy=args.allow_destroy,
                on_status=lambda run: print(
                    f"  {getattr(run.status, 'value', run.status)}"
                ),
            )

            print(f"\nphase:  {result.phase}")
            print(f"run:    {result.url or result.run_id}")
            if result.plan:
                print(f"plan:   {result.plan}")
            for warning in result.warnings:
                print(f"warn:   {warning}")

            if result.phase == "awaiting_confirmation":
                print(
                    "\nNothing was applied. Re-run with --interactive to be asked, "
                    "or --confirmed once a human has approved."
                )
            elif result.phase == "refused_destructive":
                print(
                    "\nRefused: the plan destroys or replaces resources. "
                    "Pass --allow-destroy to permit it."
                )
            elif result.phase == "errored" and result.failure:
                _print_header("Diagnosis")
                print(f"stage:      {result.failure.stage}")
                print(f"message:    {result.failure.message}")
                if result.failure.suggestion:
                    print(f"suggestion: {result.failure.suggestion}")
                return 1
            elif result.phase == "applied":
                _print_header("Outputs")
                for key, value in read_outputs(
                    tfe, organization=args.org, workspace_name=args.workspace
                ).values.items():
                    print(f"  {key} = {value}")

            # A separate approval step is the shape an agent should use: plan in
            # one call, let a human look, then apply in another.
            if result.phase == "awaiting_confirmation" and args.interactive:
                if ask(result.plan) and result.run_id:
                    applied = apply_with_gate(
                        tfe,
                        result.run_id,
                        confirmed=True,
                        allow_destroy=args.allow_destroy,
                    )
                    print(f"phase: {applied.phase}")

        except TFEError as exc:
            print(f"\nerror: {exc}", file=sys.stderr)
            if exc.hint:
                print(f"hint:  {exc.hint}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
