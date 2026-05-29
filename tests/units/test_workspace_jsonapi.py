# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from src.pytfe._jsonapi import build_included_index, parse_relationships
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
        idx = build_included_index(
            [{"type": "runs", "id": "run-x", "attributes": {}}]
        )
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
