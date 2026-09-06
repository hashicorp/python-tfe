# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Package a Terraform directory the way Terraform itself does.

``pytfe.utils.pack_contents`` (used by
:meth:`~pytfe.resources.configuration_version.ConfigurationVersions.upload`)
walks the whole tree with no exclusions, so it would ship ``.git/`` and the
provider binaries under ``.terraform/`` - typically hundreds of megabytes - to
Archivist on every run. This module is the exclusion-aware replacement; upload
its output through the public ``upload_tar_gzip`` method.

Archives are reproducible: members are sorted, and mtime/uid/gid/uname/gname are
fixed, so the same tree always produces byte-identical output.
"""

from __future__ import annotations

import fnmatch
import io
import os
import tarfile
from pathlib import Path, PurePosixPath

__all__ = ["package_directory", "DEFAULT_EXCLUSIONS"]

#: Applied before any ``.terraformignore``, mirroring Terraform's own defaults.
#: ``.terraform/modules/`` is re-included because a configuration can legitimately
#: depend on vendored modules.
DEFAULT_EXCLUSIONS: tuple[str, ...] = (
    ".git/",
    ".terraform/",
    "!.terraform/modules/",
)


class _Rule:
    """One ``.terraformignore`` pattern."""

    __slots__ = ("pattern", "negated", "dir_only", "anchored")

    def __init__(self, raw: str) -> None:
        self.negated = raw.startswith("!")
        if self.negated:
            raw = raw[1:]
        self.dir_only = raw.endswith("/")
        raw = raw.rstrip("/")
        # A pattern containing a slash is anchored to the archive root; one
        # without matches a path component at any depth.
        self.anchored = "/" in raw
        self.pattern = raw.lstrip("/")

    def matches(self, rel: str, is_dir: bool) -> bool:
        if self.dir_only and not is_dir and not self._prefix_of(rel):
            return False
        if self.anchored:
            return self._match_path(rel)
        name = PurePosixPath(rel).name
        if fnmatch.fnmatch(name, self.pattern):
            return True
        return self._match_path(rel)

    def _match_path(self, rel: str) -> bool:
        if fnmatch.fnmatch(rel, self.pattern):
            return True
        # A directory rule also covers everything beneath it.
        return fnmatch.fnmatch(rel, f"{self.pattern}/*")

    def _prefix_of(self, rel: str) -> bool:
        return rel == self.pattern or rel.startswith(f"{self.pattern}/")


def _rules(root: Path, ignore_file: str) -> list[_Rule]:
    raw = list(DEFAULT_EXCLUSIONS)
    path = root / ignore_file
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                raw.append(line)
    return [_Rule(r) for r in raw]


def _excluded(rel: str, is_dir: bool, rules: list[_Rule]) -> bool:
    """Last matching rule wins, so a later ``!pattern`` re-includes."""
    verdict = False
    for rule in rules:
        if rule.matches(rel, is_dir):
            verdict = not rule.negated
    return verdict


def _may_contain_reincluded(rel: str, rules: list[_Rule]) -> bool:
    """True when some negated rule targets a path beneath ``rel``.

    An excluded directory is normally pruned so ``os.walk`` never descends.
    That would make a rule like ``!.terraform/modules/`` unreachable, because
    ``.terraform/`` is pruned first. Descend into such a directory anyway and
    let the per-file check decide.
    """
    prefix = f"{rel}/"
    return any(
        rule.negated and (rule.pattern + "/").startswith(prefix) for rule in rules
    )


def package_directory(
    path: str | os.PathLike[str], *, ignore_file: str = ".terraformignore"
) -> bytes:
    """Package a directory as a gzipped tar, honouring Terraform's exclusions.

    Args:
        path: The configuration directory to package.
        ignore_file: Name of the ignore file to read from ``path``, if present.

    Returns:
        The ``.tar.gz`` bytes, ready for ``upload_tar_gzip``.

    Raises:
        ValueError: If ``path`` is not an existing directory.

    Example:
        >>> import io
        >>> archive = package_directory("./terraform")
        >>> client.configuration_versions.upload_tar_gzip(
        ...     cv.upload_url, io.BytesIO(archive)
        ... )
    """
    root = Path(path)
    if not root.is_dir():
        raise ValueError(
            f"Failed to package {path}: path must be an existing directory"
        )

    rules = _rules(root, ignore_file)
    members: list[tuple[str, Path]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel_dir = here.relative_to(root).as_posix()

        # Prune excluded directories in place so os.walk never descends.
        keep: list[str] = []
        for name in sorted(dirnames):
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            if not _excluded(rel, True, rules) or _may_contain_reincluded(rel, rules):
                keep.append(name)
        dirnames[:] = keep

        for name in sorted(filenames):
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            if _excluded(rel, False, rules):
                continue
            members.append((rel, here / name))

    members.sort(key=lambda item: item[0])

    buf = io.BytesIO()
    # mtime=0 in the gzip header and per-member keeps the archive reproducible.
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        for arcname, full in members:
            info = tar.gettarinfo(str(full), arcname=arcname)
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            if info.isreg():
                with full.open("rb") as handle:
                    tar.addfile(info, handle)
            else:
                tar.addfile(info)
    return buf.getvalue()
