from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from ..errors import NotFound

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
    StateVersionOutput,
    StateVersionOutputsList,
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

    def list(self, options: StateVersionListOptions | None = None) -> StateVersionList:
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

    """
    def upload(
        self,
        workspace: str,
        *,
        raw_state: bytes | None = None,
        raw_json_state: bytes | None = None,
        options: Optional[StateVersionCreateOptions] = None,
        organization: Optional[str] = None,
    ) -> StateVersion:
    # TBD: Implements Upload State Functionality
    """

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
        resp = self.t.request(
            "GET", url, allow_redirects=True, headers={"Accept": "application/json"}
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
            "GET", url, allow_redirects=True, headers={"Accept": "*/*"}
        )
        return resp.content

    # ----------------------------
    # Outputs (via state version)
    # ----------------------------

    def list_outputs(
        self,
        state_version_id: str,
        options: StateVersionOutputsListOptions | None = None,
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
