# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import CommentCreateOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Comments demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--run-id", required=True, help="Run ID (e.g. run-xxxxx)")
    parser.add_argument("--create", action="store_true", help="Create a new comment")
    parser.add_argument("--body", help="Comment body text (required with --create)")
    parser.add_argument("--read", action="store_true", help="Read a specific comment")
    parser.add_argument("--id", help="Comment ID (e.g. com-xxxxx), required for --read")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Always list existing comments for the run
    _print_header(f"Listing comments for run: {args.run_id}")
    comment_count = 0
    for comment in client.comments.list(run_id=args.run_id):
        comment_count += 1
        print(f"- ID: {comment.id}")
        print(f"  Body: {comment.body}")
        print()

    if comment_count == 0:
        print("No comments found.")
    else:
        print(f"Total: {comment_count} comments")

    # 2) Create a new comment
    if args.create:
        if not args.body:
            print("--body is required for --create")
        else:
            _print_header(f"Creating a comment on run: {args.run_id}")
            opts = CommentCreateOptions(body=args.body)
            comment = client.comments.create(run_id=args.run_id, options=opts)
            print(f"Created comment: {comment.id}")
            print(f"  Body: {comment.body}")

    # 3) Read a specific comment
    if args.read:
        if not args.id:
            print("--id is required for --read")
        else:
            _print_header(f"Reading comment: {args.id}")
            comment = client.comments.read(comment_id=args.id)
            print(f"ID: {comment.id}")
            print(f"Body: {comment.body}")


if __name__ == "__main__":
    main()
