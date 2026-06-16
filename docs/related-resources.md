# Related resources (`?include=`, relationships & included)

HCP Terraform speaks [JSON:API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs#inclusion-of-related-resources).
A resource carries a **`relationships`** block — linkage references (`type` + `id`)
for every related resource — and, when you request `?include=`, the response also
carries a top-level **`included`** array holding the *full bodies* of those
relations.

pyTFE handles this on two levels:

1. **Typed hydration** — relationships the SDK models are parsed into typed
   fields, and when you pass `include=...` those fields are filled from
   `included`. For example:

   ```python
   from pytfe import TFEClient
   from pytfe.models.workspace import WorkspaceReadOptions, WorkspaceIncludeOpt

   client = TFEClient()
   ws = client.workspaces.read_by_id_with_options(
       "ws-abc123",
       WorkspaceReadOptions(include=[WorkspaceIncludeOpt.OUTPUTS, WorkspaceIncludeOpt.PROJECT]),
   )

   for o in ws.outputs:          # fully hydrated from `included`
       print(o.name, o.value)
   print(ws.project.name)        # not just the id — the real project record
   ```

2. **Lossless raw access** — even relations the SDK does **not** model as typed
   fields are never lost. Every resource on the relationship-parsing path keeps
   the raw blocks, reachable through these accessors:

   | Accessor | Returns |
   |---|---|
   | `model.relationships` | the raw `relationships` block (dict) |
   | `model.included` | the raw `included` array (list of dicts) |
   | `model.has_relationships` | `True` if a `relationships` block was on the wire |
   | `model.has_included` | `True` if a top-level `included` array was on the wire |
   | `model.included_by(type, id)` | one included object matched by `type` + `id` |
   | `model.related(name)` | the references of relationship `name`, each resolved to its full included body (or left as a bare `{type, id}` ref if it wasn't `include`-d) |

   `.relationships` / `.included` are always present and stably typed — they
   return `{}` / `[]` whether the block was *empty* or *absent*. The API genuinely
   distinguishes the two (SSH keys omit `relationships` entirely; `included`
   only appears with `?include=`), so `has_relationships` / `has_included` tell
   you which — without making the data accessors conditionally vanish.

   `model.related(name)` takes the raw relationship key from
   `model.relationships`, not the Python field name. These keys often contain
   hyphens: use `ws.related("current-run")`, not `ws.related("current_run")`.

   ```python
   # Reach a related resource the SDK doesn't expose as a typed field:
   readme = ws.included_by("workspace-readme", "rm-1")
   if readme:
       print(readme["attributes"]["raw-markdown"])

   # Or resolve a whole relationship by name:
   for out in ws.related("outputs"):
       print(out["attributes"]["name"], out["attributes"]["value"])

   # Enumerate every relationship the API returned, modelled or not:
   print(list(ws.relationships))   # e.g. ['organization', 'project', 'outputs', ...]
   ```

   A read-only raw-access example using an unmodelled organization relation:

   ```python
   from pytfe.models.organization import OrganizationIncludeOpt, OrganizationReadOptions

   org = client.organizations.read(
       "my-org",
       OrganizationReadOptions(
           include=[OrganizationIncludeOpt.ORGANIZATION_SUBSCRIPTION],
       ),
   )

   # `subscription` is not a typed Organization field, but it is still available.
   for subscription in org.related("subscription"):
       print(subscription["attributes"])

   # included_by() is useful when you already have the relationship ref.
   ref = org.relationships["subscription"]["data"]
   subscription = org.included_by(ref["type"], ref["id"])
   if subscription:
       print(subscription["attributes"])
   ```

## Which should I use — the typed field or the raw accessor?

**The one rule:** when a typed relationship is present, it carries **at least
the `id`**. Pass `?include=<relation>` to fill in the rest.

```python
from pytfe.models.policy_set import PolicySetReadOptions, PolicySetIncludeOpt

ps = client.policy_sets.read("polset-abc")
if ps.current_version:
    ps.current_version.id        # present on the id-only stub
    ps.current_version.source    # None — you didn't ask for it

ps = client.policy_sets.read_with_options(
    "polset-abc",
    PolicySetReadOptions(include=[PolicySetIncludeOpt.POLICY_SET_CURRENT_VERSION]),
)
if ps.current_version:
    ps.current_version.source    # now hydrated from `included`
```

* **Prefer the typed field** (`ps.current_version`, `ws.outputs`, `team.users`,
  `org_membership.user`, `run_event.actor`) whenever the relation is modelled — it's
  type-checked and stable, and `?include=<relation>` fills it on single-resource
  reads. This works the *same way for every resource that models the relation*:
  there are no single-resource read paths where a typed field silently stays a
  stub after you `?include=` it.
* **Use the raw accessors** (`model.related(name)`, `model.included_by(type, id)`)
  only for relations the SDK does **not** model as a typed field — e.g. an
  organization's `subscription`, or a workspace `readme`. The data is still returned
  by `?include=`, just untyped.

You never need both for the same relation: if a typed field exists, `?include=` fills
it; if it doesn't, the raw accessors are the way in.

## Per-resource coverage

`?include=` support by single-resource `read*` (see each resource's `*IncludeOpt`):

| Behaviour | Resources |
|---|---|
| **Typed hydration** — `include` fills the typed field | `workspaces`, `runs`, `agent_pools`, `stack_configuration`, `teams`, `task_stages`, `policy_set`, `organization_membership`, `variable_set`, `run_event`, `no_code_modules.read_variables` |
| **Raw capture** — relation not modelled as a typed field; reach it via `related()` / `included_by()` | `organizations` (`subscription`), `state_versions`, `agents`, `configuration_version`, `oauth_client`, `projects`, `query_run`, `registry_provider`, `run_task` |
| **List-only** — `?include=` exists only on the `list` endpoint | `registry_module`, `run_trigger`, `policy_check` |

In every case the **`relationships`** block and raw accessors are populated,
so unmodelled relations are never lost. **List endpoints** currently capture
`relationships` but not `included` (the page-level `included` array is not yet threaded
through pagination — in progress).

For list endpoints, this means `model.has_relationships` can be `True`, but
`model.has_included` is currently `False` even when the list options expose an
`include` parameter. Typed relations returned from list calls therefore remain
id-only stubs until you read a single resource with the matching read options.

## Notes

- The raw blocks are **private attributes**, so they never appear in
  `model_dump()` / serialized output and add no public fields. They're an
  untyped escape hatch, not a stable typed API — prefer the typed fields when a
  relation is modelled.
- This complements `extra="allow"`, which retains unknown **attributes**;
  `relationships`/`included` cover unknown **relations**. Together nothing the
  API returns is silently dropped.
- Accessors are provided by `pytfe.models.TFEModel`, which top-level
  resource models derive from — so `.relationships` / `.included` /
  `.included_by` / `.related` are available everywhere. They're *populated* on
  single-resource `read*` calls: the `relationships` block on reads that go
  through a relationship-capturing parser, and the `included` array whenever you
  pass `?include=`. **List endpoints** currently populate `relationships` but not
  `included` — the shared top-level `included` array is not yet threaded through
  pagination (in progress).
