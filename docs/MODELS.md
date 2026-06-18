# Models — Pydantic conventions in pyTFE

This is internal reference for adding or editing Pydantic models in `src/pytfe/models/`. The patterns below are what the codebase already does; follow them so new resources line up with what's there.

All models inherit from `pydantic.BaseModel` and target Pydantic v2. The `from __future__ import annotations` line is at the top of every model file so forward references and type hints work without runtime imports.

## Layout of a model file

One model file per resource, named after the resource (`workspace.py`, `agent.py`, `team.py`). Each file usually contains:

1. **Enums** for fixed string sets the API uses (status, type, kind).
2. **The main resource model** (the thing you get back from a `read`/`list` — e.g. `Workspace`, `Team`).
3. **`*CreateOptions`** for `POST` requests.
4. **`*UpdateOptions`** for `PATCH` requests.
5. **`*ListOptions`** for `GET` collection requests (filters, pagination, includes).
6. **`*ReadOptions`** for `GET` single-resource requests that take `include[]` (only when needed).

Use a single file unless the model surface is large enough that splitting helps. There's no "package per resource" pattern here — one file is the default.

## `ConfigDict`

New or touched `BaseModel` classes should set `model_config = ConfigDict(...)` unless you are deliberately preserving a local legacy pattern. Several older models predate this convention; do not mass-refactor them just to satisfy this rule because changing validation/coercion behavior can be a public API change. The conventions for new work are:

| Setting | When to use |
|---|---|
| `populate_by_name=True` | **Always.** Lets callers pass either the field name (`created_at=...`) or the alias (`{"created-at": ...}`) when constructing. |
| `validate_by_name=True` | Use on models that are parsed *from* API responses **or** constructed by callers via field names. Pair with `populate_by_name=True`. |
| `extra="forbid"` | Use on `*CreateOptions` / `*UpdateOptions` / option models where you want a typo (`workspce_id=...`) to fail loudly instead of being silently dropped. Don't put it on response models — the API can add fields and we don't want that to break parsing. |
| `extra="allow"` | Standard for **response models** parsed from API payloads. The default (`extra="ignore"`) silently drops any wire attribute without a declared field, so a new server field becomes a data-loss bug. `extra="allow"` retains undeclared fields in `model_extra` under their wire names (e.g. `model_extra["future-field"]`). Note: extra keys are *not* dot-accessible as snake_case and have no type — add an explicit aliased field for anything users should access ergonomically. `Workspace` is the reference implementation; relationship parsing for these models goes through `pytfe._jsonapi.parse_relationships` (see the Relationships section). |
| `arbitrary_types_allowed=True` | Only when you genuinely have a non-Pydantic type in a field (rare). |

The standard line you'll write 90% of the time:

```python
class Foo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    ...
```

## Base class: `TFEModel` vs `BaseModel`

| Inherit from | For |
|---|---|
| **`TFEModel`** (`pytfe.models`, defined in `models/_base.py`) | **Top-level resource models**: anything returned from a `read`/`list`/`create`/`update` that corresponds to a JSON:API *resource object* (`Workspace`, `Run`, `Project`, `Policy`, `AdminRun`, …). |
| **`BaseModel`** | Everything else: `*CreateOptions` / `*UpdateOptions` / `*ListOptions`, nested attribute sub-objects (`WorkspacePermissions`, `VCSRepo`, …), enums, and `*List` envelopes. |

`TFEModel` is **config-light**: it adds no `model_config`, so you still set your own (`extra="allow"`, etc.) exactly as above. What it adds is the lossless related-resource escape hatch: `.relationships`, `.included`, `.included_by(type, id)`, `.related(name)`, and the `.has_relationships` / `.has_included` presence flags. These are private attributes, so they never touch `model_dump()` and add no public fields, and `TFEModel` also overrides `__eq__` to ignore them, so equality stays identical to a plain `BaseModel`. Inheriting it is additive and non-breaking.

For the accessors to be *populated* (not just present-and-empty), the resource's parser must hand the raw JSON:API resource dict (and any document `included`) to `attach_jsonapi`:

```python
from .._jsonapi import attach_jsonapi, parse_relationships   # in a resources/*.py

def _foo_from(data, included=None):
    attr = dict(data.get("attributes") or {})
    attr["id"] = data.get("id")
    attr.update(parse_relationships(data.get("relationships"), _FOO_REL_MAP, included=included))
    return attach_jsonapi(Foo.model_validate(attr), data, included)
```

`attach_jsonapi(obj, data, included)` is the one line that captures both raw blocks; pass `included=payload.get("included")` from any `read`/`list` that supports `?include=`. See [related-resources.md](related-resources.md) for the consumer-facing view.

### Why not put it on every model

