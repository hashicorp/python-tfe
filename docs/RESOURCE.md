# Resources — adding a new resource to pyTFE

This is internal reference for adding or editing resource services in `src/pytfe/resources/`. A "resource" here is a service class like `Workspaces`, `Comments`, `TeamWorkspaceAccesses` — it wraps a related set of HCP Terraform API endpoints. The patterns below reflect what the codebase already does. Follow them.

Companion docs you'll need alongside this one:

- [MODELS.md](MODELS.md) — how to define the Pydantic models the resource takes and returns
- [ITERATORS.md](ITERATORS.md) — how `list_*` methods are shaped
- The [examples/](../examples) directory — runnable demos for each resource

## What a resource file looks like

One file per resource in `src/pytfe/resources/`, named after the resource (`workspaces.py`, `policy_set.py`, `team_workspace_access.py`). The class inside is the plural form (`Workspaces`, `PolicySets`, `TeamWorkspaceAccesses`).

Every resource class inherits from `_Service` (in `_base.py`), which gives it:

- `self.t` — the `HTTPTransport` for making requests
- `self._list(path, params=...)` — the paginated iterator helper (see [ITERATORS.md](ITERATORS.md))

Standard file scaffolding:

```python
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import InvalidWorkspaceIDError, InvalidOrgError
from ..models.widget import Widget, WidgetCreateOptions, WidgetListOptions
from ..utils import valid_string_id
from ._base import _Service


class Widgets(_Service):
    """Service for managing widgets."""

    def list(self) -> Iterator[Widget]: ...
    def read(self, widget_id: str) -> Widget: ...
    def create(self, organization: str, options: WidgetCreateOptions) -> Widget: ...
    def update(self, widget_id: str, options: WidgetUpdateOptions) -> Widget: ...
    def delete(self, widget_id: str) -> None: ...

    def _widget_from(self, data: dict[str, Any]) -> Widget: ...
```

The private `_widget_from(data)` helper at the bottom is convention — every resource that returns a model has one, used to translate a JSON:API resource object into the Pydantic model.

## Method conventions

The verbs are stable across the codebase. Use these names exactly.

| Verb | Signature | HTTP | Returns |
|---|---|---|---|
| `list(...)` | `(parent_id, options=None)` | `GET` collection endpoint | `Iterator[Widget]` |
| `read(id)` | `(widget_id)` | `GET /widgets/{id}` | `Widget` |
| `read_with_options(id, options)` | `(widget_id, options)` | `GET /widgets/{id}?include=...` | `Widget` |
| `create(parent_id, options)` | parent first, options last | `POST` | `Widget` |
| `update(id, options)` | `(widget_id, options)` | `PATCH /widgets/{id}` | `Widget` |
| `delete(id)` | `(widget_id)` | `DELETE /widgets/{id}` | `None` |

Argument-order rule: **identifiers first, options last**. `create(organization, options)`, `update(widget_id, options)`. Never reverse this; downstream callers rely on it.

For relationship endpoints (`POST /widgets/{id}/relationships/foos`), use verbs like:

- `add_*(id, options)` / `remove_*(id, options)` — modifies an unordered set
- `update_*(id, options)` — replaces the entire set
- `attach_*` / `detach_*` — pair-style operations
- `assign_*` — when there's a single relation being set (e.g. `assign_ssh_key`)

Pick the verb that mirrors what go-tfe and the API docs use — consistency across SDKs matters when users are reading both.

## Source verification

Before implementing a new endpoint, check the primary sources for the exact contract:

- Official HCP Terraform API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
- go-tfe implementation: https://github.com/hashicorp/go-tfe
- OpenAPI specs or live probes when docs/go-tfe are missing, beta, or ambiguous

Verify URL path, HTTP method, request envelope, enum values, response shape, redirects, and whether the feature is generally available. If the implementation depends on a surprising behavior, record the source in the PR description, test name, example header, or a short code comment.

## Validation: eager, with typed errors

Validate every ID/name argument at the top of every method. Two helpers from `utils.py`:

- `valid_string(s)` — non-empty string
- `valid_string_id(s)` — non-empty string with no `/` or whitespace (the JSON:API id contract)

For new public APIs, prefer a typed `TFEError` subclass from `pytfe/errors.py`. Existing resources still expose many `ValueError` validation paths; do not change those established exception types unless the breaking-change impact is explicitly accepted.

```python
from ..errors import InvalidWidgetIDError
from ..utils import valid_string_id

def read(self, widget_id: str) -> Widget:
    if not valid_string_id(widget_id):
        raise InvalidWidgetIDError()
    r = self.t.request("GET", f"/api/v2/widgets/{widget_id}")
    return self._widget_from(r.json().get("data", {}))
```

If the typed error class you need doesn't exist yet, add it to `errors.py`. Follow the existing naming:

