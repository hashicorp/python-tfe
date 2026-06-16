# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from urllib.parse import urlencode

from .._jsonapi import attach_jsonapi
from ..errors import ErrStateVersionUploadNotSupported, NotFound, TFEError
from ..models.state_version import (
    StateVersion,
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionListOptions,
    StateVersionReadOptions,
)
from ..models.state_version_output import (
    StateVersionOutput,
    StateVersionOutputsListOptions,
)
from ..utils import looks_like_workspace_id, valid_string_id
from ._base import _Service


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


class StateVersions(_Service):
    """
    TFE/TFC State Versions service.

    Endpoints covered (JSON:API):
      - GET  /api/v2/workspaces/:workspace_id/state-versions
      - GET  /api/v2/workspaces/:workspace_id/current-state-version
      - GET  /api/v2/state-versions/:id
      - GET  /api/v2/state-versions/:id/download
      - GET  /api/v2/state-versions/:id/outputs
      - POST /api/v2/workspaces/:workspace_id/state-versions
      - POST /api/v2/state-versions/:id/actions/soft_delete_backing_data      (TFE only)
      - POST /api/v2/state-versions/:id/actions/restore_backing_data          (TFE only)
      - POST /api/v2/state-versions/:id/actions/permanently_delete_backing_data (TFE only)
    """

    def _resolve_workspace_id(self, workspace: str, organization: str | None) -> str:
        """Accept a workspace ID (ws-xxxxxx) or resolve by name with organization."""
        if looks_like_workspace_id(workspace):
            return workspace
        if not organization:
            raise ValueError("organization is required when workspace is a name")
        r = self.t.request(
            "GET", f"/api/v2/organizations/{organization}/workspaces/{workspace}"
        )
        data = r.json().get("data") or {}
        ws_id = _safe_str(data.get("id"))
        if not ws_id:
            raise NotFound(f"workspace '{workspace}' not found in org '{organization}'")
        return ws_id

    # ----------------------------
    # Listing & reading
    # ----------------------------

    @staticmethod
    def _encode_query(params: dict[str, Any]) -> str:
        clean = {k: v for k, v in params.items() if v is not None}
        if not clean:
            return ""
        return "?" + urlencode(clean, doseq=True)

    def list(
        self, options: StateVersionListOptions | None = None
    ) -> Iterator[StateVersion]:
        """
        GET /state-versions
        Accepts filters for organization and workspace and standard pagination.
        """
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/state-versions{self._encode_query(params)}"
        for d in self._list(path, params=params):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            yield attach_jsonapi(StateVersion.model_validate(attrs), d)

    def read(self, state_version_id: str) -> StateVersion:
        """Read a state version by ID."""
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        r = self.t.request("GET", f"/api/v2/state-versions/{state_version_id}")
        payload = r.json()
        d = payload["data"]
        attr = d.get("attributes", {}) or {}

        return attach_jsonapi(
            StateVersion(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            ),
            d,
            payload.get("included"),
        )

    def read_with_options(
        self, state_version_id: str, options: StateVersionReadOptions
    ) -> StateVersion:
        """Read a state version with include options (?include=outputs,run,created_by,...)."""
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)

        r = self.t.request(
            "GET", f"/api/v2/state-versions/{state_version_id}", params=params
        )
        payload = r.json()
        d = payload["data"]
        attr = d.get("attributes", {}) or {}

        return attach_jsonapi(
            StateVersion(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            ),
            d,
            payload.get("included"),
        )

    def read_current(self, workspace_id: str) -> StateVersion:
        """Read the current state version for a workspace."""
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        r = self.t.request(
            "GET", f"/api/v2/workspaces/{workspace_id}/current-state-version"
        )
        payload = r.json()
        d = payload["data"]
        attr = d.get("attributes", {}) or {}

        return attach_jsonapi(
            StateVersion(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            ),
            d,
            payload.get("included"),
        )

    def read_current_with_options(
        self, workspace_id: str, options: StateVersionCurrentOptions
    ) -> StateVersion:
        """Read the current state version with include options."""
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        params: dict[str, Any] = {}
        if options and options.include:
            params["include"] = ",".join(options.include)

        r = self.t.request(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/current-state-version",
            params=params,
        )
        payload = r.json()
        d = payload["data"]
        attr = d.get("attributes", {}) or {}

        return attach_jsonapi(
            StateVersion(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            ),
            d,
            payload.get("included"),
        )

    # ----------------------------
    # Create / upload (signed URL)
    # ----------------------------

    def create(
        self,
        workspace: str,
        options: StateVersionCreateOptions,
        *,
        organization: str | None = None,
    ) -> StateVersion:
        """Create a state-version record (returns hosted upload URLs if content omitted)."""
        ws_id = self._resolve_workspace_id(workspace, organization)

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        if not attrs:
            # API requires attributes; at minimum serial & md5
            raise ValueError(
                "state-version create requires attributes (at least serial & md5)"
            )

        body = {"data": {"type": "state-versions", "attributes": attrs}}
        r = self.t.request(
            "POST", f"/api/v2/workspaces/{ws_id}/state-versions", json_body=body
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    def upload(
        self,
        workspace: str,
        *,
        raw_state: bytes | None,
        raw_json_state: bytes | None = None,
        options: StateVersionCreateOptions,
        organization: str | None = None,
    ) -> StateVersion:
        """
        Create a state version and upload state bytes to signed Archivist URLs.

        This mirrors Terraform's recommended workflow:
          1. POST /workspaces/:id/state-versions with serial+md5 and no inline state
          2. PUT raw state bytes to hosted-state-upload-url
          3. Optional PUT JSON state bytes to hosted-json-state-upload-url
          4. Read the state version again and return the refreshed object
        """
        if raw_state is None:
            raise ValueError("raw_state is required")
        if options.state is not None or options.json_state is not None:
            raise ValueError(
                "options.state and options.json_state must be omitted when using upload"
            )

        try:
            sv = self.create(workspace, options, organization=organization)
        except TFEError as exc:
            # Older servers can reject the create-without-inline-state flow.
            if "param is missing or the value is empty: state" in str(exc):
                raise ErrStateVersionUploadNotSupported(
                    "state version upload is not supported by this server"
                ) from exc
            raise

        if not sv.hosted_state_upload_url:
            raise ErrStateVersionUploadNotSupported(
                "hosted-state-upload-url not returned by server"
            )

        self.t.request(
            "PUT",
            sv.hosted_state_upload_url,
            data=raw_state,
            headers={"Content-Type": "application/octet-stream"},
        )

        if raw_json_state is not None:
            if not sv.hosted_json_state_upload_url:
                raise ErrStateVersionUploadNotSupported(
                    "hosted-json-state-upload-url not returned by server"
                )
            self.t.request(
                "PUT",
                sv.hosted_json_state_upload_url,
                data=raw_json_state,
                headers={"Content-Type": "application/octet-stream"},
            )

        return self.read(sv.id)

    def download(self, state_version_id: str) -> bytes:
        """
        Download the raw state file bytes for a specific state version.

        HCP Terraform returns a signed blob URL in the state-version attributes
        called 'hosted-state-download-url'. We must fetch that URL directly.
        """
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        sv = self.read(state_version_id)
        url = sv.hosted_state_download_url
        if not url:
            # Can happen if SV is missing, not finalized yet, or you lack permissions.
            # Also happens on some older/self-hosted versions if backing data was GC’d.
            from ..errors import NotFound

            raise NotFound("download url not available for this state version")

        # Download the bytes from the signed Archivist URL. The presigned URL
        # already carries its own credentials, so the TFE bearer token must
        # NOT be forwarded.
        resp = self.t.request(
            "GET",
            url,
            allow_redirects=True,
            headers={"Accept": "*/*"},
        )
        return resp.content

    def download_current(self, workspace_id: str) -> bytes:
        """Download the current state for a workspace."""
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        sv = self.read_current(workspace_id)
        url = sv.hosted_state_download_url
        if not url:
            from ..errors import NotFound

            raise NotFound("download url not available for current state")
        resp = self.t.request(
            "GET",
            url,
            allow_redirects=True,
            headers={"Accept": "*/*"},
        )
        return resp.content

    # ----------------------------
    # Outputs (via state version)
    # ----------------------------

    def list_outputs(
        self,
        state_version_id: str,
        options: StateVersionOutputsListOptions | None = None,
    ) -> Iterator[StateVersionOutput]:
        """List outputs for a given state version (paged)."""
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        path = f"/api/v2/state-versions/{state_version_id}/outputs"

        for d in self._list(path, params=params):
            attr = d.get("attributes", {}) or {}
            yield StateVersionOutput(
                id=_safe_str(d.get("id")),
                **{k.replace("-", "_"): v for k, v in attr.items()},
            )

    # ----------------------------
    # TFE-only backing data actions
    # ----------------------------

    def soft_delete_backing_data(self, state_version_id: str) -> None:
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")
        self.t.request(
            "POST",
            f"/api/v2/state-versions/{state_version_id}/actions/soft_delete_backing_data",
        )
        return None

    def restore_backing_data(self, state_version_id: str) -> None:
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")
        self.t.request(
            "POST",
            f"/api/v2/state-versions/{state_version_id}/actions/restore_backing_data",
        )
        return None

    def permanently_delete_backing_data(self, state_version_id: str) -> None:
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")
        self.t.request(
            "POST",
            f"/api/v2/state-versions/{state_version_id}/actions/permanently_delete_backing_data",
        )
        return None

    def rollback(
        self,
        workspace_id: str,
        rollback_state_version_id: str,
    ) -> StateVersion:
        """Roll a workspace back to a previous state version.

        Duplicates the named state version and sets the copy as the workspace's
        current state version. The workspace must be locked by the caller
        before invoking this operation, otherwise the API returns 409.
        """
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")
        if not valid_string_id(rollback_state_version_id):
            raise ValueError("invalid rollback state version id")
        body = {
            "data": {
                "type": "state-versions",
                "relationships": {
                    "rollback-state-version": {
                        "data": {
                            "type": "state-versions",
                            "id": rollback_state_version_id,
                        }
                    }
                },
            }
        }
        resp = self.t.request(
            "PATCH",
            f"/api/v2/workspaces/{workspace_id}/state-versions",
            json_body=body,
        )
        data = (resp.json() or {}).get("data") or {}
        attributes = dict(data.get("attributes") or {})
        attributes["id"] = data.get("id", "")
        return attach_jsonapi(StateVersion.model_validate(attributes), data)
