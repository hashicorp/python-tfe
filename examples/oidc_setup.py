#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Reference example: configure HCP Terraform OIDC federation across one
or more workspaces.

This is a worked example you can run as-is or adapt to your own
automation. It shows two distinct shapes of the same workflow:

  (A) Managed-IAM mode (default): the script provisions a per-workspace
      IAM role for you and points the workspace at it.

  (B) Bring-your-own-role mode (--use-existing-role <ARN>): the script
      makes no AWS API calls; it just sets the OIDC environment variables
      on each workspace pointing at the role ARN you already manage
      elsewhere (Terraform, CDK, Pulumi, console, ...).

Per workspace, the script:
  1. Reads the workspace (or creates it if --create-missing).
  2. In managed-IAM mode: ensures a workspace-scoped IAM role with a
     trust policy bound to that workspace's OIDC `sub` claim, and
     optionally attaches AWS-managed or inline permissions to it.
  3. Sets TFC_AWS_PROVIDER_AUTH=true and TFC_AWS_RUN_ROLE_ARN=<arn> on
     the workspace.
  4. Optionally removes any pre-existing static AWS_* credentials on the
     workspace (only with --remove-static-aws-creds).

In managed-IAM mode, the IAM OIDC provider for app.terraform.io is
account-global — one per AWS account — so it is created once and reused
on subsequent runs. Pass --skip-identity-provider to assume it already
exists. --use-existing-role implies that (no AWS calls happen at all).

Tokens (sensitive) come from environment variables:
    TFE_TOKEN                         (always)
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN                 (managed-IAM mode only)

Everything else is a CLI flag.

Examples:

    # Managed-IAM mode — script provisions the role.
    python examples/oidc_setup.py \\
        --cloud aws --org my-org \\
        --workspaces prod-app,staging-app \\
        --attach-managed-policy arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess

    # Bring-your-own-role — script only updates workspace env vars.
    python examples/oidc_setup.py \\
        --cloud aws --org my-org \\
        --workspaces prod-app,staging-app \\
        --use-existing-role arn:aws:iam::111122223333:role/my-tfc-role

Re-runs are idempotent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from pytfe import TFEClient
from pytfe.errors import TFEError
from pytfe.models import (
    CategoryType,
    VariableCreateOptions,
    Workspace,
    WorkspaceCreateOptions,
)

OIDC_PROVIDER_URL = "app.terraform.io"
OIDC_AUDIENCE = "aws.workload.identity"
STATIC_AWS_VARS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN")

# Placeholder thumbprint sent to AWS when creating the OIDC provider. AWS's
# `CreateOpenIDConnectProvider` accepts a `ThumbprintList` parameter that
# was historically expected to be the SHA1 hash of the provider's TLS
# certificate. Since July 2023 AWS no longer validates this value for
# providers backed by Amazon Trust Services CAs (which app.terraform.io
# is) — the cert chain is validated at runtime against the ATS root CAs.
# Any 40-char hex string is accepted in the field.
# See: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html
#
# Sending a placeholder removes the need for this script to make a TLS
# connection to app.terraform.io and SHA1-hash the leaf cert — both of
# which trip CodeQL's py/insecure-protocol and py/weak-sensitive-data-hashing
# rules even though neither is a security concern in this context.
OIDC_PROVIDER_THUMBPRINT_PLACEHOLDER = "0" * 40


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@dataclass
class Args:
    cloud: str
    org: str
    workspaces: list[str]
    aws_region: str
    role_name_template: str
    skip_identity_provider: bool
    create_missing: bool
    remove_static_aws_creds: bool
    use_existing_role: str | None = None
    attach_managed_policies: list[str] = field(default_factory=list)
    inline_policy_path: Path | None = None


