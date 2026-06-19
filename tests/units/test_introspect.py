# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the discovery helpers (describe / llms_txt) and lifecycle."""

import json

import pytfe
from pytfe import TFEClient, TFEConfig, describe, llms_txt, tool_schemas


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


class TestToolSchemas:
    """Test the MCP-style tool-schema generator."""

    def test_returns_tool_specs(self):
        """tool_schemas() returns a non-empty list of well-formed specs."""
        tools = tool_schemas()
        assert isinstance(tools, list)
        assert len(tools) > 100
        sample = tools[0]
        for key in ("name", "resource", "method", "description", "input_schema"):
            assert key in sample
        assert sample["input_schema"]["type"] == "object"

    def test_json_serializable(self):
        """Specs must be JSON-serializable for MCP/tooling consumers."""
        json.dumps(tool_schemas())

    def test_identifiers_and_options_composed(self):
        """A create method exposes its id args plus the embedded *Options schema."""
        byname = {t["name"]: t for t in tool_schemas()}
        create = byname["workspaces.create"]
        props = create["input_schema"]["properties"]
        assert set(create["input_schema"]["required"]) == {"organization", "options"}
        assert props["organization"] == {"type": "string"}
        # the WorkspaceCreateOptions Pydantic model is embedded as JSON Schema
        options_schema = props["options"]
        assert options_schema.get("type") == "object"
        assert "properties" in options_schema or "$ref" in options_schema

    def test_optional_param_not_required(self):
        """A param with a default (e.g. options=None on list) is not required."""
        byname = {t["name"]: t for t in tool_schemas()}
        list_tool = byname["workspaces.list"]
        required = list_tool["input_schema"].get("required", [])
        assert "organization" in required
        assert "options" not in required

    def test_nested_admin_dotted_names(self):
        """Grouping namespaces produce dotted tool names with the top resource."""
        admin = [t for t in tool_schemas() if t["name"].startswith("admin.")]
        assert admin
        assert all(t["resource"] == "admin" for t in admin)
        assert all(t["name"].count(".") >= 2 for t in admin)

    def test_resource_filter(self):
        """The resources filter limits output to the named namespaces."""
        only = tool_schemas(resources={"workspaces"})
        assert only
        assert all(t["resource"] == "workspaces" for t in only)
        assert len(only) < len(tool_schemas())

    def test_schemas_are_self_contained(self):
        """Input schemas must be fully inlined: no $ref/$defs.

        LLM tool-calling layers behind many MCP clients reject `$ref`/`$defs`,
        so every embedded model must be inlined into a self-contained schema.
        """

        def _has_key(node, key):
            if isinstance(node, dict):
                if key in node:
                    return True
                return any(_has_key(v, key) for v in node.values())
            if isinstance(node, list):
                return any(_has_key(item, key) for item in node)
            return False

        for spec in tool_schemas():
            schema = spec["input_schema"]
            assert not _has_key(schema, "$ref"), f"$ref left in {spec['name']}"
            assert not _has_key(schema, "$defs"), f"$defs left in {spec['name']}"


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
        assert callable(pytfe.tool_schemas)
        assert "describe" in pytfe.__all__
        assert "llms_txt" in pytfe.__all__
        assert "tool_schemas" in pytfe.__all__


class TestClientLifecycle:
    """Context-manager support and idempotent close()."""

    def test_context_manager_returns_client(self):
        with TFEClient(TFEConfig(address="", token="")) as tfe:
            assert isinstance(tfe, TFEClient)

    def test_close_is_idempotent(self):
        tfe = TFEClient(TFEConfig(address="", token=""))
        tfe.close()
        tfe.close()  # second call must not raise
