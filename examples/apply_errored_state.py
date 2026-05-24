#!/usr/bin/env python3
"""Apply errored-state recovery example.

Demonstrates ``client.applies.errored_state(apply_id)``, which fetches
the raw state bytes that were uploaded but never committed because the
apply failed.  The TFE endpoint returns a 307 redirect to a presigned
object-storage URL; the SDK follows the redirect without forwarding the
TFE bearer token.

If the apply did not have a failed state upload, the API returns 404
(``NotFound``).

Usage::

    TFE_TOKEN=... python examples/apply_errored_state.py --apply-id apply-XXXX
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.errors import NotFound


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--apply-id", required=True)
    p.add_argument("--out", help="Write the recovered state bytes to this file")
    args = p.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    print(f"reading apply {args.apply_id} ...")
    apply = client.applies.read(args.apply_id)
    print(f"  status: {apply.status}")

    print("fetching errored state ...")
    try:
        data = client.applies.errored_state(args.apply_id)
    except NotFound:
        print("no errored state available for this apply (apply did not fail "
              "during state upload, or storage retention has elapsed).")
        return 0

    print(f"recovered {len(data)} bytes of errored state")
    if args.out:
        with open(args.out, "wb") as f:
            f.write(data)
        print(f"wrote {args.out}")
    else:
        # Show a small preview
        preview = data[:256].decode("utf-8", errors="replace")
        print(f"--- preview ---\n{preview}\n--- end preview ---")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
