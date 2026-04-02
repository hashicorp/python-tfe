#!/usr/bin/env bash
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

set -euo pipefail


PYPI_REPO="${PYPI_REPO:-testpypi}"     # "pypi" or "testpypi"
PYPI_TOKEN="${PYPI_TOKEN:-}"       # export PYPI_TOKEN="pypi-***" (or test token)
PYTHON="${PYTHON:-python}"         # "python" or "python3"
DIST_DIR="dist"
PYPROJECT="pyproject.toml"


if [[ ! -f "$PYPROJECT" ]]; then
  echo "$PYPROJECT not found (are you in the project root?)"
  exit 1
fi

if [[ -z "$PYPI_TOKEN" ]]; then
  echo "PYPI_TOKEN not set. Run: export PYPI_TOKEN='pypi-XXXX...'"
  exit 1
fi

# Read project metadata (name & version) from pyproject.toml using Python
read_pyproject() {
  "$PYTHON" - <<'PY'
import sys, pathlib
pp = pathlib.Path("pyproject.toml")
if not pp.exists():
    print("unknown|unknown"); sys.exit(0)
try:
    import tomllib
except ModuleNotFoundError:
    # Python <3.11 fallback
    import json, re
    # very small fallback parser: good enough to grab name/version in simple cases
    text = pp.read_text()
    name = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"', text)
    ver  = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
    print(f"{name.group(1) if name else 'unknown'}|{ver.group(1) if ver else 'unknown'}")
    sys.exit(0)

data = tomllib.loads(pp.read_bytes())
proj = data.get("project", {})
print(f"{proj.get('name','unknown')}|{proj.get('version','unknown')}")
PY
}

IFS="|" read -r PKG_NAME PKG_VER < <(read_pyproject)
echo "Package: ${PKG_NAME}  Version: ${PKG_VER}"


echo "Cleaning old builds..."
rm -rf "$DIST_DIR" build ./*.egg-info


echo "Installing build tools..."
$PYTHON -m pip install -q --upgrade pip build twine

echo "Building sdist & wheel..."
$PYTHON -m build  # uses hatchling per your [build-system]

echo "Validating with twine..."
$PYTHON -m twine check "$DIST_DIR"/*


if [[ "$PYPI_REPO" == "testpypi" ]]; then
  REPO_URL="https://test.pypi.org/legacy/"
  echo "Target: TestPyPI"
else
  REPO_URL="https://upload.pypi.org/legacy/"
  echo "Target: PyPI"
fi

# -----------------------------
# Upload
# -----------------------------
echo "Uploading distributions..."
$PYTHON -m twine upload \
  --non-interactive \
  --repository-url "$REPO_URL" \
  -u __token__ \
  -p "$PYPI_TOKEN" \
  "$DIST_DIR"/*

echo "Published ${PKG_NAME} ${PKG_VER} to ${PYPI_REPO}"
