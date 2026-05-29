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
| `extra="allow"` | Standard for **response models** parsed from API payloads. The default (`extra="ignore"`) silently drops any wire attribute without a declared field, so a new server field becomes a data-loss bug. `extra="allow"` retains undeclared fields in `model_extra` under their wire names (e.g. `model_extra["future-field"]`). Note: extra keys are *not* dot-accessible as snake_case and have no type — add an explicit aliased field for anything users should access ergonomically. `Workspace` is the reference implementation; relationship parsing for these models goes through `resources/_jsonapi`. |
| `arbitrary_types_allowed=True` | Only when you genuinely have a non-Pydantic type in a field (rare). |

The standard line you'll write 90% of the time:

```python
class Foo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    ...
```

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
- **Page params** use the JSON:API square-bracket form: `Field(None, alias="page[number]")`, `Field(None, alias="page[size]")`.
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

Use `model_construct` (not `model_validate`) in the resource for these stubs — it skips validation, which is correct because you only have `{id, type}`:

```python
attributes["run"] = Run.model_construct(id=run_data["id"])
```

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
- [ ] Response model fields default to `T | None = Field(None, alias="...")`
- [ ] `*CreateOptions` uses `Field(...)` for required fields, `T | None = None` for optional
- [ ] `*UpdateOptions` is fully optional
- [ ] Enums are `str, Enum` with SCREAMING_SNAKE member names and wire-faithful values
- [ ] New validators prefer typed `TFEError` subclasses; existing `ValueError` behavior is not changed without an explicit compatibility decision
- [ ] Collections use `default_factory=list` / `default_factory=dict`
- [ ] Added to `models/__init__.py` imports + `__all__`
- [ ] If you used forward references, added a `model_rebuild()` call at the bottom of `models/__init__.py`
