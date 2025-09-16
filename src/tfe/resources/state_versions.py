from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Optional, Dict
from urllib.parse import urlencode

from ..utils import valid_string_id
from ._base import _Service
from ..errors import (
    ErrStateVersionUploadNotSupported
)

# Pydantic models for this feature
from ..models.state_version import (
    StateVersion,
    StateVersionCreateOptions,
    StateVersionCurrentOptions,
    StateVersionList,
    StateVersionListOptions,
    StateVersionReadOptions,
)
from ..models.state_version_output import (
    StateVersionOutputsList,
    StateVersionOutputsListOptions,
    StateVersionOutput,
)


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

    # ----------------------------
    # Listing & reading
    # ----------------------------

    @staticmethod
    def _encode_query(params: Dict[str, Any]) -> str:
        clean = {k: v for k, v in params.items() if v is not None}
        if not clean:
            return ""
        return "?" + urlencode(clean, doseq=True)

    def list(self, options: Optional[StateVersionListOptions] = None) -> StateVersionList:
        """
        GET /state-versions
        Accepts filters for organization and workspace and standard pagination.
        """
        params = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        path = f"/api/v2/state-versions{self._encode_query(params)}"
        r = self.t.request("GET", path)
        jd = r.json()
        # Expecting JSON:API list. Normalize to models.
        items = []
        meta = jd.get("meta", {})
        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            items.append(StateVersion.model_validate(attrs))
        return StateVersionList(
            items=items,
            current_page=meta.get("pagination", {}).get("current-page"),
            total_pages=meta.get("pagination", {}).get("total-pages"),
            total_count=meta.get("pagination", {}).get("total-count"),
        )


    def read(self, state_version_id: str) -> StateVersion:
        """Read a state version by ID."""
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        r = self.t.request("GET", f"/api/v2/state-versions/{state_version_id}")
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
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
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    def read_current(self, workspace_id: str) -> StateVersion:
        """Read the current state version for a workspace."""
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        r = self.t.request(
            "GET", f"/api/v2/workspaces/{workspace_id}/current-state-version"
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
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
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}

        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    # ----------------------------
    # Create / upload (signed URL)
    # ----------------------------

    def create(
        self, workspace_id: str, options: Optional[StateVersionCreateOptions] = None
    ) -> StateVersion:
        """Create a state version record (server returns signed upload URL)."""
        if not valid_string_id(workspace_id):
            raise ValueError("invalid workspace id")

        body = {
            "data": {
                "type": "state-versions",
                "attributes": (options.model_dump(by_alias=True, exclude_none=True) if options else {}),
            }
        }
        r = self.t.request(
            "POST", f"/api/v2/workspaces/{workspace_id}/state-versions", json_body=body
        )
        d = r.json()["data"]
        attr = d.get("attributes", {}) or {}
        return StateVersion(
            id=_safe_str(d.get("id")),
            **{k.replace("-", "_"): v for k, v in attr.items()},
        )

    def upload(self, workspace_id: str, *, raw_state: bytes | None = None, raw_json_state: bytes | None = None,
               options: Optional[StateVersionCreateOptions] = None) -> StateVersion:
        """
        Mirrors go-tfe Upload:
          1) POST to create (obtain upload URL)
          2) PUT the raw content to the object store (archivist)
        """
        sv = self.create(workspace_id, options or StateVersionCreateOptions())
        upload_url = sv.hosted_state_upload_url
        if not upload_url:
            raise ErrStateVersionUploadNotSupported(
                message="Server did not return an upload URL for state version",
                method="PUT", path="(signed upload URL)"
            )

        # Choose the content
        content = raw_json_state if raw_json_state is not None else raw_state
        if content is None:
            raise ErrStateVersionUploadNotSupported(message="No state content provided", method="PUT", path=upload_url)

        # Raw PUT to the object store
        self.t.request(
            "PUT",
            upload_url,
            json_body=None,
            allow_redirects=True,
            timeout=120,
            headers={"Content-Type": "application/octet-stream"},
            raw_body=content,  # transport should use raw bytes when provided
            retry_non_idempotent=False,
        )

        # Read back the created SV to reflect any server-side fields
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

        # Download the bytes from the signed Archivist URL (follow redirects).
        # Avoid JSON:API headers here; Accept */* is fine.
        resp = self.t.request("GET", url, allow_redirects=True, headers={"Accept": "application/json"})
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
        resp = self.t.request("GET", url, allow_redirects=True, headers={"Accept": "*/*"})
        return resp.content



    # ----------------------------
    # Outputs (via state version)
    # ----------------------------

    def list_outputs(
        self, state_version_id: str, options: Optional[StateVersionOutputsListOptions] = None
    ) -> StateVersionOutputsList:
        """List outputs for a given state version (paged)."""
        if not valid_string_id(state_version_id):
            raise ValueError("invalid state version id")

        params: dict[str, Any] = {}
        if options:
            if options.page_number is not None:
                params["page[number]"] = options.page_number
            if options.page_size is not None:
                params["page[size]"] = options.page_size

        r = self.t.request(
            "GET", f"/api/v2/state-versions/{state_version_id}/outputs", params=params
        )
        data = r.json()

        items: list[StateVersionOutput] = []
        for item in data.get("data", []):
            attr = item.get("attributes", {}) or {}
            items.append(
                StateVersionOutput(
                    id=_safe_str(item.get("id")),
                    **{k.replace("-", "_"): v for k, v in attr.items()},
                )
            )

        meta = data.get("meta", {}).get("pagination", {}) or {}
        return StateVersionOutputsList(
            items=items,
            current_page=meta.get("current-page"),
            total_pages=meta.get("total-pages"),
            total_count=meta.get("total-count"),
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
