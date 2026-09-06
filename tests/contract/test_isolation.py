# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""The workflow layer must build only on the public pytfe surface.

Core (``resources/``, ``models/``, ``client.py``) may one day be regenerated
from an OpenAPI spec. Everything in ``pytfe.workflows`` has to survive that, so
it is forbidden from importing private modules, touching the transport handle
``.t`` or the pagination helper ``._list``, or sleeping outside the one polling
primitive.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "pytfe"
LAYER_DIRS = ["workflows", "agent"]

FORBIDDEN_MODULES = {
    "pytfe._http",
    "pytfe._jsonapi",
    "pytfe.utils",
    "pytfe.client",
    "pytfe._logging",
}
FORBIDDEN_RELATIVE = {"_http", "_jsonapi", "utils", "_logging"}
FORBIDDEN_ATTRS = {"t", "_list", "_sync", "_transport"}
SLEEP_ALLOWED_IN = {"_poll.py"}


def _layer_files() -> list[Path]:
    out: list[Path] = []
    for name in LAYER_DIRS:
        directory = PACKAGE_ROOT / name
        if directory.is_dir():
            out.extend(sorted(directory.rglob("*.py")))
    return out


LAYER_FILES = _layer_files()


def test_layer_is_present() -> None:
    assert LAYER_FILES, "expected at least one module under src/pytfe/workflows"


@pytest.mark.parametrize("path", LAYER_FILES, ids=lambda p: p.name)
def test_no_private_core_imports(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in FORBIDDEN_MODULES, (
                    f"{path.name} imports private core module {alias.name}"
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module not in FORBIDDEN_MODULES, (
                f"{path.name} imports from private core module {module}"
            )
            # Relative imports: `from .._http import ...` has level>0.
            if node.level and module.split(".")[0] in FORBIDDEN_RELATIVE:
                pytest.fail(f"{path.name} imports private core module {module!r}")
            assert not module.startswith("pytfe.resources"), (
                f"{path.name} imports the resource layer directly ({module})"
            )
            if node.level and module.startswith("resources"):
                pytest.fail(f"{path.name} imports the resource layer directly")


@pytest.mark.parametrize("path", LAYER_FILES, ids=lambda p: p.name)
def test_no_transport_or_pager_access(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            pytest.fail(
                f"{path.name}:{node.lineno} accesses .{node.attr} - the workflow "
                "layer must use the public client surface only"
            )


@pytest.mark.parametrize("path", LAYER_FILES, ids=lambda p: p.name)
def test_no_sleep_outside_the_poller(path: Path) -> None:
    if path.name in SLEEP_ALLOWED_IN:
        return
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sleep"
        ):
            pytest.fail(
                f"{path.name}:{node.lineno} calls sleep(); every wait must go "
                "through pytfe.workflows._poll.wait_until"
            )


@pytest.mark.parametrize("path", LAYER_FILES, ids=lambda p: p.name)
def test_no_httpx_dependency(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        assert "httpx" not in names, (
            f"{path.name} imports httpx; the transport already translates errors"
        )


@pytest.mark.parametrize("path", LAYER_FILES, ids=lambda p: p.name)
def test_carries_licence_header(path: Path) -> None:
    head = path.read_text(encoding="utf-8").splitlines()[:2]
    assert head[0].startswith("# Copyright IBM Corp."), path.name
    assert head[1] == "# SPDX-License-Identifier: MPL-2.0", path.name
