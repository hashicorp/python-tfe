from __future__ import annotations

import argparse
import os
from pathlib import Path

from tfe import TFEClient, TFEConfig
from tfe.errors import ErrStateVersionUploadNotSupported
from tfe.models.state_version import (
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionListOptions,
)
from tfe.models.state_version_output import StateVersionOutputsListOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="State Versions demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--workspace", required=True, help="Workspace name")
    parser.add_argument("--workspace-id", required=True, help="Workspace ID")
    parser.add_argument("--download", help="Path to save downloaded current state")
    parser.add_argument("--upload", help="Path to a .tfstate (or JSON state) to upload")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    options = StateVersionListOptions(
        page_number=args.page,
        page_size=args.page_size,
        organization=args.org,
        workspace=args.workspace,
    )

    sv_list = client.state_versions.list(options)

    print(f"Total state versions: {sv_list.total_count}")
    print(f"Page {sv_list.current_page} of {sv_list.total_pages}")
    print()

    for sv in sv_list.items:
        print(f"- {sv.id} | status={sv.status} | created_at={sv.created_at}")

    # 1) List all state versions across org and workspace filters
    _print_header("Org-scoped listing via /api/v2/state-versions (first page)")
    all_sv = client.state_versions.list(
        StateVersionListOptions(
            organization=args.org, workspace=args.workspace, page_size=args.page_size
        )
    )
    for sv in all_sv.items:
        print(f"- {sv.id} | status={sv.status} | created_at={sv.created_at}")

    # 2) Read the current state version (with outputs included if you want)
    _print_header("Reading current state version")
    current = client.state_versions.read_current_with_options(
        args.workspace_id, StateVersionCurrentOptions(include=["outputs"])
    )
    print(
        f"Current SV: {current.id} status={current.status} durl={current.hosted_state_download_url}"
    )

    # 3) (Optional) Download the current state (optional)
    if args.download:
        _print_header(f"Downloading current state to: {args.download}")
        raw = client.state_versions.download(current.id)
        Path(args.download).write_bytes(raw)
        print(f"Wrote {len(raw)} bytes to {args.download}")

    # 4) List outputs for the current state version (paged)
    _print_header("Listing outputs (current state version)")
    outs = client.state_versions.list_outputs(
        current.id, options=StateVersionOutputsListOptions(page_size=50)
    )
    if not outs.items:
        print("No outputs found.")
    for o in outs.items:
        # Sensitive outputs will have value = None
        print(f"- {o.name}: sensitive={o.sensitive} type={o.type} value={o.value}")

    # 5) (Optional) Upload a new state file
    if args.upload:
        _print_header(f"Uploading new state from: {args.upload}")
        payload = Path(args.upload).read_bytes()
        try:
            # If your server supports signed uploads, this will:
            #   a) create SV (to get upload URL)
            #   b) PUT bytes to the signed URL
            #   c) read back the SV to return a hydrated object
            new_sv = client.state_versions.upload(
                args.workspace_id,
                raw_state=payload,
                options=StateVersionCreateOptions(),
            )
            print(f"Uploaded new SV: {new_sv.id} status={new_sv.status}")
        except ErrStateVersionUploadNotSupported as e:
            # Some older/self-hosted versions don’t support direct upload
            print(f"Upload not supported on this server: {e}")


if __name__ == "__main__":
    main()