`TFEModel` is scoped to resource objects on purpose. The escape hatch is only meaningful for things parsed from a JSON:API *resource object* (a thing with a `relationships` block, returned from `read`/`list`/`create`/`update`). Putting it on `*Options`, sub-objects, and `*List` envelopes would cost more than it gives:

* **It does nothing on its own.** The accessors stay empty until a parser calls `attach_jsonapi(...)`. A request/options model is never parsed from a response, so its accessors would be permanently empty and pointless.
* **It adds a confusing, response-only surface to request objects.** A `WorkspaceReadOptions` is something you *build and send*. Exposing `.relationships`, `.included`, and `.related(...)` on it (always empty) is misleading in code, in docs, and in editor autocomplete.
* **It reserves names.** `TFEModel` claims `relationships`, `included`, `related`, `included_by`, `has_relationships`, and `has_included`. If a model later needs a field with one of those names, Pydantic warns (`Field name "..." shadows an attribute in parent "TFEModel"`) and the field silently wins, quietly breaking the escape hatch on that model. Keeping non-resource models on `BaseModel` avoids reserving those names where they are not needed.
* **It changes the public class hierarchy and equality** for many public, downstream-facing models. `TFEModel`'s `__eq__` is intentionally equivalent to `BaseModel`'s for public fields, but there is no reason to swap a custom `__eq__` onto the hundreds of options and sub-object models that behave like plain Pydantic today.

What it does **not** break: `frozen=True` models stay hashable, because Pydantic regenerates `__hash__` for a frozen subclass. The only real failure mode is the name collision above.

Rule of thumb: inherit `TFEModel` when the model is a JSON:API resource you parse *from* a response; use `BaseModel` for everything you *build* (options), *nest* (sub-objects), or *wrap* (`*List` envelopes).

## Field aliases: JSON:API hyphens → Python snake_case

