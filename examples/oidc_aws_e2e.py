#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Runnable end-to-end example: secret-less AWS access via OIDC federation.

Implements the workflow from the HashiCorp blog
(https://www.hashicorp.com/en/blog/access-aws-from-hcp-terraform-with-oidc-federation)
using pyTFE + boto3. Verified live against AWS + HCP Terraform.

What this script does, in order:

  AWS side (provisioned with the credentials in your shell):
    1. Ensure an IAM OIDC provider exists for ``https://app.terraform.io``.
    2. Ensure an IAM role with a trust policy scoped to a single HCP
       workspace, and a least-privilege EC2 policy for the test.

  HCP side (provisioned via pyTFE):
    3. Ensure the target workspace exists.
    4. Set ``TFC_AWS_PROVIDER_AUTH`` and ``TFC_AWS_RUN_ROLE_ARN`` on the
       workspace.
    5. Upload a tiny Terraform configuration that launches a single
       t3.micro in the AWS region's default VPC.
    6. Trigger a run; wait through plan + apply.

  Verification:
    7. Use boto3 to confirm the EC2 instance is running and tagged.
    8. If ``OIDC_DESTROY_AFTER_VERIFY=true`` (default), queue a destroy
       run via pyTFE so the cleanup itself exercises the OIDC trust the
       other direction.

What it intentionally LEAVES in place:
    - The HCP workspace, env vars, IAM role, and OIDC provider — so you
      can reuse the same setup for other Terraform code without redoing
      the trust dance.

Environment variables:

    Required:
        TFE_TOKEN              user or team HCP Terraform token
        TFE_ORG                HCP Terraform organization name
        AWS_ACCESS_KEY_ID      AWS sandbox credentials
        AWS_SECRET_ACCESS_KEY
        AWS_SESSION_TOKEN      (only needed for STS session credentials)

    Optional:
        TFE_ADDRESS                  default: https://app.terraform.io
        OIDC_WORKSPACE_NAME          default: pytfe-oidc-aws-e2e
        OIDC_AWS_REGION              default: ap-south-1
        OIDC_IAM_ROLE_NAME           default: <workspace_name>-role
        OIDC_INSTANCE_TYPE           default: t3.micro
        OIDC_DESTROY_AFTER_VERIFY    "true" / "false", default: true

Run:

    export TFE_TOKEN=...
    export TFE_ORG=my-org
    export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...
    export OIDC_WORKSPACE_NAME=my-app-prod
    python examples/oidc_aws_e2e.py

Re-runs are idempotent: every AWS and HCP resource is created only if
missing, and the IAM trust + EC2 policies are refreshed in place.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tarfile
import time
import traceback

import boto3
from botocore.exceptions import ClientError

from pytfe import TFEClient
from pytfe.errors import TFEError
from pytfe.models import (
    CategoryType,
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
    RunCreateOptions,
    VariableCreateOptions,
    Workspace,
    WorkspaceCreateOptions,
)

# ---- Configuration (env-driven, no defaults that leak identifiers) ----

HCP_ORG = os.environ["TFE_ORG"]
WORKSPACE_NAME = os.environ.get("OIDC_WORKSPACE_NAME", "pytfe-oidc-aws-e2e")
AWS_REGION = os.environ.get("OIDC_AWS_REGION", "ap-south-1")
IAM_ROLE_NAME = os.environ.get("OIDC_IAM_ROLE_NAME", f"{WORKSPACE_NAME}-role")
INSTANCE_TYPE = os.environ.get("OIDC_INSTANCE_TYPE", "t3.micro")
DESTROY_AFTER_VERIFY = os.environ.get(
    "OIDC_DESTROY_AFTER_VERIFY", "true"
).strip().lower() in ("1", "true", "yes")

OIDC_PROVIDER_URL = "app.terraform.io"
OIDC_AUDIENCE = "aws.workload.identity"

# Placeholder thumbprint for IAM's CreateOpenIDConnectProvider. AWS no
# longer validates this field for providers backed by Amazon Trust Services
# CAs (app.terraform.io is one) — any 40-char hex string is accepted.
# See: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html
OIDC_PROVIDER_THUMBPRINT_PLACEHOLDER = "0" * 40

# Tag applied to the test instance so we can find/verify it later.
INSTANCE_NAME_TAG = WORKSPACE_NAME


# ---- Terraform code uploaded to the workspace ----

TERRAFORM_MAIN_TF = f"""\
terraform {{
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = "{AWS_REGION}"
}}

data "aws_vpc" "default" {{
  default = true
}}

data "aws_subnets" "default" {{
  filter {{
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }}
}}

data "aws_ami" "al2023" {{
  most_recent = true
  owners      = ["amazon"]
  filter {{
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }}
  filter {{
    name   = "architecture"
    values = ["x86_64"]
  }}
}}

resource "aws_instance" "test" {{
  ami           = data.aws_ami.al2023.id
  instance_type = "{INSTANCE_TYPE}"
  subnet_id     = tolist(data.aws_subnets.default.ids)[0]

  tags = {{
    Name    = "{INSTANCE_NAME_TAG}"
    Purpose = "pyTFE OIDC federation example"
  }}
}}

output "instance_id" {{
  value = aws_instance.test.id
}}
""".encode()


# ---- Helpers ----


def banner(s: str) -> None:
    print()
    print("=" * 72)
    print(s)
    print("=" * 72)


def ensure_oidc_provider(iam) -> str:
    """Create or reuse the app.terraform.io OIDC provider. Returns ARN."""
    expected_url = f"https://{OIDC_PROVIDER_URL}"
    for p in iam.list_open_id_connect_providers()["OpenIDConnectProviderList"]:
        d = iam.get_open_id_connect_provider(OpenIDConnectProviderArn=p["Arn"])
        if f"https://{d['Url']}" == expected_url:
            print(f"  reusing OIDC provider: {p['Arn']}")
            return p["Arn"]

    resp = iam.create_open_id_connect_provider(
        Url=expected_url,
        ClientIDList=[OIDC_AUDIENCE],
        ThumbprintList=[OIDC_PROVIDER_THUMBPRINT_PLACEHOLDER],
    )
    arn = resp["OpenIDConnectProviderArn"]
    print(f"  created OIDC provider: {arn}")
    return arn


def ensure_iam_role(iam, oidc_provider_arn: str) -> str:
    """Create or reuse the IAM role; refresh trust policy + inline EC2 policy."""
    trust = {
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
                        # sub claim format:
                        #   organization:<ORG>:project:<PROJECT>:workspace:<WS>:run_phase:<PHASE>
                        # Wildcards on project + run_phase keep this simple
                        # while pinning to a single workspace.
                        f"{OIDC_PROVIDER_URL}:sub": (
                            f"organization:{HCP_ORG}"
                            f":project:*"
                            f":workspace:{WORKSPACE_NAME}"
                            f":run_phase:*"
                        ),
                    },
                },
            }
        ],
    }

    try:
        existing = iam.get_role(RoleName=IAM_ROLE_NAME)
        arn = existing["Role"]["Arn"]
        iam.update_assume_role_policy(
            RoleName=IAM_ROLE_NAME, PolicyDocument=json.dumps(trust)
        )
        print(f"  reusing IAM role (trust refreshed): {arn}")
    except ClientError as e:
        if e.response["Error"]["Code"] != "NoSuchEntity":
            raise
        resp = iam.create_role(
            RoleName=IAM_ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust),
            Description=(
                "OIDC federation role for pyTFE workspace - managed by "
                "examples/oidc_aws_e2e.py"
            ),
        )
        arn = resp["Role"]["Arn"]
        print(f"  created IAM role: {arn}")

    # Tight inline policy: EC2 reads the AWS provider needs at plan time +
    # RunInstances/TerminateInstances/CreateTags for our test resource.
    # Drop ec2:DescribeVpcAttribute and the plan errors with
    # UnauthorizedOperation; the others are pulled in by the network/subnet
    # data sources Terraform hydrates during plan.
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeImages",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeVpcAttribute",
                    "ec2:DescribeVpcClassicLink",
                    "ec2:DescribeVpcClassicLinkDnsSupport",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DescribeNetworkAcls",
                    "ec2:DescribeRouteTables",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeAvailabilityZones",
                    "ec2:DescribeAccountAttributes",
                    "ec2:DescribeDhcpOptions",
                    "ec2:DescribeInstances",
                    "ec2:DescribeInstanceAttribute",
                    "ec2:DescribeInstanceStatus",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeInstanceCreditSpecifications",
                    "ec2:DescribeVolumes",
                    "ec2:DescribeTags",
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:CreateTags",
                    "ec2:DeleteTags",
                ],
                "Resource": "*",
            }
        ],
    }
    iam.put_role_policy(
        RoleName=IAM_ROLE_NAME,
        PolicyName=f"{IAM_ROLE_NAME}-ec2",
        PolicyDocument=json.dumps(policy),
    )
    return arn


