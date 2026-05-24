# Iterators and pagination in pyTFE

This is internal reference for anyone — human or AI — adding a new resource to the SDK or auditing existing ones. Keep this file up to date as the conventions evolve.

## The one-line rule

> Any method named `list` or `list_*` on a resource service returns `Iterator[X]`. Never `list[X]`, never `LazyList`, never a custom `*Pager`. Just `Iterator[X]`.

The matching import is `from collections.abc import Iterator`, not `typing.Iterator` (which is deprecated alias since 3.9).

This rule applies to public resource service methods. Private parsing helpers may return concrete lists when they are just internal implementation details and are not part of the SDK public surface.

## Why iterators

The HCP Terraform API paginates **every** list endpoint. The contract is uniform: pass `page[number]` and `page[size]`, read pagination metadata out of the response envelope, and follow links until there are no more. Materialising the entire result set up front would mean fetching every page synchronously before the caller sees the first row — fine for ten workspaces, painful for ten thousand. Iterators let the SDK do the right thing by default: lazy under the hood, simple at the call site.

Even when an endpoint isn't actually paginated (some single-shot relationship reads like `effective-tag-bindings`), we still use the iterator signature. The reason is purely consistency — a future contributor (or an LLM generating new resources by analogy) should never have to think about which list method is which shape. If it's named `list_*`, it returns `Iterator[X]`.

## How callers use them

There are two idioms. Both are normal and expected.

```python
# 1. Stream — handy when results are large, or you can break early.
for ws in client.workspaces.list("my-org"):
    if ws.name.startswith("prod-"):
        print(ws.id)
        break

# 2. Materialize — when you actually want a list to len(), index, or hand off.
workspaces = list(client.workspaces.list("my-org"))
print(f"{len(workspaces)} workspaces")
```

Two things every caller needs to know:

- **Iterators are single-use.** Iterating an already-walked iterator yields nothing. If you need to traverse the same result more than once, capture it with `list(...)` first.
- **Iterators are always truthy.** `if iterator:` is True even when the iterator is empty. Use `materialized = list(...); if materialized:` if you need a non-empty check.

## How to implement a new `list_*` method

There is **one canonical pattern** in the codebase, and it works for both paginated and non-paginated endpoints. Use it unless you have a specific reason not to.

### The canonical pattern: `self._list(...)` + `yield`

```python
def list(
    self, organization: str, options: WorkspaceListOptions | None = None
) -> Iterator[Workspace]:
    if not valid_string_id(organization):
        raise InvalidOrgError()

    params = options.model_dump(by_alias=True, exclude_none=True, mode="json") if options else {}
    path = f"/api/v2/organizations/{organization}/workspaces"
    for item in self._list(path, params=params):
        yield self._workspace_from(item)
```

That's it. `self._list()` lives in `_base.py` and handles `page[number]` / `page[size]` and follow-through automatically. It is also robust to endpoints that **don't paginate** — if the response has no pagination metadata and the returned data is smaller than the requested page size, the helper just breaks after one round-trip. So you do not need a different code path for relationship reads like `GET /workspaces/{id}/tag-bindings` (single response) versus list endpoints like `GET /organizations/{org}/workspaces` (paginated). The same `for item in self._list(path): yield ...` works for both.


### Note on lazy validation

A Python generator function defers its entire body until the caller calls `next()`. That means `if not valid_string_id(...): raise ...` only fires on first iteration, not at call time. Practically, callers iterate immediately so this is fine — but tests need to materialize before asserting that a `ValueError` is raised:

```python
# tests/units/test_*.py — invalid-id case
with pytest.raises(InvalidOrgError):
    list(client.workspaces.list(""))     # wrap with list() to force iteration
```

If you genuinely need eager validation (raised from the call expression itself, not the first `for` loop), use the wrapper pattern:

```python
def list(self, organization: str, ...) -> Iterator[Workspace]:
    if not valid_string_id(organization):
        raise InvalidOrgError()             # eager

    params = ...
    path = ...
    def _gen() -> Iterator[Workspace]:
        for item in self._list(path, params=params):
            yield self._workspace_from(item)
    return _gen()
```

