# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the public Terraform Registry resource."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidModuleNameError,
    InvalidModuleNamespaceError,
    InvalidModuleProviderError,
    InvalidModuleVersionError,
    RequiredQueryError,
    TFEError,
)
from pytfe.models.registry import (
    PublicRegistryModule,
    PublicRegistryModuleDownloadsSummary,
    PublicRegistryModuleVersions,
    PublicRegistrySearchOptions,
)
from pytfe.resources.registry import DEFAULT_REGISTRY_URL, Registry


class TestRegistry:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Registry(mock_transport)

    @staticmethod
    def _json(payload):
        r = Mock()
        r.json.return_value = payload
        return r

    # ── Construction ──────────────────────────────────────────────────────────

    def test_default_base_url(self, service):
        assert service.base_url == DEFAULT_REGISTRY_URL

    def test_custom_base_url_strips_trailing_slash(self, mock_transport):
        svc = Registry(mock_transport, base_url="https://reg.example.com/")
        assert svc.base_url == "https://reg.example.com"

    # ── list / pagination / auth ──────────────────────────────────────────────

    def test_list_modules_paginates_and_strips_auth(self, service, mock_transport):
        page1 = self._json(
            {"meta": {"next_offset": 2}, "modules": [{"id": "a/b/c/1"}, {"id": "a/b/c/2"}]}
        )
        page2 = self._json({"meta": {}, "modules": [{"id": "a/b/c/3"}]})
        mock_transport.request.side_effect = [page1, page2]

        result = list(service.list_modules("acme"))

        assert [m.id for m in result] == ["a/b/c/1", "a/b/c/2", "a/b/c/3"]
        assert mock_transport.request.call_count == 2
        first = mock_transport.request.call_args_list[0]
        assert first.args == ("GET", "https://registry.terraform.io/v1/modules/acme")
        assert first.kwargs["include_auth"] is False
        assert first.kwargs["headers"] == {"Accept": "application/json"}
        # second page carries the offset from meta.next_offset
        assert mock_transport.request.call_args_list[1].kwargs["params"]["offset"] == 2

    def test_list_modules_no_namespace_uses_root_path(self, service, mock_transport):
        mock_transport.request.return_value = self._json({"meta": {}, "modules": []})
        list(service.list_modules())
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v1/modules",
        )

    def test_list_modules_invalid_namespace(self, service):
        with pytest.raises(InvalidModuleNamespaceError):
            list(service.list_modules("bad namespace"))

    def test_search_requires_query(self, service):
        with pytest.raises(RequiredQueryError):
            list(service.search_modules(""))

    def test_search_sends_q_and_lowercases_bool(self, service, mock_transport):
        mock_transport.request.return_value = self._json({"meta": {}, "modules": []})

        list(
            service.search_modules(
                "vpc", PublicRegistrySearchOptions(provider="aws", verified=True)
            )
        )

        params = mock_transport.request.call_args.kwargs["params"]
        assert params["q"] == "vpc"
        assert params["provider"] == "aws"
        assert params["verified"] == "true"  # bool lowercased for the wire
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v1/modules/search",
        )

    # ── single reads ──────────────────────────────────────────────────────────

    def test_latest_for_provider(self, service, mock_transport):
        mock_transport.request.return_value = self._json(
            {"id": "hashicorp/consul/aws/1.0.0", "name": "consul", "providers": ["aws"]}
        )
        m = service.latest_for_provider("hashicorp", "consul", "aws")
        assert isinstance(m, PublicRegistryModule)
        assert m.id == "hashicorp/consul/aws/1.0.0"
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v1/modules/hashicorp/consul/aws",
        )

    def test_get_module(self, service, mock_transport):
        mock_transport.request.return_value = self._json(
            {"id": "hashicorp/consul/aws/0.0.1"}
        )
        m = service.get_module("hashicorp", "consul", "aws", "0.0.1")
        assert m.version is None and m.id == "hashicorp/consul/aws/0.0.1"
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v1/modules/hashicorp/consul/aws/0.0.1",
        )

    def test_list_versions_returns_first_module(self, service, mock_transport):
        mock_transport.request.return_value = self._json(
            {
                "modules": [
                    {
                        "source": "hashicorp/consul/aws",
                        "versions": [{"version": "0.0.1"}, {"version": "0.0.2"}],
                    }
                ]
            }
        )
        v = service.list_versions("hashicorp", "consul", "aws")
        assert isinstance(v, PublicRegistryModuleVersions)
        assert v.source == "hashicorp/consul/aws"
        assert [x.version for x in v.versions] == ["0.0.1", "0.0.2"]

    def test_list_versions_empty(self, service, mock_transport):
        mock_transport.request.return_value = self._json({"modules": []})
        v = service.list_versions("hashicorp", "consul", "aws")
        assert v.versions == []

    def test_read_invalid_coordinates(self, service):
        with pytest.raises(InvalidModuleNamespaceError):
            service.latest_for_provider("", "consul", "aws")
        with pytest.raises(InvalidModuleNameError):
            service.latest_for_provider("hashicorp", "", "aws")
        with pytest.raises(InvalidModuleProviderError):
            service.latest_for_provider("hashicorp", "consul", "")
        with pytest.raises(InvalidModuleVersionError):
            service.get_module("hashicorp", "consul", "aws", "")

    # ── downloads ─────────────────────────────────────────────────────────────

    def test_download_url_reads_header(self, service, mock_transport):
        resp = Mock()
        resp.headers = {"X-Terraform-Get": "git::https://example.com/repo"}
        mock_transport.request.return_value = resp

        url = service.download_url("hashicorp", "consul", "aws", "0.0.1")

        assert url == "git::https://example.com/repo"
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v1/modules/hashicorp/consul/aws/0.0.1/download",
        )

    def test_latest_download_url_reads_header(self, service, mock_transport):
        resp = Mock()
        resp.headers = {"X-Terraform-Get": "git::https://example.com/repo?ref=v1"}
        mock_transport.request.return_value = resp

        url = service.latest_download_url("hashicorp", "consul", "aws")

        assert url == "git::https://example.com/repo?ref=v1"

    def test_download_url_missing_header_raises(self, service, mock_transport):
        resp = Mock()
        resp.headers = {}
        mock_transport.request.return_value = resp
        with pytest.raises(TFEError):
            service.download_url("hashicorp", "consul", "aws", "0.0.1")

    # ── downloads summary ─────────────────────────────────────────────────────

    def test_downloads_summary(self, service, mock_transport):
        mock_transport.request.return_value = self._json(
            {
                "data": {
                    "type": "module-downloads-summary",
                    "id": "hashicorp/consul/aws",
                    "attributes": {"week": 1, "month": 2, "year": 3, "total": 4},
                }
            }
        )
        s = service.downloads_summary("hashicorp", "consul", "aws")
        assert isinstance(s, PublicRegistryModuleDownloadsSummary)
        assert s.id == "hashicorp/consul/aws"
        assert (s.week, s.month, s.year, s.total) == (1, 2, 3, 4)
        assert mock_transport.request.call_args.args == (
            "GET",
            "https://registry.terraform.io/v2/modules/hashicorp/consul/aws/downloads/summary",
        )
