# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import TeamTokenCreateOptions, TeamTokenListOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_token(token):
    print(f"- ID: {token.id}")
    if token.description:
        print(f"  Description: {token.description}")
    print(f"  Created At: {token.created_at}")
    print(f"  Last Used At: {token.last_used_at}")
    print(f"  Expired At: {token.expired_at}")
    if token.team:
        print(f"  Team ID: {token.team.id}")
    if token.created_by:
        if token.created_by.user:
            print(f"  Created By (user): {token.created_by.user.id}")
        elif token.created_by.team:
            print(f"  Created By (team): {token.created_by.team.id}")
        elif token.created_by.organization:
            print(f"  Created By (org): {token.created_by.organization.id}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Team Tokens demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", required=True, help="Organization name")
    parser.add_argument("--team-id", help="Team ID (e.g. team-xxxxx)")
    parser.add_argument("--create", action="store_true", help="Create a team token")
    parser.add_argument(
        "--description", help="Token description (creates a named multi-token)"
    )
    parser.add_argument(
        "--expired-at",
        help="Expiry datetime in ISO 8601 (e.g. 2026-12-31T00:00:00Z)",
    )
    parser.add_argument(
        "--read", action="store_true", help="Read the legacy token for --team-id"
    )
    parser.add_argument(
        "--read-by-id", action="store_true", help="Read a token by --token-id"
    )
    parser.add_argument("--token-id", help="Token ID (e.g. at-xxxxx)")
    parser.add_argument(
        "--delete", action="store_true", help="Delete the legacy token for --team-id"
    )
    parser.add_argument(
        "--delete-by-id",
        action="store_true",
        help="Delete a token by --token-id",
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) Always list tokens for the organization
    _print_header(f"Listing team tokens for organization: {args.organization}")
    list_opts = TeamTokenListOptions()
    token_count = 0
    for t in client.team_tokens.list(organization=args.organization, options=list_opts):
        token_count += 1
        _print_token(t)

    if token_count == 0:
        print("No team tokens found.")
    else:
        print(f"Total: {token_count} team tokens")

    # 2) Create a team token
    if args.create:
        if not args.team_id:
            print("--team-id is required for --create")
        else:
            from datetime import datetime

            if args.description or args.expired_at:
                _print_header(f"Creating named team token for team: {args.team_id}")
                create_opts = TeamTokenCreateOptions(
                    description=args.description,
                    expired_at=datetime.fromisoformat(args.expired_at)
                    if args.expired_at
                    else None,
                )
                t = client.team_tokens.create_with_options(
                    team_id=args.team_id, options=create_opts
                )
            else:
                _print_header(
                    f"Creating legacy team token for team: {args.team_id}"
                )
                t = client.team_tokens.create(team_id=args.team_id)
            print("Created team token:")
            _print_token(t)

    # 3) Read legacy token by team ID
    if args.read:
        if not args.team_id:
            print("--team-id is required for --read")
        else:
            _print_header(f"Reading legacy token for team: {args.team_id}")
            t = client.team_tokens.read(team_id=args.team_id)
            _print_token(t)

    # 4) Read token by token ID
    if args.read_by_id:
        if not args.token_id:
            print("--token-id is required for --read-by-id")
        else:
            _print_header(f"Reading token by ID: {args.token_id}")
            t = client.team_tokens.read_by_id(token_id=args.token_id)
            _print_token(t)

    # 5) Delete legacy token by team ID
    if args.delete:
        if not args.team_id:
            print("--team-id is required for --delete")
        else:
            _print_header(f"Deleting legacy token for team: {args.team_id}")
            client.team_tokens.delete(team_id=args.team_id)
            print("Deleted.")

    # 6) Delete token by token ID
    if args.delete_by_id:
        if not args.token_id:
            print("--token-id is required for --delete-by-id")
        else:
            _print_header(f"Deleting token by ID: {args.token_id}")
            client.team_tokens.delete_by_id(token_id=args.token_id)
            print("Deleted.")


if __name__ == "__main__":
    main()
