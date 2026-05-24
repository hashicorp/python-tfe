#!/usr/bin/env python3
"""Policy set project-exclusions example.

Demonstrates::

    client.policy_sets.add_project_exclusions(policy_set_id, options)
    client.policy_sets.remove_project_exclusions(policy_set_id, options)

By default this script creates a scratch policy set and a scratch project,
adds the project to the policy set's exclusion list, removes it again,
then cleans up.  Provide ``--policy-set-id`` and ``--project-id`` to act
on existing resources instead.

Usage::

    TFE_TOKEN=... TFE_ORG=prab-sandbox02 \\
        python examples/policy_set_project_exclusions.py
"""

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    PolicySetAddProjectExclusionsOptions,
    PolicySetCreateOptions,
    PolicySetRemoveProjectExclusionsOptions,
    Project,
    ProjectCreateOptions,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    p.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    p.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    p.add_argument("--policy-set-id")
    p.add_argument("--project-id")
    args = p.parse_args()

    if not args.token or not args.organization:
        print("set TFE_TOKEN and TFE_ORG")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    created: dict[str, str] = {}
    try:
        ps_id = args.policy_set_id
        proj_id = args.project_id

        if not ps_id:
            stamp = int(time.time())
            # Exclusions require a *global* policy set.
            ps = client.policy_sets.create(
                args.organization,
                PolicySetCreateOptions(name=f"pytfe-pe-{stamp}", Global=True),
            )
            created["policy_set"] = ps.id
            ps_id = ps.id
            print(f"created policy set: {ps.id} ({ps.name}, global=True)")

        if not proj_id:
            stamp = int(time.time())
            proj = client.projects.create(
                args.organization,
                ProjectCreateOptions(name=f"pytfe-pe-proj-{stamp}"),
            )
            created["project"] = proj.id
            proj_id = proj.id
            print(f"created project:    {proj.id} ({proj.name})")

        print(f"\nadding project {proj_id} to exclusions of {ps_id}")
        client.policy_sets.add_project_exclusions(
            ps_id,
            PolicySetAddProjectExclusionsOptions(
                project_exclusions=[Project(id=proj_id)]
            ),
        )
        print("added")

        # Confirm via the canonical read with include
        from pytfe.models import PolicySetReadOptions, PolicySetIncludeOpt

        ps_after = client.policy_sets.read_with_options(
            ps_id,
            PolicySetReadOptions(
                include=[PolicySetIncludeOpt.POLICY_SET_PROJECT_EXCLUSIONS]
            ),
        )
        excluded_ids = [p.id for p in (ps_after.project_exclusions or [])]
        print(f"current excluded projects: {excluded_ids}")
        assert proj_id in excluded_ids, "project not in exclusions"

        print(f"\nremoving project {proj_id} from exclusions")
        client.policy_sets.remove_project_exclusions(
            ps_id,
            PolicySetRemoveProjectExclusionsOptions(
                project_exclusions=[Project(id=proj_id)]
            ),
        )
        print("removed")

        ps_final = client.policy_sets.read_with_options(
            ps_id,
            PolicySetReadOptions(
                include=[PolicySetIncludeOpt.POLICY_SET_PROJECT_EXCLUSIONS]
            ),
        )
        excluded_ids = [p.id for p in (ps_final.project_exclusions or [])]
        print(f"final excluded projects:   {excluded_ids}")
        return 0
    finally:
        if "project" in created:
            try:
                client.projects.delete(created["project"])
                print(f"cleaned up project {created['project']}")
            except Exception as e:
                print(f"WARN: could not clean up project: {e}")
        if "policy_set" in created:
            try:
                client.policy_sets.delete(created["policy_set"])
                print(f"cleaned up policy set {created['policy_set']}")
            except Exception as e:
                print(f"WARN: could not clean up policy set: {e}")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
