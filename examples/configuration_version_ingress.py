#!/usr/bin/env python3
"""Configuration-version VCS ingress attributes example.

Demonstrates ``client.configuration_versions.ingress_attributes(cv_id)``,
which returns the VCS metadata (branch / commit / PR) for a CV that was
created from a VCS connection.  Returns ``None`` for API-driven CVs.

Usage::

    TFE_TOKEN=... python examples/configuration_version_ingress.py \\
        --cv-id cv-XXXX
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--cv-id", required=True)
    args = p.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    cv = client.configuration_versions.read(args.cv_id)
    print(f"configuration version: {cv.id}  source={cv.source}  status={cv.status}")

    ingress = client.configuration_versions.ingress_attributes(args.cv_id)
    if ingress is None:
        print(
            "no ingress attributes — this configuration version was not "
            "created from a VCS connection."
        )
        return 0

    print("ingress attributes:")
    for field in (
        "branch",
        "clone_url",
        "commit_message",
        "commit_sha",
        "commit_url",
        "compare_url",
        "identifier",
        "is_pull_request",
        "on_default_branch",
        "pull_request_number",
        "pull_request_url",
        "pull_request_title",
        "tag",
        "sender_username",
    ):
        value = getattr(ingress, field, None)
        if value is not None:
            print(f"  {field:<22}: {value}")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