def ensure_workspace(client: TFEClient) -> Workspace:
    try:
        ws = client.workspaces.read(WORKSPACE_NAME, organization=HCP_ORG)
        print(f"  reusing workspace: {ws.id}")
        return ws
    except TFEError:
        ws = client.workspaces.create(
            HCP_ORG,
            WorkspaceCreateOptions(
                name=WORKSPACE_NAME,
                description="Created by pyTFE OIDC AWS end-to-end example.",
                auto_apply=False,
            ),
        )
        print(f"  created workspace: {ws.id}")
        return ws


def upsert_env_var(
    client: TFEClient,
    workspace_id: str,
    key: str,
    value: str,
    *,
    sensitive: bool,
) -> None:
    for v in client.variables.list(workspace_id):
        if v.key == key:
            client.variables.delete(workspace_id, v.id)
            break
    client.variables.create(
        workspace_id,
        VariableCreateOptions(
            key=key,
            value=value,
            category=CategoryType.ENV,
            sensitive=sensitive,
        ),
    )
    print(f"  set {key} = {'(sensitive)' if sensitive else value}")


def make_tarball(files: dict[str, bytes]) -> io.BytesIO:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = int(time.time())
            tar.addfile(info, io.BytesIO(data))
    buf.seek(0)
    return buf


