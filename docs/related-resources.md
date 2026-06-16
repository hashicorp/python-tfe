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
   the raw blocks, reachable through four accessors:

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

## Notes

- The raw blocks are **private attributes**, so they never appear in
  `model_dump()` / serialized output and add no public fields. They're an
  untyped escape hatch, not a stable typed API — prefer the typed fields when a
  relation is modelled.
- This complements `extra="allow"`, which retains unknown **attributes**;
  `relationships`/`included` cover unknown **relations**. Together nothing the
  API returns is silently dropped.
- Accessors are provided by `pytfe.models.TFEModel`, which **every
  resource model** now derives from — so `.relationships` / `.included` /
  `.included_by` / `.related` are available everywhere. They're *populated* on
  resources parsed through a dedicated parser; other resources expose the
  accessors but return them empty until their parser is wired to capture the
  raw blocks.
