# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""The read-only gate, the before_request hook, and error hints.

The gate lives on the httpx client's request event hook rather than inside
``HTTPTransport.request``, because two upload paths issue ``self.t._sync.put``
directly and never reach ``request()``. Those bypass paths are the most
important thing a read-only client has to block, so they are tested explicitly.
"""

from __future__ import annotations

import io

import httpx
import pytest

from pytfe import TFEClient, TFEConfig
from pytfe.config import RequestInfo, request_info
from pytfe.errors import AuthError, NotFound, ReadOnlyViolation, TFEError


def make_client(**kw: object) -> TFEClient:
    return TFEClient(
        TFEConfig(address="https://tfe.example.com", token="t", **kw)  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------
# RequestInfo
# --------------------------------------------------------------------------


def test_request_info_classifies_writes() -> None:
    assert request_info("GET", "/api/v2/organizations").is_write is False
    assert request_info("head", "/api/v2/organizations").is_write is False
    assert request_info("POST", "/api/v2/organizations").is_write is True
    assert request_info("delete", "/api/v2/workspaces/ws-1").is_write is True


def test_request_info_extracts_the_resource() -> None:
    info = request_info("POST", "/api/v2/organizations/acme/workspaces")
    assert info.resource == "organizations"
    assert request_info("GET", "https://x/api/v2/runs/run-1").resource == "runs"
    # An absolute blob URL has no /api/v2/ segment.
    assert request_info("PUT", "https://archivist.terraform.io/v1/o/x").resource is None


# --------------------------------------------------------------------------
# read_only
# --------------------------------------------------------------------------


def test_read_only_blocks_writes_through_request() -> None:
    client = make_client(read_only=True)
    try:
        with pytest.raises(ReadOnlyViolation) as excinfo:
            client._transport.request("POST", "/api/v2/organizations/acme/workspaces")
        assert excinfo.value.method == "POST"
        assert excinfo.value.hint
    finally:
        client.close()


def test_read_only_blocks_the_upload_bypass() -> None:
    """configuration_versions.upload_tar_gzip goes straight to _sync.put.

    A gate placed only inside HTTPTransport.request would let a full Terraform
    configuration tarball reach Archivist from a read-only client.
    """
    client = make_client(read_only=True)
    try:
        with pytest.raises(TFEError) as excinfo:
            client.configuration_versions.upload_tar_gzip(
                "https://archivist.terraform.io/v1/object/abc", io.BytesIO(b"data")
            )
        assert isinstance(excinfo.value, ReadOnlyViolation)
    finally:
        client.close()


def test_read_only_allows_reads() -> None:
    client = make_client(read_only=True)
    try:
        client._transport._sync = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"data": []})
            ),
            event_hooks={"request": [client._transport._gate]},
        )
        response = client._transport.request("GET", "/api/v2/organizations")
        assert response.status_code == 200
    finally:
        client.close()


def test_read_only_honours_the_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTFE_READ_ONLY", "true")
    assert TFEConfig().read_only is True
    monkeypatch.setenv("PYTFE_READ_ONLY", "0")
    assert TFEConfig().read_only is False
    monkeypatch.delenv("PYTFE_READ_ONLY")
    assert TFEConfig().read_only is False


# --------------------------------------------------------------------------
# before_request
# --------------------------------------------------------------------------


def test_before_request_sees_every_request() -> None:
    seen: list[RequestInfo] = []
    client = make_client(before_request=seen.append)
    try:
        client._transport._sync = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"data": []})
            ),
            event_hooks={"request": [client._transport._gate]},
        )
        client._transport.request("GET", "/api/v2/organizations")
        assert len(seen) == 1
        assert seen[0].method == "GET"
        assert seen[0].resource == "organizations"
    finally:
        client.close()


def test_before_request_can_block() -> None:
    class Blocked(Exception):
        pass

    def veto(info: RequestInfo) -> None:
        if info.is_write:
            raise Blocked(info.path)

    client = make_client(before_request=veto)
    try:
        with pytest.raises(Blocked):
            client._transport.request("POST", "/api/v2/organizations/acme/workspaces")
    finally:
        client.close()


def test_config_with_a_callable_still_serializes() -> None:
    """A bare Callable field would break model_json_schema and model_dump_json."""
    config = TFEConfig(before_request=lambda info: None)
    assert config.model_dump_json()
    assert TFEConfig.model_json_schema()
    assert "before_request" not in config.model_dump()


# --------------------------------------------------------------------------
# Error hints
# --------------------------------------------------------------------------


def _error_for(status: int, payload: dict | None = None) -> TFEError:
    client = make_client()
    try:
        client._transport._sync = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status, json=payload or {})
            ),
            event_hooks={"request": [client._transport._gate]},
        )
        with pytest.raises(TFEError) as excinfo:
            client._transport.request("GET", "/api/v2/organizations")
        return excinfo.value
    finally:
        client.close()


@pytest.mark.parametrize(
    ("status", "needle"),
    [
        (401, "TFE_TOKEN"),
        (403, "permission"),
        (404, "Verify names"),
        (409, "locked workspace"),
        (500, "Server error"),
    ],
)
def test_hints_are_actionable(status: int, needle: str) -> None:
    error = _error_for(status)
    assert error.hint and needle in error.hint


def test_401_and_403_are_distinguishable() -> None:
    """Both raise AuthError, so the hint has to carry the difference."""
    unauthorized = _error_for(401)
    forbidden = _error_for(403)
    assert isinstance(unauthorized, AuthError)
    assert isinstance(forbidden, AuthError)
    assert unauthorized.hint != forbidden.hint


def test_422_names_the_offending_field() -> None:
    error = _error_for(
        422,
        {
            "errors": [
                {
                    "detail": "is not a valid version",
                    "source": {"pointer": "/data/attributes/terraform-version"},
                }
            ]
        },
    )
    assert error.hint is not None
    assert "terraform-version" in error.hint
    # The snake_case options field name is what the caller actually types.
    assert "terraform_version" in error.hint


def test_to_dict_is_json_serializable() -> None:
    import json

    error = _error_for(404)
    payload = error.to_dict()
    json.dumps(payload)
    assert payload["type"] == "NotFound"
    assert payload["status"] == 404
    assert payload["hint"]


def test_existing_error_behaviour_is_unchanged() -> None:
    """hint must not alter __str__ or args - downstream asserts on those."""
    plain = TFEError("boom", status=500)
    hinted = TFEError("boom", status=500, hint="try again")
    assert str(plain) == str(hinted) == "boom"
    assert plain.args == hinted.args == ("boom",)
    assert plain.hint is None


def test_workspace_not_found_is_still_a_not_found() -> None:
    """The workflow layer reuses this class rather than shadowing it."""
    from pytfe.errors import WORKSPACE_NOT_FOUND_HINT, WorkspaceNotFound

    error = WorkspaceNotFound("missing", hint=WORKSPACE_NOT_FOUND_HINT)
    assert isinstance(error, NotFound)
    assert isinstance(error, TFEError)
    assert error.hint and "find_workspaces" in error.hint


# --------------------------------------------------------------------------
# Cookie policy
#
# The SDK authenticates with a bearer token. A retained Set-Cookie session
# silently overrides that auth and produces 401/404 on later requests, so no
# cookie may survive any request - including the uploads that bypass request().
# --------------------------------------------------------------------------


def _cookie_client() -> tuple[TFEClient, httpx.Client]:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"data": []}, headers={"Set-Cookie": "_atlas_session=abc; Path=/"}
        )

    client = make_client()
    client._transport._sync = httpx.Client(
        transport=httpx.MockTransport(handler),
        event_hooks={
            "request": [client._transport._gate],
            "response": [client._transport._forget_cookies],
        },
    )
    return client, client._transport._sync


def test_cookies_are_dropped_after_a_normal_request() -> None:
    client, sync = _cookie_client()
    try:
        client._transport.request("GET", "/api/v2/organizations")
        assert dict(sync.cookies) == {}
    finally:
        client.close()


def test_cookies_are_dropped_after_a_bypass_upload() -> None:
    """configuration_version/registry uploads call _sync.put directly.

    A custom jar cannot cover this: httpx's Client.cookies setter rewraps
    whatever it is given in a plain Cookies, so a no-store subclass is silently
    discarded. The response hook is what actually holds.
    """
    client, sync = _cookie_client()
    try:
        sync.put("https://archivist.terraform.io/v1/object/abc", content=b"x")
        assert dict(sync.cookies) == {}
    finally:
        client.close()
