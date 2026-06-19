# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the discovery helpers (describe / llms_txt) and lifecycle."""

import json

import pytfe
from pytfe import TFEClient, TFEConfig, describe, llms_txt


class TestDescribe:
    """Test the machine-readable API manifest."""

    def test_manifest_shape(self):
        """describe() returns the documented top-level shape."""
        m = describe()
        assert m["sdk"] == "pytfe"
        assert m["client"] == "pytfe.TFEClient"
        assert isinstance(m["version"], str)
        assert isinstance(m["resources"], dict)
        assert m["resource_count"] == len(m["resources"])
        assert m["resource_count"] > 40

    def test_json_serializable(self):
        """The manifest must be JSON-serializable for MCP/tooling consumers."""
        json.dumps(describe())

    def test_core_resources_have_methods_and_signatures(self):
        """Core resources expose verbs with captured signatures + summaries."""
        res = describe()["resources"]
        ws = res["workspaces"]
        assert ws["class"] == "Workspaces"
        assert "list" in ws["methods"]
        assert "read" in ws["methods"]
        read = ws["methods"]["read"]
        assert read["signature"].startswith("(")
        assert read["summary"]  # one-line docstring captured

    def test_admin_namespace_is_nested(self):
        """Grouping namespaces (admin) recurse one level into sub-services."""
        admin = describe()["resources"]["admin"]
        assert admin["class"] == "AdminClient"
        assert "saml_settings" in admin["namespaces"]
        assert admin["namespaces"]["saml_settings"]["methods"]

    def test_no_transport_or_scalar_leak(self):
        """The HTTP transport and plain scalars never appear as resources."""
        m = describe()
        assert "t" not in m["resources"]
        for entry in m["resources"].values():
            assert "t" not in entry.get("namespaces", {})
        # registry holds a plain base_url string that must not become a namespace
        assert "namespaces" not in m["resources"]["registry"]

    def test_makes_no_network_calls(self):
        """describe() must not require a token or perform any I/O."""
        # Running offline with an empty config is enough; absence of an
        # exception here is the assertion.
        assert describe()["resource_count"] > 0


class TestLlmsTxt:
    """Test the packaged llms.txt orientation guide."""

    def test_packaged_and_readable(self):
        """llms_txt() reads the file shipped inside the package."""
        text = llms_txt()
        assert text.startswith("# pytfe")
        assert "TFEClient" in text
        assert "pytfe.describe()" in text
        assert len(text) > 200


class TestExports:
    """The discovery helpers are part of the public API."""

    def test_exported(self):
        assert callable(pytfe.describe)
        assert callable(pytfe.llms_txt)
        assert "describe" in pytfe.__all__
        assert "llms_txt" in pytfe.__all__


class TestClientLifecycle:
    """Context-manager support and idempotent close()."""

    def test_context_manager_returns_client(self):
        with TFEClient(TFEConfig(address="", token="")) as tfe:
            assert isinstance(tfe, TFEClient)

    def test_close_is_idempotent(self):
        tfe = TFEClient(TFEConfig(address="", token=""))
        tfe.close()
        tfe.close()  # second call must not raise
