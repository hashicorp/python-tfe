# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from pytfe import TFEClient, TFEConfig
from pytfe.errors import ErrStateVersionUploadNotSupported
from pytfe.models import (
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionListOptions,
    StateVersionOutputsListOptions,
    StateVersionReadOptions,
)
from pytfe.models.workspace import WorkspaceLockOptions


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _install_debug_hook(client: TFEClient, token: str) -> None:
    """
    Wrap the transport's request() to print every URL and its headers.
    The Authorization token value is masked so it is safe to share output.
    """
    transport = client.state_versions.t
    original_request = transport.request

    def _debug_request(method, path, **kwargs):
        use_defaults = kwargs.get("use_default_headers", True)
        extra_headers = kwargs.get("headers") or {}

        # Reconstruct exactly what the transport will send
        if use_defaults:
            sent_headers = dict(transport.headers)
            sent_headers.update(extra_headers)
        else:
            sent_headers = dict(extra_headers)

        # Mask the bearer token so it is safe to print
        display_headers = {}
        for k, v in sent_headers.items():
            if k.lower() == "authorization":
                masked = v[:14] + "***" + v[-4:] if len(v) > 18 else "***"
                display_headers[k] = masked
            else:
                display_headers[k] = v

        url = transport._build_url(path)
        print(f"\n  [DEBUG] {method} {url}")
        for k, v in display_headers.items():
            print(f"          {k}: {v}")

        return original_request(method, path, **kwargs)

    transport.request = _debug_request


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
    parser.add_argument(
        "--download", help="Optional path to save downloaded current state"
    )
    parser.add_argument(
        "--upload",
        help="Optional path to a .tfstate JSON to upload (defaults to current state with serial bumped by 1)",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip the upload demo (upload requires locking the workspace).",
    )
    parser.add_argument(
        "--demo-backing-data",
        action="store_true",
        help="Exercise TFE-only soft_delete/restore backing-data actions on the newly uploaded SV.",
    )
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print every request URL and headers (token masked).",
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    if args.debug:
        _install_debug_hook(client, args.token)

    # 1) List state versions filtered by org + workspace
    _print_header("Listing state versions (filter[organization]+filter[workspace])")
    sv_list = list(
        client.state_versions.list(
            StateVersionListOptions(
                page_size=args.page_size,
                organization=args.org,
                workspace=args.workspace,
            )
        )
    )
    print(f"Total state versions returned: {len(sv_list)}")
    for sv in sv_list:
        print(f"- {sv.id} | status={sv.status} | created_at={sv.created_at}")

    # 2) Read the current state version with include=outputs
    _print_header("read_current_with_options(include=outputs)")
    current = client.state_versions.read_current_with_options(
        args.workspace_id, StateVersionCurrentOptions(include=["outputs"])
    )
    print(f"Current SV: {current.id} status={current.status}")
    print(f"  download_url:      {current.hosted_state_download_url}")
    print(f"  json_download_url: {current.hosted_json_state_download_url}")

    # 3) Read by ID, with and without include options
    _print_header("read(sv_id) and read_with_options(sv_id, include=[run,outputs])")
    sv_read = client.state_versions.read(current.id)
    print(f"read():              id={sv_read.id} serial={sv_read.serial}")
    sv_read_opts = client.state_versions.read_with_options(
        current.id, StateVersionReadOptions(include=["run", "outputs"])
    )
    print(f"read_with_options(): id={sv_read_opts.id} serial={sv_read_opts.serial}")

    # 4) Download current state bytes
    _print_header("download(current_sv_id)")
    raw_current = client.state_versions.download(current.id)
    print(f"Downloaded {len(raw_current)} bytes of state")
    if args.download:
        Path(args.download).write_bytes(raw_current)
        print(f"  wrote bytes to {args.download}")

    # 5) List outputs (by SV and via workspace shortcut)
    _print_header("list_outputs(current_sv_id)")
    outs = list(
        client.state_versions.list_outputs(
            current.id, options=StateVersionOutputsListOptions(page_size=50)
        )
    )
    if not outs:
        print("No outputs found.")
    for o in outs:
        print(f"- {o.name}: sensitive={o.sensitive} type={o.type} value={o.value}")

    _print_header("state_version_outputs.read_current(workspace_id)")
    outs2 = list(
        client.state_version_outputs.read_current(
            args.workspace_id, options=StateVersionOutputsListOptions(page_size=50)
        )
    )
    if not outs2:
        print("No outputs found.")
    for o in outs2:
        print(f"- {o.name}: sensitive={o.sensitive} type={o.type} value={o.value}")

    # 6) Upload demo: requires the workspace to be locked.
    if args.skip_upload:
        _print_header("Skipping upload demo (--skip-upload)")
        return

    _print_header("upload(workspace_id, raw_state=..., options=...)")
    if args.upload:
        payload = Path(args.upload).read_bytes()
        print(f"Using user-provided payload from {args.upload} ({len(payload)} bytes)")
    else:
        try:
            state_obj = json.loads(raw_current.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Could not parse current state as JSON; skip upload: {e}")
            return
        state_obj["serial"] = int(state_obj.get("serial", 0)) + 1
        payload = json.dumps(state_obj).encode("utf-8")
        print(
            f"Synthesized payload from current state with serial bumped to "
            f"{state_obj['serial']} ({len(payload)} bytes)"
        )

    try:
        state_obj = json.loads(payload.decode("utf-8"))
        serial = int(state_obj["serial"])
        lineage = state_obj.get("lineage")
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Upload input must be valid Terraform state JSON with a serial: {e}")
        return

    md5 = hashlib.md5(payload).hexdigest()  # nosec B324

    locked = False
    try:
        client.workspaces.lock(
            args.workspace_id,
            WorkspaceLockOptions(reason="python-tfe state_versions example"),
        )
        locked = True
        print(f"Locked workspace {args.workspace_id}")
    except Exception as e:
        print(f"Could not lock workspace (continuing without lock): {e}")

    new_sv = None
    try:
        new_sv = client.state_versions.upload(
            args.workspace_id,
            raw_state=payload,
            options=StateVersionCreateOptions(
                serial=serial,
                md5=md5,
                lineage=lineage,
            ),
        )
        print(
            f"Uploaded new SV: {new_sv.id} status={new_sv.status} serial={new_sv.serial}"
        )
    except ErrStateVersionUploadNotSupported as e:
        print(f"Upload not supported on this server: {e}")
    except Exception as e:
        print(f"Upload failed: {e}")
    finally:
        if locked:
            try:
                client.workspaces.unlock(args.workspace_id)
                print(f"Unlocked workspace {args.workspace_id}")
            except Exception as e:
                print(f"Failed to unlock workspace: {e}")

    # 7) Optional: exercise TFE-only backing data actions on the new SV
    if args.demo_backing_data and new_sv is not None:
        _print_header("TFE-only backing data actions on the new SV")
        try:
            client.state_versions.soft_delete_backing_data(new_sv.id)
            print("soft_delete_backing_data: OK")
            client.state_versions.restore_backing_data(new_sv.id)
            print("restore_backing_data: OK")
            print("(skipping permanently_delete_backing_data — irreversible)")
        except Exception as e:
            print(
                f"Backing-data actions not available (likely HCP Terraform, not TFE): {e}"
            )


if __name__ == "__main__":
    main()
