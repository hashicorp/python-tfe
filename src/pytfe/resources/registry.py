# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Client for the **public** Terraform Registry module API.

``client.registry`` talks to the public Terraform Registry at
``registry.terraform.io`` (host configurable via ``base_url``). It implements
the [module registry protocol](https://developer.hashicorp.com/terraform/internals/module-registry-protocol)
plus HashiCorp's documented discovery extensions: listing and searching modules
across the whole registry, reading a module's metadata/inputs/outputs/versions,
resolving a version's download source, and reading download metrics.

This API is **unauthenticated** and lives on a different host from the HCP
Terraform / Terraform Enterprise V2 API, so the SDK never sends the bearer token
to the registry.

It is distinct from the SDK's *private* registry resources
(``client.registry_modules``, ``client.registry_providers``,
``client.registry_provider_versions``, ``client.registry_provider_platforms``),
which manage the private registry included in your HCP Terraform / Terraform
Enterprise organization via the authenticated, JSON:API ``/api/v2/registry-*``
endpoints (publish, update, delete, add versions).

Public Registry API reference:
https://developer.hashicorp.com/terraform/registry/api-docs
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._http import HTTPTransport
from ..errors import (
    InvalidModuleNameError,
    InvalidModuleNamespaceError,
    InvalidModuleProviderError,
    InvalidModuleVersionError,
    RequiredQueryError,
    TFEError,
)
from ..models.registry import (
    PublicRegistryModule,
    PublicRegistryModuleDownloadsSummary,
    PublicRegistryModuleListOptions,
    PublicRegistryModuleVersions,
    PublicRegistrySearchOptions,
)
from ..utils import valid_string, valid_string_id
from ._base import _Service

DEFAULT_REGISTRY_URL = "https://registry.terraform.io"


def _query_params(options: Any) -> dict[str, Any]:
    """Dump option models to query params, lowercasing bools (``verified=true``)."""
    if options is None:
        return {}
    dumped = options.model_dump(by_alias=True, exclude_none=True, mode="json")
    return {
        k: (str(v).lower() if isinstance(v, bool) else v) for k, v in dumped.items()
    }


class Registry(_Service):
    """Client for the public Terraform Registry module API.

    Targets ``registry.terraform.io`` by default; set ``base_url`` to point at
    another registry that implements the
    [module registry protocol](https://developer.hashicorp.com/terraform/internals/module-registry-protocol).
    This API is unauthenticated — the HCP Terraform/TFE bearer token is never
    sent to the registry host.
    """

    def __init__(self, t: HTTPTransport, base_url: str | None = None) -> None:
        super().__init__(t)
        self.base_url = (base_url or DEFAULT_REGISTRY_URL).rstrip("/")

    def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        allow_redirects: bool = True,
    ) -> Any:
        return self.t.request(
            "GET",
            f"{self.base_url}{path}",
            params=params,
            headers={"Accept": "application/json"},
            include_auth=False,
            allow_redirects=allow_redirects,
        )

    def _paginate(
        self, path: str, params: dict[str, Any]
    ) -> Iterator[PublicRegistryModule]:
        p = dict(params)
        while True:
            body = self._get(path, params=p).json()
            if not isinstance(body, dict):
                return
            for item in body.get("modules") or []:
                yield PublicRegistryModule.model_validate(item)
            meta = body.get("meta") or {}
            next_offset = meta.get("next_offset") if isinstance(meta, dict) else None
            if next_offset is None:
                return
            p["offset"] = next_offset

    def list_modules(
        self,
        namespace: str | None = None,
        options: PublicRegistryModuleListOptions | None = None,
    ) -> Iterator[PublicRegistryModule]:
        """List registry modules, optionally restricted to a ``namespace``."""
        if namespace is not None and not valid_string_id(namespace):
            raise InvalidModuleNamespaceError()
        path = f"/v1/modules/{namespace}" if namespace else "/v1/modules"
        yield from self._paginate(path, _query_params(options))

    def search_modules(
        self, query: str, options: PublicRegistrySearchOptions | None = None
    ) -> Iterator[PublicRegistryModule]:
        """Search registry modules by keyword/phrase (``q``)."""
        if not valid_string(query):
            raise RequiredQueryError()
        params = _query_params(options)
        params["q"] = query
        yield from self._paginate("/v1/modules/search", params)

    def list_latest_for_all_providers(
        self,
        namespace: str,
        name: str,
        options: PublicRegistryModuleListOptions | None = None,
    ) -> Iterator[PublicRegistryModule]:
        """List the latest version of a module for each of its providers."""
        self._validate(namespace, name)
        yield from self._paginate(
            f"/v1/modules/{namespace}/{name}", _query_params(options)
        )

    def latest_for_provider(
        self, namespace: str, name: str, provider: str
    ) -> PublicRegistryModule:
        """Read the latest version of a module for a single provider."""
        self._validate(namespace, name, provider)
        body = self._get(f"/v1/modules/{namespace}/{name}/{provider}").json()
        return PublicRegistryModule.model_validate(body)

    def get_module(
        self, namespace: str, name: str, provider: str, version: str
    ) -> PublicRegistryModule:
        """Read a specific version of a module for a single provider."""
        self._validate(namespace, name, provider, version)
        body = self._get(f"/v1/modules/{namespace}/{name}/{provider}/{version}").json()
        return PublicRegistryModule.model_validate(body)

    def list_versions(
        self, namespace: str, name: str, provider: str
    ) -> PublicRegistryModuleVersions:
        """List the available versions for a fully-qualified module.

        Returns the requested module (the API always lists it first); any
        dependency modules the registry also returns are not included.
        """
        self._validate(namespace, name, provider)
        body = self._get(f"/v1/modules/{namespace}/{name}/{provider}/versions").json()
        modules = (body or {}).get("modules") or [] if isinstance(body, dict) else []
        if not modules:
            return PublicRegistryModuleVersions()
        return PublicRegistryModuleVersions.model_validate(modules[0])

    def download_url(
        self, namespace: str, name: str, provider: str, version: str
    ) -> str:
        """Return a module version's source location (the ``X-Terraform-Get`` value).

        The value is a go-getter URL string, not the archive bytes.
        """
        self._validate(namespace, name, provider, version)
        resp = self._get(
            f"/v1/modules/{namespace}/{name}/{provider}/{version}/download"
        )
        return self._x_terraform_get(resp)

    def latest_download_url(self, namespace: str, name: str, provider: str) -> str:
        """Return the latest version's source location (``X-Terraform-Get``).

        The endpoint 302-redirects to the versioned download; the redirect is
        followed automatically.
        """
        self._validate(namespace, name, provider)
        resp = self._get(f"/v1/modules/{namespace}/{name}/{provider}/download")
        return self._x_terraform_get(resp)

    def downloads_summary(
        self, namespace: str, name: str, provider: str
    ) -> PublicRegistryModuleDownloadsSummary:
        """Read a module's download metrics summary (week/month/year/total)."""
        self._validate(namespace, name, provider)
        body = self._get(
            f"/v2/modules/{namespace}/{name}/{provider}/downloads/summary"
        ).json()
        data = (body or {}).get("data") or {} if isinstance(body, dict) else {}
        attrs = dict(data.get("attributes") or {})
        attrs["id"] = data.get("id")
        return PublicRegistryModuleDownloadsSummary.model_validate(attrs)

    @staticmethod
    def _x_terraform_get(resp: Any) -> str:
        source = resp.headers.get("X-Terraform-Get")
        if not source:
            raise TFEError(
                "registry download response did not include an X-Terraform-Get header"
            )
        return str(source)

    @staticmethod
    def _validate(
        namespace: str,
        name: str,
        provider: str | None = None,
        version: str | None = None,
    ) -> None:
        if not valid_string_id(namespace):
            raise InvalidModuleNamespaceError()
        if not valid_string_id(name):
            raise InvalidModuleNameError()
        if provider is not None and not valid_string_id(provider):
            raise InvalidModuleProviderError()
        if version is not None and not valid_string_id(version):
            raise InvalidModuleVersionError()