HCP Terraform speaks JSON:API, which uses hyphenated attribute names (`created-at`, `auto-apply`, `state-versions`). Python uses snake_case. Bridge with `Field(alias=...)`:

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class Run(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    has_changes: bool | None = Field(None, alias="has-changes")
    is_destroy: bool | None = Field(None, alias="is-destroy")
    auto_apply: bool | None = Field(None, alias="auto-apply")
    created_at: datetime | None = Field(None, alias="created-at")
    canceled_at: datetime | None = Field(None, alias="canceled-at")
```

Rules:

- **Every multi-word JSON:API attribute** gets an alias. Don't try to invent a snake_case-to-hyphen mapper — be explicit per field.
- **Page params** use the JSON:API square-bracket form: `Field(None, alias="page[number]")`, `Field(None, alias="page[size]")`. Note that a few endpoints (workspace `/vars`, `/all-vars`) are not paginated and ignore these — their resource methods call `self._list(..., paginated=False)`, so a `page_size` field on those options models would be a no-op. See [ITERATORS.md](ITERATORS.md).
- **Filter params** use the same convention: `Field(None, alias="filter[workspace][name]")`.
- **`include`** is a comma-separated string on the wire but exposed as `list[SomeEnum] | None` in Python; the resource layer dumps options with `mode="json"` and joins the resulting values (`",".join(params["include"])`). See the `policy_set.read_with_options` pattern.

## Optional vs required vs default fields

The codebase is conservative about which fields are required. The pattern:

- **Resource models** (parsed from API responses): almost everything except `id` is `field: T | None = Field(None, alias="...")`. The API may omit fields depending on permissions or include params, so being permissive avoids brittle parsing.
- **`*CreateOptions`**: required fields use `field: T = Field(..., description="...")` (Pydantic's "required" sentinel). Optional fields use `field: T | None = None`.
- **`*UpdateOptions`**: **everything** is optional (`field: T | None = None`). `PATCH` semantics — only set fields are sent.
- **Collection fields**: prefer `default_factory=list` over `= []` (avoids the mutable-default trap). For maps, `default_factory=dict`.

Example:

```python
class WorkspaceCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(..., description="Workspace name")
    description: str | None = None
    auto_apply: bool | None = Field(None, alias="auto-apply")
    project: dict | None = None   # relationship — see "Relationships" below


class WorkspaceUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str | None = None
    description: str | None = None
    auto_apply: bool | None = Field(None, alias="auto-apply")
```

## Enums

String enums with explicit string values, mirroring what the API returns:

```python
from enum import Enum


class RunStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    PLANNED = "planned"
    APPLIED = "applied"
    ERRORED = "errored"
    DISCARDED = "discarded"
```

A few conventions:

- **`str, Enum`** so the value is JSON-serialisable without `.value` indirection (pydantic handles this with `mode="json"` on `model_dump`).
- **`SCREAMING_SNAKE`** member names. Values mirror the wire string exactly — usually lowercase, sometimes with underscores. Don't change the wire value to "look nicer".
- When the API uses hyphenated values (`"pre-plan"`, `"post-plan"`), keep the hyphens in the value string. Verify enum values against the official HCP Terraform API docs, go-tfe, or live API if unsure — there have been past bugs where underscore values diverged from what the server actually returns.
- Put enums **above** the model that uses them in the same file.

## Validators

Two flavours, both Pydantic v2:

### `model_validator(mode="after")` for option models

Use on `*CreateOptions` / `*UpdateOptions` to enforce required-name / valid-ID rules at construction time. For new public APIs, prefer a typed `TFEError` subclass from `pytfe.errors`. For existing option models that already raise `ValueError`, preserve that behavior unless the breaking-change impact is explicitly accepted:

```python
from pydantic import model_validator
from ..errors import InvalidNameError, RequiredNameError
from ..utils import valid_string, valid_string_id


class AgentPoolCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(..., alias="name")

    @model_validator(mode="after")
    def valid(self) -> AgentPoolCreateOptions:
        if not valid_string(self.name):
            raise RequiredNameError()
        if not valid_string_id(self.name):
            raise InvalidNameError()
        return self
```

### `field_validator` for per-field coercion or normalisation

Use sparingly — only when you need to massage input before Pydantic's default coercion, or when a single field has a non-trivial rule:

```python
from pydantic import field_validator


class NotificationConfiguration(BaseModel):
    @field_validator("triggers", mode="before")
    @classmethod
    def _coerce_triggers(cls, v):
        ...
```

`mode="before"` runs on the raw input; `mode="after"` runs on the already-validated value. Default to `"after"` unless you need pre-validation cleanup.

## Relationships

JSON:API responses include a `relationships` block separate from `attributes`. Two ways to model relationship references on the resource:

### Option 1 — ID stub on the related model

When you only need the related id, use a typed stub. The resource layer fills it in via `Model.model_construct(id=...)`:

```python
class TaskStage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    run: Run | None = Field(None, alias="run")            # only .id populated
    task_results: list[TaskResult] | None = Field(None, alias="task-results")
```

The resource layer should populate these via the shared `parse_relationships` helper (see below) rather than a hand-rolled if-ladder. For a true one-off, `Model.model_construct(id=...)` (not `model_validate`) is correct — it skips validation, which is right because you only have `{id, type}`.

### Parsing relationships — `pytfe._jsonapi.parse_relationships`

Don't hand-roll the `relationships.get("x", {}).get("data")` if-ladder per resource. The canonical parser lives in `src/pytfe/_jsonapi.py` and is driven by a declarative map of `{wire_relation: Model}` (or `{wire_relation: (python_attr, Model)}` when the attribute name diverges from `wire.replace("-", "_")`):

```python
from .._jsonapi import parse_relationships

_WIDGET_REL_MAP = {
    "organization": Organization,                 # attr derived: "organization"
    "current-run": Run,                            # attr derived: "current_run"
    "vars": ("variables", Variable),               # wire name diverges from attr
}

def _widget_from(d, included=None):
    attrs = dict(d.get("attributes") or {})
    attrs["id"] = d.get("id")
    attrs.update(parse_relationships(d.get("relationships"), _WIDGET_REL_MAP, included=included))
    return Widget.model_validate(attrs)
```

`parse_relationships` handles single vs list `data`, skips null/absent and unmapped relations (so they fall back to model defaults / `extra="allow"`), and — when the caller passes the response's top-level `included` array — hydrates the **full** related object instead of an id-only stub (so `?include=current_run` returns a populated `Run`, not just `{id}`). Thread `included` from read paths: `payload = r.json(); _widget_from(payload["data"], payload.get("included"))`.

Keep genuinely polymorphic relations (e.g. workspace `locked-by`, `data-retention-policy-choice`) and relations whose `data` carries inline attributes (e.g. workspace `outputs`) as explicit special cases — they don't fit the simple map. `Workspace` (`resources/workspaces.py`) and `Run` (`resources/run.py`) are the reference implementations.

> One gotcha: a parser written as a **method** on a service class that also defines `def list(...)` cannot annotate `included: list[...] | None` — in class scope `list` resolves to the method. Make the parser a module-level function (preferred, matches `_ws_from`/`_run_from`), or use `builtins.list[...]`.

### Option 2 — Flat `*_id` field

When the relationship is "owned" by this resource and just one id matters, expose it as a flat `*_id` field (with hyphen alias if needed). Less plumbing, fine when you don't need the related model object:

```python
class TeamWorkspaceAccess(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str
    team_id: str | None = Field(default=None, alias="team-id")
    workspace_id: str | None = Field(default=None, alias="workspace-id")
```

The resource layer reads from `relationships.team.data.id` and stuffs it into `attributes["team-id"]` before calling `model_validate`. See `resources/team_workspace_access.py:_parse`.

Pick Option 1 when callers may want to traverse the relationship further (e.g. `task_stage.run.id`). Pick Option 2 when the id is all you'll ever need.

## Forward references and `model_rebuild`

If a model A references model B and B references A (or A is defined before B), Pydantic can't resolve the forward ref at class-definition time. The fix: leave the annotation as a string in the model file, then call `Model.model_rebuild()` from `models/__init__.py` once everything is imported.

The block at the bottom of `models/__init__.py` is where this happens:

```python
Run.model_rebuild(
    raise_errors=False,
    _types_namespace={"TaskStage": TaskStage},
)
Workspace.model_rebuild(
    raise_errors=False,
    _types_namespace={"AgentPool": AgentPool, "Run": Run, "TaskStage": TaskStage},
)
```

`raise_errors=False` is the project default — failure to resolve a forward ref shouldn't crash the SDK at import time. Add your new model's rebuild call there if it has forward-referenced relations.

## Exporting

Two things to update when you add a model:

1. **Imports** at the top of `models/__init__.py` — add your new classes alphabetically within their section.
2. **`__all__`** at the bottom — add the names that should be importable as `from pytfe.models import Foo`.

Don't forget option models, enums, and any include-opt enums. The `__all__` list is what users see in `pytfe.models` — if it's not there, it's not part of the public API.

## What NOT to do

```python
# ❌ Don't use bare strings for the alias when the field has multiple words.
created_at: datetime | None = None              # parses "created_at", misses "created-at"

# ❌ Don't reach for arbitrary_types_allowed unless you actually have one.

# ❌ Don't use mutable default values directly.
tags: list[str] = []                            # all instances share the same list
tags: list[str] = Field(default_factory=list)   # ✅

# Prefer a typed TFEError subclass for new public APIs.
raise ValueError("name required")               # existing APIs may still do this
raise RequiredNameError()                       # preferred for new APIs

# ❌ Don't model relationships as raw dicts when there's a typed stub option.
workspace: dict | None = None                   # loses type information
workspace: Workspace | None = None              # ✅ (filled via model_construct in resource)
```

### Python keyword aliases require `populate_by_name=True`

`populate_by_name=True` is documented above as "Always" — for aliases that are Python keywords (`global`, `class`, `from`, `import`, `return`, `yield`, `lambda`, `del`, `pass`, `raise`, `with`, `as`, `is`, `in`, `not`, `and`, `or`, `if`, `else`, `elif`, `for`, `while`, `try`, `except`, `finally`, `def`, `async`, `await`), it's not just convenience — it's a correctness requirement. Without it, callers cannot construct the model with a kwarg at all and are forced into ugly workarounds:

```python
# ❌ Without populate_by_name=True, this is the only way to construct:
VariableSetCreateOptions(name="x", **{"global": False})            # awkward
VariableSetCreateOptions.model_validate({"name": "x", "global": False})  # inconsistent with every other *CreateOptions

# Field name with trailing underscore IS NOT accepted because populate_by_name defaults to False:
VariableSetCreateOptions(name="x", global_=False)                  # ValidationError: 'global' field required

# ✅ With populate_by_name=True, the trailing-underscore form works and matches the rest of the SDK:
class VariableSetCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    global_: bool = Field(alias="global")

VariableSetCreateOptions(name="x", global_=False)                  # ✅
```

The CI check in `tests/units/test_model_conventions.py` enforces this for every model that declares an `alias=`. Models that intentionally accept only the wire-format alias must be added to the explicit allowlist in that test, with a comment explaining why.

## Checklist when adding a new model

- [ ] `from __future__ import annotations` at the top
- [ ] New or touched classes use `model_config = ConfigDict(populate_by_name=True, validate_by_name=True)` unless preserving a local legacy pattern
- [ ] Hyphenated JSON:API attribute names → `Field(alias="...")`
- [ ] **Response models** (parsed from API payloads) add `extra="allow"` to their `ConfigDict` for forward compatibility; relationships are parsed via `parse_relationships`, not a hand-rolled if-ladder
- [ ] Response model fields default to `T | None = Field(None, alias="...")`
- [ ] `*CreateOptions` uses `Field(...)` for required fields, `T | None = None` for optional
- [ ] `*UpdateOptions` is fully optional
- [ ] Enums are `str, Enum` with SCREAMING_SNAKE member names and wire-faithful values
- [ ] New validators prefer typed `TFEError` subclasses; existing `ValueError` behavior is not changed without an explicit compatibility decision
- [ ] Collections use `default_factory=list` / `default_factory=dict`
- [ ] Added to `models/__init__.py` imports + `__all__`
- [ ] If you used forward references, added a `model_rebuild()` call at the bottom of `models/__init__.py`