- `Invalid<Thing>IDError(InvalidValues)` — the id is missing or malformed
- `Required<Thing>Error(InvalidValues)` — a field that must be set wasn't
- `<Thing>NotFoundError(NotFound)` — the API returned 404 (use sparingly; usually the transport raises `NotFound` already)

Subclass from a sensible parent (`InvalidValues`, `WorkspaceValidationError`, etc.) so consumers can `except TFEError:` once and catch new errors. When touching existing methods, preserve their historical exception behavior unless the change is intentionally breaking.

## Building JSON:API request payloads

Most resource write requests use the JSON:API envelope:

```python
payload = {
    "data": {
        "type": "widgets",
        "attributes": options.model_dump(by_alias=True, exclude_none=True),
    }
}
self.t.request("POST", "/api/v2/...", json_body=payload)
```

Key arguments to `model_dump`:

- **`by_alias=True`** — emit the hyphenated JSON:API attribute names, not the Python snake_case field names. Without this you'll send `auto_apply` instead of `auto-apply` and the API will silently ignore it.
- **`exclude_none=True`** — don't send fields the caller didn't set. `PATCH` semantics depend on this.
- **`mode="json"`** — when your options contain enums, including query params such as `include`. Without `mode="json"`, an enum field serialises as `EnumClass.MEMBER` (the repr) instead of the wire value. The bug is silent — the API returns 400 with "Invalid parameter".

So for option models that contain enum fields:

```python
params = options.model_dump(by_alias=True, exclude_none=True, mode="json")
if isinstance(params.get("include"), list):
    params["include"] = ",".join(params["include"])
```

For relationships, use the JSON:API identifier-object shape:

```python
payload = {
    "data": {
        "type": "team-workspaces",
        "attributes": attrs,
        "relationships": {
            "team": {"data": {"type": "teams", "id": team_id}},
            "workspace": {"data": {"type": "workspaces", "id": workspace_id}},
        },
    }
}
```

For *replace-many* relationships, pass an array of identifiers:

```python
payload = {
    "data": [
        {"type": "workspaces", "id": wid} for wid in workspace_ids
    ]
}
self.t.request("POST", f"/api/v2/projects/{project_id}/relationships/workspaces", json_body=payload)
```

## Parsing responses

Do not assume every successful response is a JSON:API envelope. Check the official docs/go-tfe/spec before writing the parser. Common shapes in this SDK include:

- JSON:API envelope: `{"data": {...}}` or `{"data": [{...}]}`
- Bare resource object with top-level `attributes`
- `204 No Content`
- `null`
- Raw bytes
- `3xx` redirect to a presigned blob URL

Add unit tests for every non-standard shape a method supports. The common `_widget_from(data)` helper takes a single JSON:API `data` object (already unwrapped from the envelope by the caller) and returns the Pydantic model:

```python
def _widget_from(self, data: dict[str, Any]) -> Widget:
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    return Widget.model_validate(attrs)
```

If the model has relationships, parse them with the shared `parse_relationships` helper from `pytfe._jsonapi` — don't hand-roll a per-relation if-ladder. Pass a declarative `{wire_relation: Model}` map (or `{wire: (python_attr, Model)}` when the attribute name diverges from `wire.replace("-", "_")`), and thread the response's top-level `included` so `?include=` requests hydrate full nested objects instead of id-only stubs:

```python
from .._jsonapi import parse_relationships

_WIDGET_REL_MAP = {"organization": Organization, "current-run": Run}

def _widget_from(self, data: dict[str, Any], included=None) -> Widget:
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    attrs.update(parse_relationships(data.get("relationships"), _WIDGET_REL_MAP, included=included))
    return Widget.model_validate(attrs)

# caller threads included from the envelope:
payload = r.json()
return self._widget_from(payload["data"], payload.get("included"))
```

`parse_relationships` skips null/absent/unmapped relations, handles single vs list `data`, and builds id-only stubs via `model_construct` when `included` is absent. For a relation the model exposes as a **flat `*_id`** field instead of an embedded model, keep the small manual extraction:

```python
team_data = (data.get("relationships", {}).get("team") or {}).get("data") or {}
if team_data.get("id"):
    attrs["team-id"] = team_data["id"]
```

Keep polymorphic relations (e.g. `locked-by`) and relations whose `data` carries inline attributes (e.g. workspace `outputs`) as explicit special cases — they don't fit the map. See `resources/workspaces.py` and `resources/run.py` for the reference parsers. Always defensively coalesce with `or {}` — relationships may be missing from sparse responses.

> If the parser is a **method** on a service class that defines `def list(...)`, you can't annotate `included: list[...] | None` (in class scope `list` is the method). Prefer a module-level `_widget_from` function (like `_ws_from`/`_run_from`), or use `builtins.list[...]`.