Both forms appear in the codebase (`policy_set.list` uses the wrapper; most others don't). Pick the wrapper only when eager-error behavior is important to a specific resource.

### Mypy note: `def list` shadows `list[...]`

Inside a class that defines a method named `list`, mypy can resolve later bare annotations like `list[str]` to the method instead of the builtin type. If the same resource class has helper methods after `def list(...)`, avoid bare `list[...]` in those later signatures or annotations. Use one of these instead:

```python
import builtins
from collections.abc import Sequence


def add_users(self, team_id: str, usernames: builtins.list[str]) -> None: ...
def add_users(self, team_id: str, usernames: Sequence[str]) -> None: ...
```

### The one deviation: `return iter(list)` for endpoints with fallback logic

There is exactly one situation where neither the plain generator nor the wrapper pattern works well: when the method has a **try/except fallback that calls a different endpoint** after the primary one fails. A pure generator could yield items from the primary endpoint, fail partway through, then switch to the fallback and yield duplicates.

For this case — and this case only — fetch eagerly and return `iter(materialized_list)`:

```python
def list_versions(
    self, module_id: RegistryModuleID
) -> Iterator[RegistryModuleVersion]:
    if not self._validate_module_id(module_id):
        raise ValueError("Invalid module ID")

    try:
        versions = [...]                       # primary endpoint
        return iter(versions)
    except Exception:
        try:
            versions = [...]                   # fallback: different endpoint
            return iter(versions)
        except Exception:
            return iter([])
```

`registry_module.list_versions` is the only method in the codebase that does this. Add a docstring note explaining the reason if you find yourself reaching for this pattern, so future readers don't mistake it for something to copy.

Do **not** reach for `iter(list)` just because the endpoint is non-paginated. Use `self._list()` for those — that's the convention.

### Shape that does **not** match the convention (don't do this)

```python
# ❌ Returns Iterable instead of Iterator — looks similar, isn't.
def list(...) -> Iterable[Workspace]: ...

# ❌ Returns Pager / LazyList / custom wrapper.
def list(...) -> WorkspaceList: ...

# ❌ Returns concrete list. The type is a public contract; consumers will
#    rely on len(), indexing, and isinstance(result, list). See "Known
#    exceptions" below for the one method where this is documented.
def list_widgets(...) -> list[Widget]: ...
```

## Known exceptions (and why)

A handful of methods deliberately diverge from the convention. They're tracked here so future audits don't try to "fix" them and silently break a downstream consumer.

| Method | Returns | Why we left it |
|---|---|---|
| `projects.list_tag_bindings` | `list[TagBinding]` | Downstream code checks `isinstance(response, list)`, so changing this would be a breaking change. |
| `registry_module.list_commits` | `CommitList` | The endpoint returns a typed envelope with metadata fields beyond just the list of commits. A custom return type is appropriate here. |
| `registry_module.list_versions` | `Iterator[X]` via `iter(list)` | Has a try/except fallback path that calls a different endpoint on failure. See the deviation pattern above. |

Anything public and not in that table should follow the canonical pattern. If you find one that doesn't, either fix it or add it to the table with the compatibility reason.

## How to test a `list_*` method

Mock the transport, then materialize with `list(...)` to assert:

```python
def test_list_workspaces(self):
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "ws-1", "attributes": {"name": "first"}}],
        "meta": {"pagination": {"current-page": 1, "total-pages": 1}},
    }
    self.mock_transport.request.return_value = mock_response

    result = list(self.workspaces_service.list("my-org"))

    assert len(result) == 1
    assert result[0].id == "ws-1"
```

Don't assert `isinstance(result, list)` against the raw return — that asserts on the *idiom* the caller chose, not on the SDK contract. If you want to assert iterator semantics, use `isinstance(result, Iterator)` from `collections.abc`.

## Quick checklist when reviewing a new resource PR

- [ ] Every `list*` method returns `Iterator[X]`, not `list[X]` or `Iterable[X]`
- [ ] `Iterator` is imported from `collections.abc`, not `typing`
- [ ] The body uses the canonical `for item in self._list(path, params=params): yield ...` pattern — including for non-paginated single-shot endpoints
- [ ] Hand-rolled `iter(materialized_list)` only appears if the method has a try/except fallback to a different endpoint (extremely rare — has a docstring note explaining why)
- [ ] If a class defines `def list(...)`, later annotations in that class avoid bare `list[...]` so mypy does not resolve `list` to the method
- [ ] Examples that call the method use `list(client.foo.list_bars(...))` (or stream with a `for` loop) — never assume list semantics on the bare return
- [ ] Unit tests materialize with `list(...)` before asserting length/indexing; invalid-id tests also wrap with `list(...)` to force iteration
- [ ] The README's `## Listing resources` section is still accurate after your change
