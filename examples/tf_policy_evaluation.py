# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""tf-policy evaluation demo for the python-tfe SDK.

Usage examples::

    # List evaluations for a run:
    python examples/tf_policy_evaluation.py --run-id run-abc123

    # Read a specific evaluation with sideloaded set outcomes:
    python examples/tf_policy_evaluation.py --run-id run-abc123 --read tfpeval-abc123

    # List evaluations and override any awaiting_override ones (dry-run):
    python examples/tf_policy_evaluation.py --run-id run-abc123 --override --dry-run

    # Override with a comment:
    python examples/tf_policy_evaluation.py --run-id run-abc123 --override \
        --comment "Approved by ops team — ticket OPS-123"

Environment variables::

    TFE_TOKEN    - HCP Terraform / TFE API token (required)
    TFE_ADDRESS  - API address (default: https://app.terraform.io)
    TFE_RUN_ID   - Run ID (overridden by --run-id)
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    TfPolicyEvaluationListOptions,
    TfPolicyEvaluationOverrideOptions,
    TfPolicyEvaluationStatus,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_result_count(result_count) -> None:  # type: ignore[no-untyped-def]
    if result_count is None:
        return
    print(
        f"  result-count: passed={result_count.passed}  "
        f"advisory-failed={result_count.advisory_failed}  "
        f"mandatory-failed={result_count.mandatory_failed}  "
        f"errored={result_count.errored}  unknown={result_count.unknown}"
    )


def _print_evaluation(evaluation) -> None:  # type: ignore[no-untyped-def]
    print(f"  id:          {evaluation.id}")
    print(f"  status:      {evaluation.status}")
    print(f"  stage-type:  {evaluation.stage_type}")
    _print_result_count(evaluation.result_count)
    if evaluation.error:
        print(f"  error:       [{evaluation.error.type}] {evaluation.error.summary}")
    if evaluation.actions:
        print(f"  overridable: {evaluation.actions.is_overridable}")


def main() -> int:
    parser = argparse.ArgumentParser(description="tf-policy evaluation demo")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--run-id",
        default=os.getenv("TFE_RUN_ID", ""),
        help="Run ID (e.g. run-abc123)",
    )
    parser.add_argument(
        "--read",
        metavar="EVAL_ID",
        help="Read a specific evaluation by ID (e.g. tfpeval-abc123)",
    )
    parser.add_argument(
        "--override",
        action="store_true",
        help="Override any evaluations that are in awaiting_override status",
    )
    parser.add_argument(
        "--comment",
        default="",
        help="Comment to attach when overriding",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be overridden without sending the request",
    )
    args = parser.parse_args()

    if not args.token:
        print("error: TFE_TOKEN is not set")
        return 2
    if not args.run_id and not args.read:
        print("error: --run-id or --read is required")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    try:
        # ── Read a single evaluation ──────────────────────────────────────────
        if args.read:
            _print_header(f"Reading evaluation: {args.read}")
            opts = TfPolicyEvaluationListOptions(include="tf_policy_set_outcomes")
            evaluation = client.tf_policy_evaluations.read(args.read, options=opts)
            _print_evaluation(evaluation)

            # Drill into set outcomes
            _print_header("Policy-set outcomes (nested list)")
            outcomes = list(client.tf_policy_evaluations.list_set_outcomes(args.read))
            if not outcomes:
                print("  No set outcomes found.")
            for outcome in outcomes:
                print(f"\n  outcome id:  {outcome.id}")
                print(f"  policy-set:  {outcome.policy_set_name}")
                print(f"  overridable: {outcome.overridable}")
                _print_result_count(outcome.result_count)
                for o in outcome.outcomes:
                    marker = "PASS" if str(o.status) == "passed" else "FAIL"
                    print(
                        f"    [{marker}] {o.policy_name}  "
                        f"enforcement={o.enforcement_level}  status={o.status}"
                    )
            return 0

        # ── List evaluations for a run ────────────────────────────────────────
        _print_header(f"tf-policy evaluations for run: {args.run_id}")
        evaluations = list(client.tf_policy_evaluations.list(args.run_id))
        if not evaluations:
            print("  No tf-policy evaluations found for this run.")
            return 0

        overridable_ids: list[str] = []
        for evaluation in evaluations:
            _print_evaluation(evaluation)
            print()
            if evaluation.status == TfPolicyEvaluationStatus.AWAITING_OVERRIDE:
                overridable_ids.append(evaluation.id)

        print(f"Total: {len(evaluations)} evaluation(s).")

        # ── Optional override ─────────────────────────────────────────────────
        if args.override:
            if not overridable_ids:
                print("\nNo evaluations are awaiting override.")
                return 0

            for eval_id in overridable_ids:
                if args.dry_run:
                    print(f"\n[dry-run] Would override {eval_id}")
                    continue

                _print_header(f"Overriding evaluation: {eval_id}")
                override_opts = (
                    TfPolicyEvaluationOverrideOptions(comment=args.comment)
                    if args.comment
                    else None
                )
                result = client.tf_policy_evaluations.override(eval_id, override_opts)
                print(f"  new status: {result.status}")

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