def parse_args(argv: list[str] | None = None) -> Args:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--cloud",
        choices=("aws",),
        required=True,
        help="Cloud to set up. Only 'aws' is supported today; flag exists "
        "so azure/gcp/vault can be added later without breaking callers.",
    )
    p.add_argument(
        "--org",
        default=os.environ.get("TFE_ORG"),
        help="HCP Terraform organization (default: $TFE_ORG).",
    )
    p.add_argument(
        "--workspaces",
        required=True,
        help="Comma-separated workspace names. e.g. 'prod-app,staging-app,dev-app'.",
    )
    p.add_argument(
        "--aws-region",
        default="us-east-1",
        help="AWS region for the boto3 clients. The OIDC provider and IAM "
        "role are global so region mostly affects what the EC2/etc. role "
        "is used for in downstream Terraform code. (default: us-east-1)",
    )
    p.add_argument(
        "--role-name-template",
        default="tfc-{workspace}-oidc",
        help="Format string for the IAM role name; '{workspace}' is "
        "replaced with each workspace name. Must contain '{workspace}' "
        "(per-workspace roles are required for least-privilege isolation). "
        "(default: tfc-{workspace}-oidc)",
    )
    p.add_argument(
        "--skip-identity-provider",
        action="store_true",
        help="Don't create or check the IAM OIDC provider for "
        "app.terraform.io. Use this if you've already provisioned it via "
        "Terraform or another tool. By default the script idempotently "
        "creates it if missing and reuses it if present.",
    )
    p.add_argument(
        "--create-missing",
        action="store_true",
        help="Create the HCP workspace if it doesn't already exist. "
        "Default behaviour fails on a missing workspace so you don't "
        "accidentally provision new workspaces in production orgs.",
    )
    p.add_argument(
        "--remove-static-aws-creds",
        action="store_true",
        help="Remove any pre-existing AWS_ACCESS_KEY_ID / "
        "AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN environment variables "
        "on the workspace. This is the whole point of switching to OIDC; "
        "leaving them in place lets the AWS provider keep using the "
        "static creds instead of the OIDC token. Opt in explicitly to "
        "avoid surprising deletions.",
    )
    p.add_argument(
        "--attach-managed-policy",
        action="append",
        default=[],
        metavar="ARN",
        help="AWS-managed (or customer-managed) policy ARN to attach to "
        "each workspace's role. Repeatable. e.g. --attach-managed-policy "
        "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
    )
    p.add_argument(
        "--inline-policy",
        type=Path,
        default=None,
        metavar="FILE",
        help="Path to a JSON file containing an inline IAM policy "
        "document. The same policy is attached to every workspace's role "
        "under the name '<role>-inline'.",
    )
    p.add_argument(
        "--use-existing-role",
        default=None,
        metavar="ARN",
        help="Bring-your-own-role mode. Skip all IAM provisioning and set "
        "the provided role ARN as TFC_AWS_RUN_ROLE_ARN on every listed "
        "workspace. Use this when the OIDC provider, IAM role, trust "
        "policy and permissions are already managed elsewhere (e.g. by "
        "your own Terraform or CDK code). This flag implies "
        "--skip-identity-provider, disables --role-name-template, and is "
        "mutually exclusive with --attach-managed-policy and "
        "--inline-policy. AWS credentials are not required in the "
        "environment in this mode.",
    )

    ns = p.parse_args(argv)

    if not ns.org:
        p.error("--org is required (or set $TFE_ORG).")

    workspaces = [w.strip() for w in ns.workspaces.split(",") if w.strip()]
    if not workspaces:
        p.error("--workspaces must list at least one non-empty name.")

    if ns.use_existing_role:
        # Cheap shape check: catches typos without trying to be a full
        # ARN validator. Real validation happens server-side when the
        # workspace runs Terraform and tries to assume the role.
        if (
            not ns.use_existing_role.startswith("arn:")
            or ":role/" not in ns.use_existing_role
        ):
            p.error(
                f"--use-existing-role must be a full IAM role ARN "
                f"(arn:aws:iam::<acct>:role/<name>); got {ns.use_existing_role!r}"
            )
        if ns.attach_managed_policy or ns.inline_policy:
            p.error(
                "--use-existing-role is mutually exclusive with "
                "--attach-managed-policy / --inline-policy: the script "
                "doesn't manage permissions on roles it didn't create."
            )
    else:
        if "{workspace}" not in ns.role_name_template:
            p.error(
                "--role-name-template must contain the '{workspace}' placeholder "
                "(per-workspace IAM isolation). For a shared role across many "
                "workspaces, use --use-existing-role instead."
            )

    if ns.inline_policy and not ns.inline_policy.is_file():
        p.error(f"--inline-policy path not found: {ns.inline_policy}")

    return Args(
        cloud=ns.cloud,
        org=ns.org,
        workspaces=workspaces,
        aws_region=ns.aws_region,
        role_name_template=ns.role_name_template,
        skip_identity_provider=ns.skip_identity_provider,
        create_missing=ns.create_missing,
        remove_static_aws_creds=ns.remove_static_aws_creds,
        use_existing_role=ns.use_existing_role,
        attach_managed_policies=ns.attach_managed_policy,
        inline_policy_path=ns.inline_policy,
    )


# ---------------------------------------------------------------------------
# AWS helpers
# ---------------------------------------------------------------------------


