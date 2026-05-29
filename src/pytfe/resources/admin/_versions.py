# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from ...errors import ERR_INVALID_VERSION
from ...models.admin_version import (
    OpaVersion,
    OpaVersionCreateOptions,
    OpaVersionUpdateOptions,
    SentinelVersion,
    SentinelVersionCreateOptions,
    SentinelVersionUpdateOptions,
    TerraformVersion,
    TerraformVersionCreateOptions,
    TerraformVersionUpdateOptions,
)
from ...utils import valid_string_id
from .._base import _Service

_TF_VERSION_TYPE = "terraform-versions"
_OPA_VERSION_TYPE = "opa-versions"
_SENTINEL_VERSION_TYPE = "sentinel-versions"


def _parse_terraform_version(data: dict[str, Any]) -> TerraformVersion:
    attrs = data.get("attributes") or {}
    return TerraformVersion.model_validate({"id": data.get("id"), **attrs})


def _parse_opa_version(data: dict[str, Any]) -> OpaVersion:
    attrs = data.get("attributes") or {}
    return OpaVersion.model_validate({"id": data.get("id"), **attrs})


def _parse_sentinel_version(data: dict[str, Any]) -> SentinelVersion:
    attrs = data.get("attributes") or {}
    return SentinelVersion.model_validate({"id": data.get("id"), **attrs})


class _AdminTerraformVersions(_Service):
    def list(self) -> Iterator[TerraformVersion]:
        for item in self._list("/api/v2/admin/terraform-versions"):
            yield _parse_terraform_version(item)

    def read(self, version_id: str) -> TerraformVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/terraform-versions/{version_id}")
        return _parse_terraform_version(r.json()["data"])

    def create(self, options: TerraformVersionCreateOptions) -> TerraformVersion:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _TF_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/terraform-versions", json_body=body)
        return _parse_terraform_version(r.json()["data"])

    def update(self, version_id: str, options: TerraformVersionUpdateOptions) -> TerraformVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _TF_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/terraform-versions/{version_id}", json_body=body
        )
        return _parse_terraform_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/terraform-versions/{version_id}")


class _AdminOpaVersions(_Service):
    def list(self) -> Iterator[OpaVersion]:
        for item in self._list("/api/v2/admin/opa-versions"):
            yield _parse_opa_version(item)

    def read(self, version_id: str) -> OpaVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/opa-versions/{version_id}")
        return _parse_opa_version(r.json()["data"])

    def create(self, options: OpaVersionCreateOptions) -> OpaVersion:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _OPA_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/opa-versions", json_body=body)
        return _parse_opa_version(r.json()["data"])

    def update(self, version_id: str, options: OpaVersionUpdateOptions) -> OpaVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _OPA_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/opa-versions/{version_id}", json_body=body
        )
        return _parse_opa_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/opa-versions/{version_id}")


class _AdminSentinelVersions(_Service):
    def list(self) -> Iterator[SentinelVersion]:
        for item in self._list("/api/v2/admin/sentinel-versions"):
            yield _parse_sentinel_version(item)

    def read(self, version_id: str) -> SentinelVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        r = self.t.request("GET", f"/api/v2/admin/sentinel-versions/{version_id}")
        return _parse_sentinel_version(r.json()["data"])

    def create(self, options: SentinelVersionCreateOptions) -> SentinelVersion:
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SENTINEL_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request("POST", "/api/v2/admin/sentinel-versions", json_body=body)
        return _parse_sentinel_version(r.json()["data"])

    def update(self, version_id: str, options: SentinelVersionUpdateOptions) -> SentinelVersion:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
        body = {"data": {"type": _SENTINEL_VERSION_TYPE, "attributes": attrs}}
        r = self.t.request(
            "PATCH", f"/api/v2/admin/sentinel-versions/{version_id}", json_body=body
        )
        return _parse_sentinel_version(r.json()["data"])

    def delete(self, version_id: str) -> None:
        if not valid_string_id(version_id):
            raise ValueError(ERR_INVALID_VERSION)
        self.t.request("DELETE", f"/api/v2/admin/sentinel-versions/{version_id}")