## Pagination — use `self._list`, don't roll your own

`_Service._list(path, params=...)` is the universal helper. It yields raw `dict` items from the `data` array, transparently following pagination. It gracefully handles single-shot non-paginated endpoints too — see [ITERATORS.md](ITERATORS.md) for the full breakdown.

Don't write your own page loop. If you find yourself doing it, you're solving a problem `_list()` already handled.

## URL paths

Always start with `/api/v2/...`. The base URL is set on the transport, but the path includes the API version prefix:

```python
"/api/v2/organizations/{organization}/widgets"      # collection scoped to org
"/api/v2/widgets/{widget_id}"                       # single resource
"/api/v2/widgets/{widget_id}/relationships/foos"    # JSON:API relationship route
"/api/v2/widgets/{widget_id}/actions/lock"          # action endpoint
```

Use f-strings to interpolate ids — they've been validated by `valid_string_id` above. URL-quote organization names with `urllib.parse.quote` only when the API explicitly requires it (most don't).

## Errors raised by the transport

`HTTPTransport.request` raises typed errors from `pytfe.errors` based on status code:

- `AuthError` for 401/403
- `NotFound` for 404
- `RateLimited` for 429 (with `.retry_after`)
- `ServerError` for 5xx
- `TFEError` for everything else 4xx

You usually don't need to catch these — let them propagate to the caller. Catch only when:

- You want to translate to a more specific error (`except TFEError as e: if "rate-limit" in str(e): raise ...`)
- The "error" is actually an expected outcome — like a `NotFound` meaning "no current assessment yet":

```python
try:
    r = self.t.request("GET", f"/api/v2/workspaces/{ws_id}/current-assessment-result")
except NotFound:
    return None
```

## Wiring into the client

Two places to update:

### `src/pytfe/client.py`

1. Add the import alphabetically within its section.
2. Add `self.widgets = Widgets(self._transport)` to `TFEClient.__init__`, grouped with related resources.

```python
from .resources.widget import Widgets
...
self.widgets = Widgets(self._transport)
```

The attribute name on the client is **plural snake_case** (`workspaces`, `team_tokens`, `team_workspace_accesses`). It must match the class name's lowercased plural.

## Typing gotcha: `def list` shadows `list[...]`

If a resource class defines `def list(...)`, mypy can resolve later annotations in the same class like `list[str]` to the method instead of the builtin type. For helper methods defined after `list`, avoid bare `list[...]`. Use `builtins.list[...]`, `Sequence[...]`, or another unshadowed collection type.

### `src/pytfe/models/__init__.py`

If you added new models (almost always yes), wire them through:

1. Import them alphabetically in the right section block.
2. Add their names to the `__all__` list at the bottom.

If your models use forward references, add a `Model.model_rebuild(...)` call at the bottom — see [MODELS.md](MODELS.md).

## Tests

One test file per resource: `tests/units/test_widget.py`. Mirror the structure of `tests/units/test_comment.py` (small and clean) or `tests/units/test_workspaces.py` (large).

The structure:

```python
import pytest
from unittest.mock import Mock

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidWidgetIDError
from pytfe.models.widget import Widget, WidgetCreateOptions
from pytfe.resources.widget import Widgets


class TestWidgets:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return Widgets(mock_transport)

    def test_read_widget_invalid_id(self, service):
        with pytest.raises(InvalidWidgetIDError):
            service.read("")

    def test_list_widgets(self, service, mock_transport):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": "wid-1", "type": "widgets", "attributes": {...}}],
            "meta": {"pagination": {"current-page": 1, "total-pages": 1}},
        }
        mock_transport.request.return_value = mock_response

        result = list(service.list("my-org"))      # materialize Iterator

        assert len(result) == 1
        assert result[0].id == "wid-1"
```

Two things test reviewers always check:

- **Invalid-ID tests** for list methods wrap with `list(...)` to force iteration — generator-based methods defer validation. See [ITERATORS.md](ITERATORS.md).
- **JSON:API path assertions** match exactly. If you're constructing `/api/v2/widgets/{id}` with f-string interpolation, the test asserts the exact path. Don't be tempted to leave wildcards.

`make test` runs everything; `make lint` runs ruff + mypy. Both must pass.

## Examples — when and how

New resources should get an example file in `examples/`, or an existing example should be extended if that is the natural home. The purpose isn't comprehensive coverage — it's "a real engineer landing on this repo can copy-paste this and have a working demo in 60 seconds". Prefer the current style for new examples, but do not churn older examples only to rename helpers or match prose.

### When to make a new example file vs extend an existing one

- **New resource, no existing example for the parent surface** → new file (`examples/widget.py`)
- **New method on an existing resource** → extend the existing example file, gate the new section behind a flag like `--demo-foo` or `--show-bar`
- **Single related feature spread across multiple resources** → pick the most natural home; don't duplicate