def ensure_identity_provider(iam) -> tuple[str, bool]:
    """Return (OIDC provider ARN, was_created). Idempotent: reuses any
    existing provider for the same URL rather than recreating it.

    The IAM OIDC provider for app.terraform.io is an AWS-account-global
    resource — only one can exist per issuer URL per account — so on the
    second and subsequent script invocations this just returns the ARN
    of the already-existing provider.
    """
    expected_url = f"https://{OIDC_PROVIDER_URL}"
    for p in iam.list_open_id_connect_providers()["OpenIDConnectProviderList"]:
        d = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=p["Arn"])
        if f"https://{d['Url']}" == expected_url:
            return p["Arn"], False
    resp = iam.create_open_id_connect_provider(
        Url=expected_url,
        ClientIDList=[OIDC_AUDIENCE],
        ThumbprintList=[OIDC_PROVIDER_THUMBPRINT_PLACEHOLDER],
    )
    return resp["OpenIDConnectProviderArn"], True


def lookup_identity_provider_arn(iam) -> str:
    """Return the existing OIDC provider ARN; error if missing."""
    expected_url = f"https://{OIDC_PROVIDER_URL}"
    for p in iam.list_open_id_connect_providers()["OpenIDConnectProviderList"]:
        d = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=p["Arn"])
        if f"https://{d['Url']}" == expected_url:
            return p["Arn"]
    raise RuntimeError(
        f"No IAM OIDC provider found for {expected_url}. Either drop "
        "--skip-identity-provider so the script creates one, or "
        "provision it out of band first."
    )


