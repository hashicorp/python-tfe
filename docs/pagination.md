# Pagination

HCP Terraform list endpoints are paginated. pyTFE hides the page loop behind
Python iterators so callers can stream results naturally.

## The rule

Every public resource method named `list` or `list_*` returns an iterator:

```python
for workspace in client.workspaces.list("my-organization"):
    print(workspace.name)
```

The SDK fetches more pages as the iterator advances.

## Materialize when you need a Python list

Use `list(...)` when you need indexing, `len(...)`, sorting, or multiple passes:

```python
workspaces = list(client.workspaces.list("my-organization"))

print(len(workspaces))
print(workspaces[0].name)
```

## Iterators are single-use

Once an iterator has been consumed, iterating it again returns no items:

```python
workspace_iter = client.workspaces.list("my-organization")

first_pass = list(workspace_iter)
second_pass = list(workspace_iter)  # []
```

Create a new iterator or materialize the results first.

## Iterators are always truthy

Do not use `if client.workspaces.list(...):` to check whether results exist.
Python iterator objects are truthy even if the API would return zero items.

Use:

```python
workspaces = list(client.workspaces.list("my-organization"))
if workspaces:
    print("found workspaces")
```

## Page-size options

Many resources have a `*ListOptions` model with `page_size`, filters, search
fields, or include options. The SDK still returns an iterator; `page_size` only
controls how many items each underlying API request asks for.

```python
from pytfe.models import WorkspaceListOptions

options = WorkspaceListOptions(page_size=50, search="prod")

for workspace in client.workspaces.list("my-organization", options):
    print(workspace.name)
```

Runs support both page size and filters:

```python
from pytfe.models import RunListOptions

options = RunListOptions(page_size=50, status="planned")

for run in client.runs.list("ws-abc123", options):
    print(run.id, run.status)
```

## Common gotchas

- `list` / `list_*` methods are lazy. If an invalid-id check is inside a
  generator method, the exception is raised when you iterate, not when you
  create the iterator.
- Some relationship endpoints are not paginated by the server, but pyTFE still
  exposes them as iterators for a consistent public API.
- A small number of older methods intentionally return concrete lists for
  backward compatibility. Prefer the iterator rule for new code, and check the
  method's return type if you are unsure.
- `page[number]` is managed internally by pyTFE's pagination helper. In normal
  usage, set filters and `page_size`, then iterate.

For contributor implementation rules, see the internal reference
[ITERATORS.md](ITERATORS.md).

