# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Configuration packaging: exclusions, negation, determinism."""

from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path

import pytest

from pytfe.utils import pack_contents
from pytfe.workflows import package_directory


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
    (tmp_path / ".terraform" / "providers").mkdir(parents=True)
    (tmp_path / ".terraform" / "providers" / "aws").write_bytes(b"\x00" * 128)
    (tmp_path / ".terraform" / "modules").mkdir(parents=True)
    (tmp_path / ".terraform" / "modules" / "modules.json").write_text("{}")
    (tmp_path / "modules" / "vpc").mkdir(parents=True)
    (tmp_path / "modules" / "vpc" / "main.tf").write_text("module")
    (tmp_path / "main.tf").write_text("resource {}")
    (tmp_path / "secrets.auto.tfvars").write_text('token = "hunter2"')
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "notes.md").write_text("notes")
    (tmp_path / ".terraformignore").write_text(
        "# local only\n*.auto.tfvars\nscratch/\n"
    )
    return tmp_path


def _names(archive: bytes) -> list[str]:
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        return sorted(tar.getnames())


def test_excludes_git_and_provider_binaries(tree: Path) -> None:
    names = _names(package_directory(tree))
    assert ".git/HEAD" not in names
    assert ".terraform/providers/aws" not in names
    assert "main.tf" in names
    assert "modules/vpc/main.tf" in names


def test_reincludes_terraform_modules(tree: Path) -> None:
    """Terraform's own default exclusions keep .terraform/modules/."""
    assert ".terraform/modules/modules.json" in _names(package_directory(tree))


def test_honours_terraformignore(tree: Path) -> None:
    names = _names(package_directory(tree))
    assert "secrets.auto.tfvars" not in names
    assert "scratch/notes.md" not in names


def test_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text("x")
    (tmp_path / "keep.txt").write_text("y")
    (tmp_path / ".terraformignore").write_text("\n# keep.txt\n\n")
    assert "keep.txt" in _names(package_directory(tmp_path))


def test_archive_is_reproducible(tree: Path) -> None:
    first = package_directory(tree)
    second = package_directory(tree)
    assert hashlib.sha256(first).digest() == hashlib.sha256(second).digest()


def test_member_metadata_is_normalized(tree: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(package_directory(tree))) as tar:
        for member in tar.getmembers():
            assert member.mtime == 0
            assert member.uid == member.gid == 0
            assert member.uname == member.gname == ""


def test_rejects_a_non_directory(tmp_path: Path) -> None:
    target = tmp_path / "not-a-dir.tf"
    target.write_text("x")
    with pytest.raises(ValueError, match="existing directory"):
        package_directory(target)


def test_improves_on_pack_contents(tree: Path) -> None:
    """The reason this module exists at all.

    utils.pack_contents ships .git/, provider binaries and any *.auto.tfvars
    secrets file. Uploading that to Archivist on every run is the bug the
    workflow layer must not inherit.
    """
    legacy = sorted(tarfile.open(fileobj=pack_contents(str(tree))).getnames())
    assert ".git/HEAD" in legacy
    assert ".terraform/providers/aws" in legacy
    assert "secrets.auto.tfvars" in legacy

    ours = _names(package_directory(tree))
    assert not {".git/HEAD", ".terraform/providers/aws", "secrets.auto.tfvars"} & set(
        ours
    )