def trust_policy_for(oidc_provider_arn: str, org: str, workspace_name: str) -> dict:
    """Trust policy that lets ONLY the named workspace assume the role."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": oidc_provider_arn},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{OIDC_PROVIDER_URL}:aud": OIDC_AUDIENCE,
                    },
                    "StringLike": {
                        # HCP issues sub as:
                        #   organization:<ORG>:project:<PROJECT>:workspace:<WS>:run_phase:<PHASE>
                        # Wildcard project + run_phase so plan/apply/refresh
                        # all work and the project slug doesn't have to be
                        # pinned. Workspace stays exact so this role is
                        # locked to one workspace only.
                        f"{OIDC_PROVIDER_URL}:sub": (
                            f"organization:{org}"
                            f":project:*"
                            f":workspace:{workspace_name}"
                            f":run_phase:*"
                        ),
                    },
                },
            }
        ],
    }


def ensure_role(
    iam,
    role_name: str,
    oidc_provider_arn: str,
    org: str,
    workspace_name: str,
) -> tuple[str, bool]:
    """Create or update the IAM role. Returns (arn, was_created)."""
    trust = trust_policy_for(oidc_provider_arn, org, workspace_name)
    try:
        existing = iam.get_role(RoleName=role_name)
        iam.update_assume_role_policy(
            RoleName=role_name, PolicyDocument=json.dumps(trust)
        )
        return existing["Role"]["Arn"], False
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise
    resp = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust),
        Description=(
            f"OIDC federation role for HCP Terraform workspace '{workspace_name}' "
            "- managed by pyTFE oidc_setup.py"
        ),
    )
    return resp["Role"]["Arn"], True


def sync_role_policies(
    iam, role_name: str, managed_arns: list[str], inline_doc: dict | None
) -> None:
    """Attach the requested managed policies and (optionally) write an inline policy.

    Existing policies that aren't in the requested set are left alone — the
    script doesn't aggressively detach things it didn't add, to avoid
    surprising removals on shared roles.
    """
    if managed_arns:
        attached = {
            p["PolicyArn"]
            for p in iam.list_attached_role_policies(RoleName=role_name)[
                "AttachedPolicies"
            ]
        }
        for arn in managed_arns:
            if arn not in attached:
                iam.attach_role_policy(RoleName=role_name, PolicyArn=arn)

    if inline_doc is not None:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-inline",
            PolicyDocument=json.dumps(inline_doc),
        )


# ---------------------------------------------------------------------------
# HCP helpers
# ---------------------------------------------------------------------------


def get_or_create_workspace(
    client: TFEClient, org: str, name: str, *, create_missing: bool
) -> Workspace:
    try:
        return client.workspaces.read(name, organization=org)
    except TFEError:
        if not create_missing:
            raise RuntimeError(
                f"workspace '{name}' not found in org '{org}'. "
                "Pass --create-missing to create it, or check the name."
            ) from None
        return client.workspaces.create(
            org, WorkspaceCreateOptions(name=name, auto_apply=False)
        )


def upsert_env_var(
    client: TFEClient, workspace_id: str, key: str, value: str, *, sensitive: bool
) -> str:
    """Replace if present, create if not. Returns 'created' or 'updated'."""
    for v in client.variables.list(workspace_id):
        if v.key == key:
            client.variables.delete(workspace_id, v.id)
            client.variables.create(
                workspace_id,
                VariableCreateOptions(
                    key=key,
                    value=value,
                    category=CategoryType.ENV,
                    sensitive=sensitive,
                ),
            )
            return "updated"
    client.variables.create(
        workspace_id,
        VariableCreateOptions(
            key=key, value=value, category=CategoryType.ENV, sensitive=sensitive
        ),
    )
    return "created"


def remove_static_aws_creds(client: TFEClient, workspace_id: str) -> list[str]:
    """Delete AWS_ACCESS_KEY_ID/SECRET/SESSION_TOKEN env vars. Returns removed keys."""
    removed = []
    for v in list(client.variables.list(workspace_id)):
        if v.category == CategoryType.ENV and v.key in STATIC_AWS_VARS and v.id:
            client.variables.delete(workspace_id, v.id)
            removed.append(v.key)
    return removed


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print(f"HCP org:         {args.org}")
    print(f"Workspaces:      {', '.join(args.workspaces)}")

    if args.use_existing_role:
        # Bring-your-own-role: skip every boto3 call.
        iam = None
        oidc_arn = None
        inline_doc = None
        print("Mode:            bring-your-own-role")
        print(f"Existing role:   {args.use_existing_role}")
        print()
    else:
        print("Mode:            managed-IAM")
        print(f"AWS region:      {args.aws_region}")
        print(f"Role template:   {args.role_name_template}")

        boto3.setup_default_session(region_name=args.aws_region)
        iam = boto3.client("iam")
        sts = boto3.client("sts")
        print(f"Caller identity: {sts.get_caller_identity()['Arn']}")
        print()

        if args.skip_identity_provider:
            oidc_arn = lookup_identity_provider_arn(iam)
            print(
                f"IDP: reusing existing OIDC provider (--skip-identity-provider): {oidc_arn}"
            )
        else:
            oidc_arn, idp_created = ensure_identity_provider(iam)
            if idp_created:
                print(
                    f"IDP: CREATED new OIDC provider for app.terraform.io: {oidc_arn}"
                )
            else:
                print(
                    f"IDP: reused existing OIDC provider for app.terraform.io: {oidc_arn}"
                )
        print()

        inline_doc = None
        if args.inline_policy_path:
            inline_doc = json.loads(args.inline_policy_path.read_text())
            print(f"Inline policy loaded from {args.inline_policy_path}")
            print()

    client = TFEClient()
    failures: list[tuple[str, str]] = []

    for ws_name in args.workspaces:
        print(f"--- {ws_name} ---")
        try:
            ws = get_or_create_workspace(
                client, args.org, ws_name, create_missing=args.create_missing
            )
            print(f"  workspace:      {ws.id}")

            if args.use_existing_role:
                role_arn = args.use_existing_role
                print(f"  IAM role:       {role_arn}  (external)")
            else:
                role_name = args.role_name_template.format(workspace=ws_name)
                # IAM names are limited to 64 chars.
                if len(role_name) > 64:
                    raise RuntimeError(
                        f"derived role name '{role_name}' is {len(role_name)} chars; "
                        "IAM limit is 64. Use a shorter --role-name-template."
                    )
                role_arn, created = ensure_role(
                    iam, role_name, oidc_arn, args.org, ws_name
                )
                action = "created" if created else "trust refreshed"
                print(f"  IAM role:       {role_arn}  ({action})")

                if args.attach_managed_policies or inline_doc is not None:
                    sync_role_policies(
                        iam, role_name, args.attach_managed_policies, inline_doc
                    )
                    for arn in args.attach_managed_policies:
                        print(f"    managed:      {arn}")
                    if inline_doc is not None:
                        print(f"    inline:       {role_name}-inline")
                else:
                    print(
                        "  WARNING: no policies attached. Role can be assumed but "
                        "has no AWS permissions. Pass --attach-managed-policy or "
                        "--inline-policy."
                    )

            for key, value, sensitive in [
                ("TFC_AWS_PROVIDER_AUTH", "true", False),
                ("TFC_AWS_RUN_ROLE_ARN", role_arn, True),
            ]:
                action = upsert_env_var(client, ws.id, key, value, sensitive=sensitive)
                shown = "(sensitive)" if sensitive else value
                print(f"  env var:        {key} = {shown}  ({action})")

            if args.remove_static_aws_creds:
                removed = remove_static_aws_creds(client, ws.id)
                if removed:
                    print(f"  removed static: {', '.join(removed)}")
                else:
                    print("  removed static: (none present)")

        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            failures.append((ws_name, str(exc)))
        print()

    # ---- Summary ----
    print("=" * 64)
    print(
        f"OIDC setup: {len(args.workspaces) - len(failures)} of "
        f"{len(args.workspaces)} workspace(s) succeeded"
    )
    if failures:
        for name, msg in failures:
            print(f"  FAILED  {name}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
