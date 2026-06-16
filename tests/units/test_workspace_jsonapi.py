# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from src.pytfe._jsonapi import attach_jsonapi, build_included_index, parse_relationships
from src.pytfe.models.run import Run, RunStatus
from src.pytfe.resources.workspaces import _ws_from


def _ws_payload(**overrides):
    attrs = {
        "name": "demo",
        "latest-change-at": "2026-05-28T16:35:06.718Z",
        "last-assessment-result-at": None,
        "locked-reason": "",
        "project-remote-state": False,
        "unarchived-workspace-change-requests-count": 0,
        "workspace-kpis-runs-count": 3,
    }
    attrs.update(overrides.pop("attributes", {}))
    data = {"id": "ws-1", "type": "workspaces", "attributes": attrs}
    data["relationships"] = overrides.pop("relationships", {})
    return data


class TestNewTypedFields:
    def test_new_attributes_parse_with_correct_types(self):
        ws = _ws_from(_ws_payload())
        assert isinstance(ws.latest_change_at, datetime)
        assert ws.last_assessment_result_at is None
        assert ws.locked_reason == ""
        assert ws.project_remote_state is False
        assert ws.unarchived_workspace_change_requests_count == 0
        # aliased KPI field still maps despite the divergent snake/hyphen names
        assert ws.runs_count == 3

    def test_source_module_id_parses_for_no_code_workspace(self):
        # #179: no-code workspaces carry source-module-id; it must be a typed
        # attribute, not buried in model_extra under the hyphenated wire key.
        ws = _ws_from(_ws_payload(attributes={"source-module-id": "mod-ABC123"}))
        assert ws.source_module_id == "mod-ABC123"
        assert "source-module-id" not in (ws.model_extra or {})
        # absent on a normal workspace -> None, never an error
        assert _ws_from(_ws_payload()).source_module_id is None


class TestForwardCompat:
    def test_unknown_attribute_survives_in_model_extra(self):
        ws = _ws_from(_ws_payload(attributes={"future-field": "keepme"}))
        assert ws.model_extra is not None
        assert ws.model_extra.get("future-field") == "keepme"

    def test_no_spurious_extra_for_known_nested_objects(self):
        ws = _ws_from(
            _ws_payload(attributes={"setting-overwrites": {"execution-mode": True}})
        )
        # setting_overwrites is typed, must not leak into model_extra
        assert "setting_overwrites" not in (ws.model_extra or {})
        assert ws.setting_overwrites is not None
        assert ws.setting_overwrites.execution_mode is True


class TestRelations:
    def test_latest_run_relation_populates(self):
        rels = {
            "current-run": {"data": {"id": "run-x", "type": "runs"}},
            "latest-run": {"data": {"id": "run-x", "type": "runs"}},
        }
        ws = _ws_from(_ws_payload(relationships=rels))
        assert ws.current_run is not None and ws.latest_run is not None
        # latest-run mirrors current-run (deprecated alias)
        assert ws.latest_run.id == ws.current_run.id == "run-x"

    def test_remote_state_consumers_list_relation(self):
        rels = {
            "remote-state-consumers": {
                "data": [
                    {"id": "ws-a", "type": "workspaces"},
                    {"id": "ws-b", "type": "workspaces"},
                ]
            }
        }
        ws = _ws_from(_ws_payload(relationships=rels))
        assert [c.id for c in ws.remote_state_consumers] == ["ws-a", "ws-b"]

    def test_null_relation_leaves_default(self):
        ws = _ws_from(_ws_payload(relationships={"current-run": {"data": None}}))
        assert ws.current_run is None


class TestIncludedHydration:
    def test_included_hydrates_full_object(self):
        rels = {"current-run": {"data": {"id": "run-x", "type": "runs"}}}
        included = [
            {
                "id": "run-x",
                "type": "runs",
                "attributes": {"status": "applied", "has-changes": True},
            }
        ]
        ws = _ws_from(_ws_payload(relationships=rels), included)
        assert ws.current_run.status == RunStatus.Run_Applied
        assert ws.current_run.has_changes is True

    def test_without_included_falls_back_to_stub(self):
        rels = {"current-run": {"data": {"id": "run-x", "type": "runs"}}}
        ws = _ws_from(_ws_payload(relationships=rels), included=None)
        assert ws.current_run.id == "run-x"
        assert ws.current_run.status is None


class TestSharedHelper:
    def test_build_included_index_keys_by_type_and_id(self):
        idx = build_included_index([{"type": "runs", "id": "run-x", "attributes": {}}])
        assert ("runs", "run-x") in idx

    def test_build_included_index_dedupes_first_wins(self):
        idx = build_included_index(
            [
                {"type": "runs", "id": "run-x", "attributes": {"status": "applied"}},
                {"type": "runs", "id": "run-x", "attributes": {"status": "errored"}},
            ]
        )
        assert idx[("runs", "run-x")]["attributes"]["status"] == "applied"

    def test_parse_relationships_skips_unmapped_and_null(self):
        rel_map = {"current-run": ("current_run", Run)}
        out = parse_relationships(
            {
                "current-run": {"data": {"id": "run-x", "type": "runs"}},
                "unmapped": {"data": {"id": "x", "type": "y"}},
                "nullable": {"data": None},
            },
            rel_map,
        )
        assert set(out) == {"current_run"}
        assert out["current_run"].id == "run-x"


