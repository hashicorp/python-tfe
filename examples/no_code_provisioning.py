#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Example: HCP Terraform no-code provisioning.

Walks through the four phases of the no-code lifecycle:

1. Enable a registry module for no-code use, with allowed variable values.
2. Read variables declared by the module version (used for form-building).
3. Create a workspace from the no-code module on behalf of an end user.
4. Upgrade the workspace to a newer module version.

Environment variables:

    TFE_TOKEN              user or team token (not an org token)
    TFE_ADDRESS            HCP Terraform / Terraform Enterprise URL
    TFE_ORG                organization name
    TFE_REGISTRY_MODULE_ID registry module ID to enable
    TFE_PROJECT_ID         project to create workspaces in
    TFE_MODULE_VERSION     initial module version (default: latest)
    TFE_NEXT_MODULE_VERSION upgrade target version (optional; skips upgrade if unset)

The script creates one workspace and (optionally) upgrades it. It does NOT
delete the workspace or the no-code module by default — uncomment the
cleanup block at the end if you want it to.
"""

from __future__ import annotations

import os
import sys
import time

from pytfe.client import TFEClient
from pytfe.errors import TFEError
from pytfe.models import (
    CategoryType,
    NoCodeModuleCreateOptions,
    NoCodeModuleIncludeOpt,
    NoCodeModuleReadOptions,
    NoCodeModuleUpdateOptions,
    NoCodeVariableOption,
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceUpgradeOptions,
    NoCodeWorkspaceVariable,
)

TERMINAL_UPGRADE_STATES = {"planned_and_finished", "errored", "canceled"}


def main() -> int:
    organization = os.environ["TFE_ORG"]
    registry_module_id = os.environ["TFE_REGISTRY_MODULE_ID"]
    project_id = os.environ["TFE_PROJECT_ID"]
    module_version = os.environ.get("TFE_MODULE_VERSION")
    next_version = os.environ.get("TFE_NEXT_MODULE_VERSION")

    client = TFEClient()

    print("=== pyTFE No-Code Provisioning Example ===\n")

    # 1. Enable no-code provisioning on a registry module with allowed values.
    print(f"1. Enabling no-code on registry module {registry_module_id}...")
    no_code_module = client.no_code_modules.create(
        organization,
        NoCodeModuleCreateOptions(
            registry_module_id=registry_module_id,
            enabled=True,
            version_pin=module_version,
            variable_options=[
                NoCodeVariableOption(
                    variable_name="region",
                    variable_type="string",
                    options=["us-east-1", "us-west-2", "eu-west-1"],
                ),
            ],
        ),
    )
    print(f"   no-code module id: {no_code_module.id}")
    print(f"   version pin:       {no_code_module.version_pin}")

    # Re-read with include to confirm variable options round-trip.
    refreshed = client.no_code_modules.read(
        no_code_module.id,
        NoCodeModuleReadOptions(
            include=[NoCodeModuleIncludeOpt.VARIABLE_OPTIONS]
        ),
    )
    for option in refreshed.variable_options:
        print(
            "   variable option:",
            option.variable_name,
            "->",
            option.options,
        )

    # 2. Introspect variables for the pinned version.
    if module_version:
        print(f"\n2. Reading variables for version {module_version}...")
        try:
            for var in client.no_code_modules.read_variables(
                no_code_module.id, module_version
            ):
                req = "required" if var.required else "optional"
                print(f"   - {var.name} ({var.type}) [{req}]")
        except TFEError as exc:
            print(f"   could not read variables: {exc}")
    else:
        print("\n2. Skipping variable introspection — TFE_MODULE_VERSION not set.")

    # 3. Create a workspace from the no-code module.
    print("\n3. Creating a workspace from the no-code module...")
    workspace_name = f"pytfe-no-code-{int(time.time())}"
    workspace = client.no_code_modules.create_workspace(
        no_code_module.id,
        NoCodeWorkspaceCreateOptions(
            name=workspace_name,
            project_id=project_id,
            description="Created by pyTFE no-code example",
            vars=[
                NoCodeWorkspaceVariable(
                    key="region",
                    value="us-east-1",
                    category=CategoryType.TERRAFORM,
                ),
            ],
        ),
    )
    print(f"   workspace id:   {workspace.id}")
    print(f"   workspace name: {workspace.name}")
    print(f"   execution mode: {workspace.execution_mode}")

    # 4. Optional: upgrade to a newer version.
    if next_version:
        print(f"\n4. Upgrading workspace to module version {next_version}...")
        client.no_code_modules.update(
            no_code_module.id,
            NoCodeModuleUpdateOptions(version_pin=next_version),
        )
        upgrade = client.no_code_modules.upgrade_workspace(
            no_code_module.id,
            workspace.id,
            NoCodeWorkspaceUpgradeOptions(),
        )
        print(f"   upgrade id: {upgrade.id}")

        while True:
            status = client.no_code_modules.read_workspace_upgrade(
                no_code_module.id, workspace.id, upgrade.id
            )
            print(f"   upgrade status: {status.status}")
            if status.status in TERMINAL_UPGRADE_STATES:
                break
            time.sleep(5)

        if status.status == "planned_and_finished":
            client.no_code_modules.confirm_workspace_upgrade(
                no_code_module.id, workspace.id, upgrade.id
            )
            print("   upgrade applied.")
        else:
            print(f"   upgrade did not complete cleanly (status={status.status}).")
    else:
        print("\n4. Skipping upgrade — TFE_NEXT_MODULE_VERSION not set.")

    print("\nDone.")
    print(
        "Workspace and no-code module were NOT deleted. "
        "Delete them via client.workspaces.delete_by_id(...) "
        "and client.no_code_modules.delete(...) when finished."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
