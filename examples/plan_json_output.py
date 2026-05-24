#!/usr/bin/env python3
"""Plan JSON-output example.

Demonstrates four plan endpoints that work directly off a run id, so
callers do not have to ``runs.read`` first just to discover the plan id::

    client.plans.read(plan_id)
    client.plans.read_for_run(run_id)
    client.plans.read_json_output(plan_id)
    client.plans.read_json_output_for_run(run_id)
    client.plans.read_json_schema_for_run(run_id)

The ``json-output`` endpoints respond with HTTP 307 redirects to
presigned object-storage URLs; the SDK follows them without forwarding
the TFE bearer token.

Usage (either form)::

    TFE_TOKEN=... python examples/plan_json_output.py --plan-id plan-XXXX
    TFE_TOKEN=... python examples/plan_json_output.py --run-id  run-XXXX
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
    p.add_argument("--plan-id")
    p.add_argument("--run-id")
    p.add_argument(
        "--save-json", help="Write the JSON plan to this file instead of stdout"
    )
    args = p.parse_args()
    if not args.token:
        print("TFE_TOKEN is not set")
        return 2
    if not args.plan_id and not args.run_id:
        print("provide --plan-id and/or --run-id")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    if args.plan_id:
        _header(f"plans.read({args.plan_id})")
        plan = client.plans.read(args.plan_id)
        print(
            f"  status={plan.status} has_changes={plan.has_changes} "
            f"add={plan.resource_additions} change={plan.resource_changes} "
            f"destroy={plan.resource_destructions}"
        )

        _header(f"plans.read_json_output({args.plan_id})")
        out = client.plans.read_json_output(args.plan_id)
        print(
            f"  json keys: {sorted(out.keys())[:8]}... "
            f"(total {len(out)} top-level keys)"
        )

    if args.run_id:
        _header(f"plans.read_for_run({args.run_id})")
        plan = client.plans.read_for_run(args.run_id)
        print(
            f"  id={plan.id} status={plan.status} has_changes={plan.has_changes}"
        )

        _header(f"plans.read_json_output_for_run({args.run_id})")
        out = client.plans.read_json_output_for_run(args.run_id)
        print(
            f"  json keys: {sorted(out.keys())[:8]}... "
            f"(total {len(out)} top-level keys)"
        )

        _header(f"plans.read_json_schema_for_run({args.run_id})")
        schema = client.plans.read_json_schema_for_run(args.run_id)
        if isinstance(schema, dict):
            print(f"  schema keys: {sorted(schema.keys())[:8]}")
        else:
            print(f"  schema: {type(schema).__name__}")

        if args.save_json:
            import json as _json

            with open(args.save_json, "w") as f:
                _json.dump(out, f, indent=2)
            print(f"\nwrote {args.save_json}")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