We've already consolidated some examples into existing ones — see `examples/apply.py --recover-errored-state` for the pattern. When in doubt, extend rather than fragment.

### Example file structure

```python
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import WidgetCreateOptions


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="Widgets demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--organization", default=os.getenv("TFE_ORG", ""))
    parser.add_argument("--widget-id", help="Widget id for read/update/delete")
    parser.add_argument("--list", action="store_true", help="List widgets")
    parser.add_argument("--create", action="store_true", help="Create a widget")
    args = parser.parse_args()

    if not args.token:
        print("TFE_TOKEN is not set")
        return 2

    client = TFEClient(TFEConfig(address=args.address, token=args.token))

    if args.list:
        _print_header(f"Listing widgets for {args.organization}")
        for w in client.widgets.list(args.organization):
            print(f"  - {w.id}  {w.name}")

    if args.create:
        _print_header("Creating a widget")
        w = client.widgets.create(
            args.organization, WidgetCreateOptions(name="example")
        )
        print(f"  created {w.id}")
        # If the example creates resources, also clean them up at the end.
        try:
            client.widgets.delete(w.id)
            print(f"  cleaned up {w.id}")
        except Exception as e:
            print(f"  WARN: cleanup failed: {e}")

    client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Rules examples follow

- **Auth via env vars by default** — `TFE_TOKEN`, `TFE_ADDRESS`, `TFE_ORG`. Never hard-code a token.
- **`argparse` for CLI**, with sensible `--<feature>` flags so users can opt into specific demos.
- **`_print_header(title)` helper** for visual separation between sections in new examples. Older examples vary; do not churn them only for naming consistency.
- **Cleanup what you create.** If the example creates scratch resources, delete them in a `try/finally`. Warn but don't fail on cleanup errors.
- **Exit codes**: `return 0` on success, `return 2` for missing config, raise on unexpected SDK errors so the user sees the traceback.
- **`client.close()` at the end** when you opened a client.

## What NOT to do

```python
# ❌ Reaching directly through self.t for paginated endpoints — use self._list
data = self.t.request("GET", path).json()["data"]   # one page only, no pagination
for item in self._list(path): ...                    # ✅

# ❌ Letting the JSON:API envelope leak out
return r.json()                                      # raw dict with "data"/"included"/etc.
return self._widget_from(r.json()["data"])           # ✅

# ❌ Sending snake_case attrs to the API
options.model_dump(exclude_none=True)                # workspace_id → wrong on the wire
options.model_dump(by_alias=True, exclude_none=True) # ✅

# ❌ Forgetting mode="json" with enums — silent 400 from the API
options.model_dump(by_alias=True, exclude_none=True)             # enum becomes 'EnumClass.MEMBER'
options.model_dump(by_alias=True, exclude_none=True, mode="json") # ✅

# Prefer typed errors for new public APIs. Preserve existing ValueError
# behavior unless the compatibility impact is explicitly accepted.
raise ValueError("invalid widget id")                 # existing APIs may do this
raise InvalidWidgetIDError()                          # preferred for new APIs

# ❌ Forgetting to wire the resource into the client
# Just add `self.widgets = Widgets(self._transport)` in client.py — the
# resource is otherwise unreachable from TFEClient.
```

## Checklist when adding a new resource

- [ ] New file `src/pytfe/resources/widget.py` with `class Widgets(_Service)`
- [ ] Standard verbs (`list`, `read`, `create`, `update`, `delete`) with the standard signatures
- [ ] Every method validates IDs; new public APIs prefer typed `TFEError` subclasses, while established `ValueError` behavior is preserved unless intentionally changed
- [ ] Write requests use the JSON:API envelope; `model_dump` uses `by_alias=True, exclude_none=True`, plus `mode="json"` if there are enums
- [ ] `list*` returns `Iterator[X]` via `self._list(...)` (see [ITERATORS.md](ITERATORS.md))
- [ ] Response parsing helper `_widget_from(data)` translates JSON:API → Pydantic
- [ ] Non-standard response shapes (`204`, `null`, bare resources, raw bytes, redirects) are verified against docs/go-tfe/spec and covered by tests
- [ ] Classes with `def list(...)` avoid later bare `list[...]` annotations
- [ ] Models added per [MODELS.md](MODELS.md), wired in `models/__init__.py`
- [ ] Resource wired into `client.py` (import + `self.widgets = Widgets(...)`)
- [ ] Unit tests in `tests/units/test_widget.py`, including invalid-id cases and at least one happy-path per method
- [ ] Example in `examples/widget.py` (or extension to existing file), with env-var auth, cleanup, and `_print_header`
- [ ] `make test` and `make lint` both pass
