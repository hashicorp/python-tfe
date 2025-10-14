from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import PolicyEvaluationListOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Policy Evaluations demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--task-stage-id",
        required=True,
        help="Task stage ID to list policy evaluations for",
    )
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument is required")
        return

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # List all policy evaluations for the given task stage
    _print_header(f"Listing policy evaluations for task stage: {args.task_stage_id}")

    options = PolicyEvaluationListOptions(
        page_number=args.page,
        page_size=args.page_size,
    )

    try:
        pe_list = client.policy_evaluations.list(args.task_stage_id, options)

        print(f"Total policy evaluations: {pe_list.total_count}")
        print(f"Page {pe_list.current_page} of {pe_list.total_pages}")
        print()

        if not pe_list.items:
            print("No policy evaluations found for this task stage.")
        else:
            for pe in pe_list.items:
                print(f"- ID: {pe.id}")
                print(f"  Status: {pe.status}")
                print(f"  Policy Kind: {pe.policy_kind}")

                if pe.result_count:
                    print("  Result Count:")
                    if pe.result_count.passed is not None:
                        print(f"    - Passed: {pe.result_count.passed}")
                    if pe.result_count.advisory_failed is not None:
                        print(
                            f"    - Advisory Failed: {pe.result_count.advisory_failed}"
                        )
                    if pe.result_count.mandatory_failed is not None:
                        print(
                            f"    - Mandatory Failed: {pe.result_count.mandatory_failed}"
                        )
                    if pe.result_count.errored is not None:
                        print(f"    - Errored: {pe.result_count.errored}")

                if pe.status_timestamp:
                    print("  Status Timestamps:")
                    if pe.status_timestamp.passed_at:
                        print(f"    - Passed At: {pe.status_timestamp.passed_at}")
                    if pe.status_timestamp.failed_at:
                        print(f"    - Failed At: {pe.status_timestamp.failed_at}")
                    if pe.status_timestamp.running_at:
                        print(f"    - Running At: {pe.status_timestamp.running_at}")
                    if pe.status_timestamp.canceled_at:
                        print(f"    - Canceled At: {pe.status_timestamp.canceled_at}")
                    if pe.status_timestamp.errored_at:
                        print(f"    - Errored At: {pe.status_timestamp.errored_at}")

                if pe.task_stage:
                    print(f"  Task Stage: {pe.task_stage.id} ({pe.task_stage.type})")

                if pe.created_at:
                    print(f"  Created At: {pe.created_at}")
                if pe.updated_at:
                    print(f"  Updated At: {pe.updated_at}")

                print()

    except Exception as e:
        print(f"Error listing policy evaluations: {e}")
        return


if __name__ == "__main__":
    main()
