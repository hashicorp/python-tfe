# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

project = 'pytfe'
copyright = 'IBM Corp. 2025, 2026'
author = 'HashiCorp, an IBM Corp.'
release = '0.1.4'
version = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

autosummary_generate = True
autosummary_generate_overwrite = False

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "exclude-members": "__weakref__, __dict__, __module__, __annotations__",
}

autodoc_typehints = "description"
autodoc_typehints_format = "short"

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True

always_document_param_types = True
typehints_fully_qualified = False
simplify_optional_unions = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "httpx": ("https://www.python-httpx.org/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

myst_enable_extensions = ["colon_fence", "deflist", "tasklist"]
myst_heading_anchors = 3

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_with_keys": True,
    "source_repository": "https://github.com/hashicorp/python-tfe",
    "source_branch": "sphinx-docs",
    "source_directory": "docs/source/",
}
html_static_path = ["_static"]
html_title = f"pyTFE {release}"