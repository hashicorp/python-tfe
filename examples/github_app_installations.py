#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Reference example: list and read HCP Terraform GitHub App installations.

The GitHub App authorisation flow itself happens through the HCP
Terraform UI (https://app.terraform.io -> settings -> GitHub Apps).
This SDK only exposes the lookup endpoints, which you use to discover
the ``github-app-installation-id`` value that workspace, stack, and
registry-module VCS configuration takes.

Environment:

    TFE_TOKEN     user token (read-only is fine)
    TFE_ADDRESS   HCP Terraform / Terraform Enterprise URL

    Optional:
    GITHUB_APP_FILTER_NAME             filter[name] passed to list
    GITHUB_APP_FILTER_INSTALLATION_ID  filter[installation_id] passed to list
    GITHUB_APP_READ_ID                 if set, also do a single read on
                                       this HCP-side installation ID
                                       (e.g. ghain-...)
"""

from __future__ import annotations

import os
import sys

from pytfe import TFEClient
from pytfe.errors import TFEError
from pytfe.models import GitHubAppInstallationListOptions


def main() -> int:
    client = TFEClient()

    name_filter = os.environ.get("GITHUB_APP_FILTER_NAME")
    install_id_filter = os.environ.get("GITHUB_APP_FILTER_INSTALLATION_ID")
    read_id = os.environ.get("GITHUB_APP_READ_ID")

    list_options = None
    if name_filter or install_id_filter:
        list_options = GitHubAppInstallationListOptions(
            name=name_filter,
            installation_id=int(install_id_filter) if install_id_filter else None,
        )

    print("=== GitHub App installations visible to this token ===")
    try:
        installations = list(client.github_app_installations.list(list_options))
    except TFEError as exc:
        print(f"\nlist failed: {exc}")
        return 1

    if not installations:
        print(
            "  (none)  — either this token can't see any installations, "
            "or the supplied filters matched nothing."
        )
    else:
        for inst in installations:
            print(
                f"  {inst.id}  github_installation_id={inst.installation_id}  "
                f"type={inst.installation_type}  name={inst.name!r}  url={inst.installation_url}"
            )

    if read_id:
        print()
        print(f"=== Reading single installation: {read_id} ===")
        try:
            inst = client.github_app_installations.read(read_id)
        except TFEError as exc:
            print(f"  read failed: {exc}")
            return 1
        print(f"  id:                {inst.id}")
        print(f"  name:              {inst.name}")
        print(f"  installation_id:   {inst.installation_id}  (GitHub-side numeric)")
        print(f"  installation_type: {inst.installation_type}")
        print(f"  installation_url:  {inst.installation_url}")
        print(f"  icon_url:          {inst.icon_url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
