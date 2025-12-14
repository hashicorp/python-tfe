from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import PolicyCheckListOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Policy Checks demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument(
        "--run-id", required=True, help="Run ID to list policy checks for"
    )
    parser.add_argument(
        "--policy-check-id", help="Specific policy check ID to read/override"
    )
    parser.add_argument(
        "--override", action="store_true", help="Override the specified policy check"
    )
    parser.add_argument(
        "--get-logs",
        action="store_true",
        help="Get logs for the specified policy check",
    )
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument is required")
        return

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List all policy checks for the given run
    _print_header(f"Listing policy checks for run: {args.run_id}")

    options = PolicyCheckListOptions(
        page_number=args.page,
        page_size=args.page_size,
    )

    try:
        pc_list = client.policy_checks.list(args.run_id, options)

        print(f"Total policy checks: {pc_list.total_count}")
        print(f"Page {pc_list.current_page} of {pc_list.total_pages}")
        print()

        if not pc_list.items:
            print("No policy checks found for this run.")
        else:
            for pc in pc_list.items:
                print(f"- ID: {pc.id}")
                print(f"Status: {pc.status}")
                print(f"Scope: {pc.scope}")
                if pc.result:
                    print(
                        f"Result: passed={pc.result.passed}, failed={pc.result.total_failed}"
                    )
                    print(f"Duration: {pc.result.duration}ms")
                if pc.actions:
                    print(f"Can Override: {pc.actions.is_overridable}")
                if pc.permissions:
                    print(f"Has Override Permission: {pc.permissions.can_override}")
                print()

    except Exception as e:
        print(f"Error listing policy checks: {e}")
        return

    # 2) Read a specific policy check (if policy-check-id is provided)
    if args.policy_check_id:
        _print_header(f"Reading policy check: {args.policy_check_id}")

        try:
            pc = client.policy_checks.read(args.policy_check_id)

            print(f"ID: {pc.id}")
            print(f"Status: {pc.status}")
            print(f"Scope: {pc.scope}")

            if pc.result:
                print("Result Summary:")
                print(f"- Passed: {pc.result.passed}")
                print(f"- Hard Failed: {pc.result.hard_failed}")
                print(f"- Soft Failed: {pc.result.soft_failed}")
                print(f"- Advisory Failed: {pc.result.advisory_failed}")
                print(f"- Total Failed: {pc.result.total_failed}")
                print(f"- Duration: {pc.result.duration}ms")
                print(f"- Overall Result: {pc.result.result}")

            if pc.actions:
                print("Actions:")
                print(f"- Is Overridable: {pc.actions.is_overridable}")

            if pc.permissions:
                print("Permissions:")
                print(f"- Can Override: {pc.permissions.can_override}")

            if pc.status_timestamps:
                print("Status Timestamps:")
                if pc.status_timestamps.queued_at:
                    print(f"- Queued At: {pc.status_timestamps.queued_at}")
                if pc.status_timestamps.passed_at:
                    print(f"- Passed At: {pc.status_timestamps.passed_at}")
                if pc.status_timestamps.soft_failed_at:
                    print(f"- Soft Failed At: {pc.status_timestamps.soft_failed_at}")
                if pc.status_timestamps.hard_failed_at:
                    print(f"- Hard Failed At: {pc.status_timestamps.hard_failed_at}")
                if pc.status_timestamps.errored_at:
                    print(f"- Errored At: {pc.status_timestamps.errored_at}")

        except Exception as e:
            print(f"Error reading policy check: {e}")
            return

        # 3) Override the policy check (if requested and possible)
        if args.override:
            _print_header(f"Overriding policy check: {args.policy_check_id}")

            try:
                overridden_pc = client.policy_checks.override(args.policy_check_id)
                print(f"Policy check {overridden_pc.id} successfully overridden!")
                print(f"New status: {overridden_pc.status}")

            except Exception as e:
                print(f"Error overriding policy check: {e}")

        # 4) Get logs for the policy check (if requested)
        if args.get_logs:
            _print_header(f"Getting logs for policy check: {args.policy_check_id}")

            try:
                print(
                    "Fetching logs (this may take a moment if the policy check is still running)..."
                )
                logs = client.policy_checks.logs(args.policy_check_id)

                print("Policy Check Logs:")
                print("-" * 60)
                print(logs)
                print("-" * 60)

            except Exception as e:
                print(f"Error getting policy check logs: {e}")


if __name__ == "__main__":
    main()