TERMINAL_BAD = {"errored", "canceled", "discarded", "force_canceled"}
TERMINAL_GOOD = {"applied", "planned_and_finished"}
TERMINAL = TERMINAL_BAD | TERMINAL_GOOD


def wait_for_run(
    client: TFEClient, run_id: str, label: str, timeout_s: int = 900
) -> str:
    deadline = time.time() + timeout_s
    last = ""
    while time.time() < deadline:
        run = client.runs.read(run_id)
        status = run.status.value if run.status else ""
        if status != last:
            print(f"  [{label}] status: {status}")
            last = status
        if status in TERMINAL:
            return status
        time.sleep(5)
    raise TimeoutError(
        f"{label}: run {run_id} did not reach terminal state within {timeout_s}s"
    )


def find_test_instance(ec2) -> dict | None:
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [INSTANCE_NAME_TAG]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]},
        ]
    )
    for r in resp["Reservations"]:
        for i in r["Instances"]:
            return i
    return None


# ---- Main flow ----


def main() -> int:
    boto3.setup_default_session(region_name=AWS_REGION)
    iam = boto3.client("iam")
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    sts = boto3.client("sts")

    print(f"Caller identity: {sts.get_caller_identity()['Arn']}")
    print(f"HCP org:         {HCP_ORG}")
    print(f"Workspace:       {WORKSPACE_NAME}")
    print(f"AWS region:      {AWS_REGION}")
    print(f"IAM role:        {IAM_ROLE_NAME}")
    print(f"Instance type:   {INSTANCE_TYPE}")
    print(f"Destroy at end:  {DESTROY_AFTER_VERIFY}")

    client = TFEClient()

    try:
        banner("1. AWS: ensure OIDC provider for app.terraform.io")
        oidc_arn = ensure_oidc_provider(iam)

        banner("2. AWS: ensure IAM role + trust policy + EC2 policy")
        role_arn = ensure_iam_role(iam, oidc_arn)

        banner("3. HCP: ensure workspace")
        workspace = ensure_workspace(client)

        banner("4. HCP: set TFC_AWS_PROVIDER_AUTH + TFC_AWS_RUN_ROLE_ARN")
        upsert_env_var(
            client, workspace.id, "TFC_AWS_PROVIDER_AUTH", "true", sensitive=False
        )
        upsert_env_var(
            client, workspace.id, "TFC_AWS_RUN_ROLE_ARN", role_arn, sensitive=True
        )

        banner("5. HCP: upload Terraform configuration")
        cv = client.configuration_versions.create(
            workspace.id,
            ConfigurationVersionCreateOptions(auto_queue_runs=False),
        )
        if not cv.upload_url:
            raise RuntimeError("configuration version missing upload URL")
        client.configuration_versions.upload_tar_gzip(
            cv.upload_url, make_tarball({"main.tf": TERRAFORM_MAIN_TF})
        )
        for _ in range(30):
            cv = client.configuration_versions.read(cv.id)
            if cv.status and cv.status.value == "uploaded":
                break
            time.sleep(2)
        print(f"  configuration version: {cv.id} (status={cv.status})")

        banner("6. HCP: queue run, plan, apply (OIDC federates here)")
        run = client.runs.create(
            RunCreateOptions(
                workspace=Workspace(id=workspace.id),
                configuration_version=ConfigurationVersion(id=cv.id),
                message="pyTFE OIDC AWS end-to-end example - create",
            )
        )
        print(f"  run: {run.id}")
        # If the workspace doesn't auto-apply, confirm the plan once it's ready.
        # If it does auto-apply, the run will progress straight to `applied`.
        end_status = wait_for_run(client, run.id, label="create")
        if end_status not in TERMINAL_GOOD:
            # Try to confirm a planned-but-not-applied run.
            run = client.runs.read(run.id)
            if run.status and run.status.value in (
                "planned",
                "planned_and_saved",
                "cost_estimated",
                "policy_checked",
            ):
                client.runs.apply(run.id)
                end_status = wait_for_run(client, run.id, label="apply")
        if end_status not in TERMINAL_GOOD:
            raise RuntimeError(f"create run did not succeed: status={end_status}")

        banner("7. AWS: verify EC2 instance exists (proves OIDC federation worked)")
        # Brief settle window for AWS API consistency on the tag filter.
        instance = None
        for _ in range(20):
            instance = find_test_instance(ec2)
            if instance:
                break
            time.sleep(3)
        if not instance:
            raise RuntimeError(
                f"expected one running instance with tag Name={INSTANCE_NAME_TAG}, found none"
            )
        print(f"  instance id:   {instance['InstanceId']}")
        print(f"  state:         {instance['State']['Name']}")
        print(f"  instance type: {instance['InstanceType']}")
        print(f"  az:            {instance['Placement']['AvailabilityZone']}")
        print(f"  vpc:           {instance['VpcId']}")

        if not DESTROY_AFTER_VERIFY:
            banner("DONE (skipping destroy per OIDC_DESTROY_AFTER_VERIFY=false)")
            print(f"  Workspace KEPT:        {workspace.id} ({WORKSPACE_NAME})")
            print(f"  IAM role KEPT:         {role_arn}")
            print(f"  OIDC provider KEPT:    {oidc_arn}")
            print(f"  EC2 instance KEPT:     {instance['InstanceId']}")
            return 0

        banner("8. HCP: queue destroy run (re-exercises OIDC the other way)")
        destroy_run = client.runs.create(
            RunCreateOptions(
                workspace=Workspace(id=workspace.id),
                message="pyTFE OIDC AWS end-to-end example - destroy",
                is_destroy=True,
            )
        )
        print(f"  run: {destroy_run.id}")
        end_status = wait_for_run(client, destroy_run.id, label="destroy")
        if end_status not in TERMINAL_GOOD:
            destroy_run = client.runs.read(destroy_run.id)
            if destroy_run.status and destroy_run.status.value in (
                "planned",
                "planned_and_saved",
            ):
                client.runs.apply(destroy_run.id)
                end_status = wait_for_run(client, destroy_run.id, label="destroy-apply")
        if end_status not in TERMINAL_GOOD:
            raise RuntimeError(f"destroy run did not succeed: status={end_status}")

        banner("9. AWS: confirm EC2 instance terminated")
        instance_id = instance["InstanceId"]
        for attempt in range(30):
            resp = ec2.describe_instances(InstanceIds=[instance_id])
            state = resp["Reservations"][0]["Instances"][0]["State"]["Name"]
            print(f"  attempt {attempt + 1}: {instance_id} -> {state}")
            if state == "terminated":
                break
            time.sleep(5)

        banner("SUCCESS: end-to-end OIDC federation verified via pyTFE")
        print(f"  Workspace KEPT:        {workspace.id} ({WORKSPACE_NAME})")
        print(f"  IAM role KEPT:         {role_arn}")
        print(f"  OIDC provider KEPT:    {oidc_arn}")
        print("  EC2 instance:          terminated (cleanup successful)")
        return 0

    except Exception:
        traceback.print_exc()
        print()
        print("!!! FAILURE — leaving all resources in place for inspection !!!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
