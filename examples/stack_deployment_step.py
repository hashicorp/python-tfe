#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
"""Example: list, read, advance, list diagnostics, and download artifacts for stack deployment steps.

Usage::

    export TFE_TOKEN=<your-token>

    # List steps in a deployment run
    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123

    # Read a single step
    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123 --read --step-id sds-xyz789

    # Advance a step that is in the pending-operator state
    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123 --advance --step-id sds-xyz789

    # List diagnostics for a step
    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123 --diagnostics --step-id sds-xyz789

    # Download an artifact (writes to stdout or a file)
    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123 --artifact plan-description --step-id sds-xyz789

    python3 examples/stack_deployment_step.py \\
        --run-id sdr-abc123 --artifact plan-description --step-id sds-xyz789 \\
        --output-file /tmp/plan.txt
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    StackDeploymentStepArtifactType,
    StackDeploymentStepIncludeOpt,
    StackDeploymentStepListOptions,
    StackDeploymentStepReadOptions,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage stack deployment steps")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN"))
    parser.add_argument(
        "--run-id", required=True, help="Deployment run ID (sdr-...)"
    )
    parser.add_argument("--step-id", help="Deployment step ID (sds-...)")
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument(
        "--include-approval",
        action="store_true",
        help="Include stack-approval relation in list/read responses",
    )
    parser.add_argument(
        "--include-state",
        action="store_true",
        help="Include stack-state relation in list/read responses",
    )
    parser.add_argument(
        "--read", action="store_true", help="Read a specific step (requires --step-id)"
    )
    parser.add_argument(
        "--advance",
        action="store_true",
        help="Advance a step in pending-operator state (requires --step-id)",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="List diagnostics for a step (requires --step-id)",
    )
    parser.add_argument(
        "--artifact",
        choices=["plan-description", "apply-description", "plan-debug-log", "apply-debug-log"],
        help="Download an artifact (requires --step-id)",
    )
    parser.add_argument(
        "--output-file",
        help="Write downloaded artifact to this file instead of stdout",
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List deployment steps for the run
    _print_header(f"Listing deployment steps for run: {args.run_id}")
    includes = []
    if args.include_approval:
        includes.append(StackDeploymentStepIncludeOpt.STACK_APPROVAL)
    if args.include_state:
        includes.append(StackDeploymentStepIncludeOpt.STACK_STATE)
    opts = StackDeploymentStepListOptions(page_size=args.page_size, include=includes or None)
    count = 0
    for step in client.stack_deployment_steps.list(args.run_id, options=opts):
        count += 1
        print(f"- {step.id}")
        print(f"  Status:         {step.status.value if step.status else None}")
        print(f"  Operation type: {step.operation_type}")
        print(f"  Created:        {step.created_at}")
        print(f"  Updated:        {step.updated_at}")
        if step.stack_deployment_run:
            print(f"  Run:            {step.stack_deployment_run.id}")
        print()
    print(f"Total: {count} deployment step(s)")

    # 2) Read a specific step
    if args.read:
        if not args.step_id:
            print("--step-id is required for --read")
        else:
            _print_header(f"Reading deployment step: {args.step_id}")
            includes = []
            if args.include_approval:
                includes.append(StackDeploymentStepIncludeOpt.STACK_APPROVAL)
            if args.include_state:
                includes.append(StackDeploymentStepIncludeOpt.STACK_STATE)
            read_opts = StackDeploymentStepReadOptions(include=includes or None)
            step = client.stack_deployment_steps.read(args.step_id, options=read_opts)
            print(f"ID:             {step.id}")
            print(f"Status:         {step.status.value if step.status else None}")
            print(f"Operation type: {step.operation_type}")
            print(f"Created:        {step.created_at}")
            print(f"Updated:        {step.updated_at}")

    # 3) Advance a step
    if args.advance:
        if not args.step_id:
            print("--step-id is required for --advance")
        else:
            _print_header(f"Advancing step: {args.step_id}")
            client.stack_deployment_steps.advance(args.step_id)
            print(f"Advanced {args.step_id}")

    # 4) List diagnostics
    if args.diagnostics:
        if not args.step_id:
            print("--step-id is required for --diagnostics")
        else:
            _print_header(f"Diagnostics for step: {args.step_id}")
            diag_count = 0
            for diag in client.stack_deployment_steps.list_diagnostics(args.step_id):
                diag_count += 1
                print(f"- {diag.id}")
                print(f"  Severity:     {diag.severity}")
                print(f"  Summary:      {diag.summary}")
                print(f"  Detail:       {diag.detail}")
                print(f"  Acknowledged: {diag.acknowledged}")
                print()
            print(f"Total: {diag_count} diagnostic(s)")

    # 5) Download an artifact
    if args.artifact:
        if not args.step_id:
            print("--step-id is required for --artifact")
        else:
            artifact_type = StackDeploymentStepArtifactType(args.artifact)
            _print_header(f"Downloading artifact '{args.artifact}' for step: {args.step_id}")
            content = client.stack_deployment_steps.download_artifact(
                args.step_id, artifact_type
            )
            if args.output_file:
                with open(args.output_file, "wb") as fh:
                    fh.write(content)
                print(f"Artifact written to {args.output_file} ({len(content)} bytes)")
            else:
                print(content.decode(errors="replace"))


if __name__ == "__main__":
    main()
