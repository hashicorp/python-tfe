# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Public Terraform Registry (module API) demo for the python-tfe SDK.

The public registry (registry.terraform.io) is unauthenticated, so this example
does not need a token. Use ``--base-url`` to target another registry.
"""

from __future__ import annotations

import argparse
import itertools
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import PublicRegistrySearchOptions
from pytfe.resources.registry import Registry


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Public Terraform Registry demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--base-url", default=None, help="Registry base URL override")
    parser.add_argument("--search", help="Search modules by keyword")
    parser.add_argument(
        "--namespace", default="terraform-aws-modules", help="Module namespace"
    )
    parser.add_argument("--name", default="vpc", help="Module name")
    parser.add_argument("--provider", default="aws", help="Module provider")
    parser.add_argument("--limit", type=int, default=5, help="Max rows to print")
    args = parser.parse_args()

    client = TFEClient(TFEConfig(address=args.address, token=args.token))
    registry = (
        Registry(client._transport, base_url=args.base_url)
        if args.base_url
        else client.registry
    )

    if args.search:
        _print_header(f"Searching modules for: {args.search}")
        opts = PublicRegistrySearchOptions(provider=args.provider)
        for m in itertools.islice(
            registry.search_modules(args.search, opts), args.limit
        ):
            print(f"  {m.id:50}  downloads={m.downloads}  verified={m.verified}")
        return 0

    _print_header(f"Latest: {args.namespace}/{args.name}/{args.provider}")
    module = registry.latest_for_provider(args.namespace, args.name, args.provider)
    print(f"  id:          {module.id}")
    print(f"  description: {module.description}")
    print(f"  source:      {module.source}")
    print(f"  inputs:      {len(module.root.inputs or []) if module.root else 0}")
    print(f"  providers:   {module.providers}")

    _print_header("Available versions")
    versions = registry.list_versions(args.namespace, args.name, args.provider)
    vlist = [v.version for v in versions.versions]
    sample = f"{vlist[0]} … {vlist[-1]}" if vlist else "n/a"
    print(f"  {len(vlist)} versions (range: {sample}); current: {module.version}")

    _print_header("Download source (X-Terraform-Get)")
    print(f"  {registry.latest_download_url(args.namespace, args.name, args.provider)}")

    _print_header("Download metrics")
    summary = registry.downloads_summary(args.namespace, args.name, args.provider)
    print(
        f"  week={summary.week} month={summary.month} "
        f"year={summary.year} total={summary.total}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