class TestOutputsInclude:
    """python-tfe#134: ?include=outputs must hydrate name/value/type from the
    `included` array, not leave id-only stubs."""

    def _payload(self):
        return _ws_payload(
            relationships={
                "outputs": {
                    "data": [
                        {"id": "wsout-1", "type": "workspace-outputs"},
                        {"id": "wsout-2", "type": "workspace-outputs"},
                    ]
                }
            }
        )

    def test_outputs_hydrated_from_included(self):
        included = [
            {
                "id": "wsout-1",
                "type": "workspace-outputs",
                "attributes": {
                    "name": "public_ip",
                    "value": "1.2.3.4",
                    "output-type": "string",
                    "sensitive": False,
                },
            },
            {
                "id": "wsout-2",
                "type": "workspace-outputs",
                "attributes": {
                    "name": "host",
                    "value": {"role": "web"},  # object output -> dict value
                    "output-type": "object",
                    "sensitive": True,
                },
            },
        ]
        ws = _ws_from(self._payload(), included)
        assert [o.name for o in ws.outputs] == ["public_ip", "host"]
        assert ws.outputs[0].value == "1.2.3.4"
        assert ws.outputs[0].output_type == "string"
        # object/list values pass through unchanged (value is typed Any)
        assert ws.outputs[1].value == {"role": "web"}
        assert ws.outputs[1].output_type == "object"
        assert ws.outputs[1].sensitive is True

    def test_outputs_without_included_fall_back_to_id_stubs(self):
        ws = _ws_from(self._payload(), included=None)
        assert [o.id for o in ws.outputs] == ["wsout-1", "wsout-2"]
        assert all(o.name is None and o.value is None for o in ws.outputs)


class TestLosslessIncluded:
    """Raw `included` is retained even for relations the SDK does not model, and
    never leaks into model_dump() (TFEModel escape hatch)."""

    def test_unmapped_include_reachable_via_included_by(self):
        data = {
            "id": "ws-x",
            "type": "workspaces",
            "attributes": {"name": "demo"},
            "relationships": {
                "readme": {"data": {"id": "rm-1", "type": "workspace-readme"}}
            },
        }
        included = [
            {
                "id": "rm-1",
                "type": "workspace-readme",
                "attributes": {"raw-markdown": "# Hello"},
            }
        ]
        ws = _ws_from(data, included)
        # readme is not a modelled relation -> no typed attribute ...
        assert not hasattr(ws, "readme")
        # ... but it is still reachable raw, losslessly.
        got = ws.included_by("workspace-readme", "rm-1")
        assert got["attributes"]["raw-markdown"] == "# Hello"
        assert len(ws.included) == 1

    def test_included_never_appears_in_model_dump(self):
        ws = _ws_from(
            _ws_payload(),
            [{"id": "x", "type": "y", "attributes": {"k": "v"}}],
        )
        dumped = ws.model_dump()
        assert "included" not in dumped
        assert "_included" not in dumped

    def test_no_included_is_empty(self):
        ws = _ws_from(_ws_payload())
        assert ws.included == []
        assert ws.included_by("any", "thing") is None

    def test_relationships_block_and_related_resolution(self):
        data = {
            "id": "ws-x",
            "type": "workspaces",
            "attributes": {"name": "demo"},
            "relationships": {
                "current-run": {"data": {"id": "run-1", "type": "runs"}},
                "readme": {"data": {"id": "rm-1", "type": "workspace-readme"}},
            },
        }
        included = [
            {
                "id": "rm-1",
                "type": "workspace-readme",
                "attributes": {"raw-markdown": "hi"},
            }
        ]
        ws = _ws_from(data, included)
        # raw relationships block is captured for every relation
        assert "current-run" in ws.relationships
        assert "readme" in ws.relationships
        # related() resolves to the full body when included ...
        assert ws.related("readme")[0]["attributes"]["raw-markdown"] == "hi"
        # ... and falls back to the bare {type,id} ref when not included
        assert ws.related("current-run") == [{"id": "run-1", "type": "runs"}]
        # neither block leaks into model_dump()
        assert "relationships" not in ws.model_dump()


class TestPresenceTracking:
    """has_relationships / has_included distinguish 'absent on wire' from
    'present but empty', without making the data accessors disappear."""

    def _obj(self):
        return Run.model_validate({"id": "run-1"})

    def test_relationships_present_absent_empty(self):
        present = attach_jsonapi(
            self._obj(),
            {"id": "r", "relationships": {"workspace": {"data": {"id": "ws"}}}},
        )
        assert present.has_relationships is True and present.relationships != {}

        empty = attach_jsonapi(self._obj(), {"id": "r", "relationships": {}})
        assert empty.has_relationships is True and empty.relationships == {}

        absent = attach_jsonapi(self._obj(), {"id": "r", "attributes": {}})
        assert absent.has_relationships is False and absent.relationships == {}

    def test_included_present_absent_empty(self):
        present = attach_jsonapi(self._obj(), {"id": "r"}, [{"id": "x", "type": "y"}])
        assert present.has_included is True and len(present.included) == 1

        empty = attach_jsonapi(self._obj(), {"id": "r"}, [])
        assert empty.has_included is True and empty.included == []

        absent = attach_jsonapi(self._obj(), {"id": "r"}, None)
        assert absent.has_included is False and absent.included == []

    def test_default_instance_reports_absent(self):
        o = self._obj()  # not built via attach_jsonapi
        assert o.has_relationships is False and o.has_included is False
        assert o.relationships == {} and o.included == []
