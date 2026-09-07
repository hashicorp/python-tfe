# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Sensitive-value removal from Terraform state.

Raw state holds provider credentials, generated passwords and private keys in
plain text. These tests are the guarantee that none of it survives a
``download_state`` or a ``state_inventory``.
"""

from __future__ import annotations

import json
from typing import Any

from pytfe.workflows import redact_attributes, redact_state

SECRET = "hunter2"


def state_with(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "version": 4,
        "outputs": {
            "vpc_id": {"value": "vpc-123", "type": "string"},
            "db_conn": {"value": f"postgres://u:{SECRET}@h/db", "sensitive": True},
        },
        "resources": [
            {
                "mode": "managed",
                "type": "aws_db_instance",
                "name": "main",
                "provider": 'provider["registry.terraform.io/hashicorp/aws"]',
                "instances": [
                    {
                        "attributes": {
                            "id": "db-1",
                            "username": "admin",
                            "password": SECRET,
                            "endpoint": "host:5432",
                        },
                        "sensitive_attributes": [
                            [{"type": "get_attr", "value": "password"}]
                        ],
                    }
                ],
            }
        ],
    }
    base.update(kw)
    return base


def test_removes_flagged_attributes() -> None:
    clean, removed = redact_state(state_with())
    attrs = clean["resources"][0]["instances"][0]["attributes"]
    assert "password" not in attrs
    assert attrs["username"] == "admin"
    assert removed == ["aws_db_instance.main.password", "output.db_conn"]


def test_no_secret_survives_anywhere() -> None:
    clean, _ = redact_state(state_with())
    assert SECRET not in json.dumps(clean)


def test_redacts_sensitive_root_outputs() -> None:
    """The Ansible collection's version walks resources only, so a sensitive
    root output keeps its value. This closes that."""
    clean, removed = redact_state(state_with())
    assert "value" not in clean["outputs"]["db_conn"]
    assert clean["outputs"]["vpc_id"]["value"] == "vpc-123"
    assert "output.db_conn" in removed


def test_clears_the_marker_after_redacting() -> None:
    """Leaving the marker would make a second pass look like it found new
    secrets, and the values it points at are already gone."""
    clean, _ = redact_state(state_with())
    assert "sensitive_attributes" not in clean["resources"][0]["instances"][0]


def test_does_not_mutate_the_input() -> None:
    original = state_with()
    redact_state(original)
    assert original["resources"][0]["instances"][0]["attributes"]["password"] == SECRET


def test_list_index_drops_the_owning_attribute() -> None:
    """Deleting one list element shifts the indices later sensitive paths refer
    to, which would strand a second secret. The whole attribute goes instead."""
    attrs, removed = redact_attributes(
        {"creds": ["secret-a", "secret-b"], "name": "keep"},
        [
            [
                {"type": "get_attr", "value": "creds"},
                {"type": "index", "value": 0},
            ]
        ],
    )
    assert "creds" not in attrs
    assert attrs["name"] == "keep"
    assert removed == ["creds[0]"]


def test_nested_map_key_is_removed_precisely() -> None:
    attrs, _ = redact_attributes(
        {"config": {"token": "s3cret", "region": "eu-west-1"}},
        [
            [
                {"type": "get_attr", "value": "config"},
                {"type": "index", "value": "token"},
            ]
        ],
    )
    assert attrs["config"] == {"region": "eu-west-1"}


def test_unwalkable_path_falls_back_to_the_top_level() -> None:
    """An ambiguous path must never leave the value in place."""
    attrs, removed = redact_attributes(
        {"config": {"token": "s3cret"}},
        [
            [
                {"type": "get_attr", "value": "config"},
                {"type": "get_attr", "value": "not_there"},
                {"type": "get_attr", "value": "deeper"},
            ]
        ],
    )
    assert "config" not in attrs
    assert removed == ["config.not_there.deeper"]


def test_malformed_paths_are_ignored_safely() -> None:
    attrs, removed = redact_attributes({"a": 1}, [[], "nonsense", None])
    assert attrs == {"a": 1}
    assert removed == []


def test_empty_and_missing_structures() -> None:
    assert redact_state({}) == ({}, [])
    assert redact_state({"resources": None, "outputs": None})[1] == []
    assert redact_attributes({}, []) == ({}, [])
