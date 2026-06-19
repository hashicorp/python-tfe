# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""HYOK (Hold Your Own Key) configurations demo for the python-tfe SDK.

Requires the HYOK entitlement on the organization, plus an existing agent pool
and OIDC configuration (see examples/oidc_configurations.py).
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    HYOKConfigurationCreateOptions,
    HYOKKMSOptions,
    OIDCConfigurationType,
)


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HYOK configurations demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    parser.add_argument("--create", action="store_true", help="Create a HYOK config")
    parser.add_argument("--name", help="Name for the new HYOK configuration")
    parser.add_argument("--kek-id", help="Key encryption key id in your KMS")
    parser.add_argument("--agent-pool-id", help="Agent pool ID (apool-xxxxx)")
    parser.add_argument("--oidc-configuration-id", help="OIDC config ID")
    parser.add_argument(
        "--oidc-type",
        choices=[t.value for t in OIDCConfigurationType],
        default=OIDCConfigurationType.VAULT.value,
        help="OIDC configuration JSON:API type",
    )
    parser.add_argument("--id", help="HYOK config ID for read/test/delete")
    parser.add_argument("--test", action="store_true", help="Test the config (--id)")
    parser.add_argument(
        "--revoke",
        action="store_true",
        help="Revoke the config (--id); required before delete",
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete the config (--id)"
    )
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    _print_header(f"HYOK configurations for {args.organization}")
    for h in client.hyok_configurations.list(args.organization):
        print(f"  - {h.id}  {h.name}  status={h.status}  primary={h.primary}")

    cfg_id = args.id
    if args.create:
        if not (
            args.name
            and args.kek_id
            and args.agent_pool_id
            and args.oidc_configuration_id
        ):
            print(
                "--create needs --name --kek-id --agent-pool-id --oidc-configuration-id"
            )
            return 2
        _print_header(f"Creating HYOK configuration: {args.name}")
        cfg = client.hyok_configurations.create(
            args.organization,
            HYOKConfigurationCreateOptions(
                name=args.name,
                kek_id=args.kek_id,
                agent_pool_id=args.agent_pool_id,
                oidc_configuration_id=args.oidc_configuration_id,
                oidc_configuration_type=OIDCConfigurationType(args.oidc_type),
                kms_options=HYOKKMSOptions(),
            ),
        )
        cfg_id = cfg.id
        print(f"  created {cfg.id} (status={cfg.status})")

    if args.id and not args.create:
        _print_header(f"Reading HYOK configuration: {args.id}")
        cfg = client.hyok_configurations.read(args.id)
        print(f"  name={cfg.name}  kek_id={cfg.kek_id}  status={cfg.status}")
        print(f"  oidc={cfg.oidc_configuration_id} ({cfg.oidc_configuration_type})")

    if args.test and cfg_id:
        _print_header(f"Testing HYOK configuration: {cfg_id}")
        client.hyok_configurations.test(cfg_id)
        print("  test triggered; poll read(...).status for the result")

    if args.revoke and cfg_id:
        _print_header(f"Revoking HYOK configuration: {cfg_id}")
        client.hyok_configurations.revoke(cfg_id)
        print("  revoke triggered; poll read(...).status until 'revoked'")

    if args.delete and cfg_id:
        # A HYOK configuration must be revoked before it can be deleted.
        _print_header(f"Deleting HYOK configuration: {cfg_id}")
        client.hyok_configurations.delete(cfg_id)
        print("  deleted")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
