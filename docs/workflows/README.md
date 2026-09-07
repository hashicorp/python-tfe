# Workflows

Every method on `TFEClient` is one HTTP request. Real jobs are not: an
API-driven run is eight calls with a polling loop in the middle, a stack
deployment spans five API levels, and the SDK never told you which run states
are final.

`pytfe.workflows` is that missing layer — multi-step operations you call once,
built on the same public API you would have used by hand.

```python
from pytfe import TFEClient
from pytfe.workflows import apply_with_gate, run_from_directory

with TFEClient() as tfe:
    result = run_from_directory(
        tfe, "./terraform", organization="acme", workspace_name="web"
    )

    if result.phase == "awaiting_confirmation":
        print(result.plan)   # +3 ~1 -0 (no destroys)
        print(result.url)    # hand this to a human
        # ...once they approve:
        apply_with_gate(tfe, result.run_id, confirmed=True)
```

Nothing here applies, deletes or approves on its own — see
[Safety model](#safety-model).

## Which workflow do I want?

| I want to… | Use |
|---|---|
| Push local config and run it | `run_from_directory` |
| Run a VCS-connected workspace, no local files | `queue_run` |
| See what *would* change | `speculative_plan`, or `queue_run(refresh_only=True)` for drift |
| Know which attribute changed, and why something is being replaced | `analyze_plan` |
| Apply a run a human already approved | `apply_with_gate(confirmed=True)` |
| Find out why a run failed | `diagnose_run` |
| Create or update a workspace, repeatably | `ensure_workspace` |
| Set variables without clobbering the rest | `ensure_variables` |
| Get outputs after an apply | `read_outputs` |
| List the machines a workspace manages, with their IPs | `state_inventory(include_attributes=True)` |
| Check the health of every workspace in an org | `org_inventory` |
| Roll a setting out across many workspaces | `bulk_update` |
| Rotate a credential everywhere | `bulk_variable_rotate` |
| Move or restore state | `push_state`, `rollback_state`, `migrate_state` |
| Deploy a stack and stop for approval | `stack_fetch_and_run` |
| See which stack deployments are waiting on me | `stack_status` |
| Tear something down | `teardown_workspace`, `teardown_stack` |

Every workflow takes the client as its first argument and returns a Pydantic
result.

## Safety model

**Nothing applies, deletes, approves or overwrites state by default.** This holds
even when you ask nicely, and it is the rule the package is built around.

- A destructive step with neither `confirmed=True` nor a `confirm` callback
  **stops and returns** — it does not raise, and it does not proceed. Branch on
  `result.phase`.
- `confirmed=True` means *the caller asserts a human approved this*. An agent
  sets it only after real human approval.
- A plan that destroys or replaces resources is **refused** unless
  `allow_destroy=True` as well. `confirmed=True` alone is not enough.
- A run whose **policy checks failed** is refused the same way. `policy=` sets
  the strictness: `require_pass` (default), `allow_advisory` (hard failures
  only), or `ignore`.
- There is no `auto_apply=True` anywhere in this package.

Gate rules apply in a fixed order, so a refusal you *cannot* override with
`confirmed=True` is always reported first:

```
refused_destructive  →  refused_policy  →  rejected  →  awaiting_confirmation
```

To hand an agent a client that physically cannot mutate anything:

```python
tfe = TFEClient(TFEConfig(read_only=True))    # or PYTFE_READ_ONLY=1
```

Every write then raises `ReadOnlyViolation`, including the configuration-version
and registry uploads that bypass the normal request path.
`TFEConfig(before_request=hook)` sees every request and may raise to block one.

## Secrets

Terraform data is full of credentials, so two rules apply everywhere:

- **State is redacted by default.** `download_state` and `state_inventory` strip
  every value Terraform flagged in `sensitive_attributes`, plus any root output
  marked `sensitive: true`. `redacted_paths` tells you what was removed, so
  "this resource has no password" is distinguishable from "the password was
  stripped". Pass `redact_sensitive=False` only when you need the secrets.
- **Analysis returns paths, never values.** `analyze_plan` tells you that
  `aws_db_instance.main.password` changed, without telling you what to.

`summary()` never contains a secret on any result, whatever flags built it.

## Errors and waiting

Everything raises `pytfe.errors.TFEError` subclasses, so one `except` catches
the lot:

```python
from pytfe.errors import TFEError, WorkflowTimeout

try:
    result = run_from_directory(tfe, "./terraform", workspace_id=ws_id)
except WorkflowTimeout as exc:
    print("timed out; last saw:", exc.last)   # the last observed object
except TFEError as exc:
    print(exc, "|", exc.hint)                 # hint names the next thing to try
    log.error(exc.to_dict())                  # JSON-serializable, for an agent
```

- Every wait takes `timeout=` and raises `WorkflowTimeout`, carrying the last
  observed object on `.last` — "timed out" alone is not actionable.
- Most errors carry an actionable `.hint`, and `to_dict()` returns
  `{type, message, status, hint, errors}` to feed back to a model.
- `WorkflowTimeout` also subclasses `TimeoutError`, so either `except` works.

## Conventions

| Rule | Detail |
|---|---|
| Identifiers first, options last | Matches the resource layer. |
| Either addressing form | `workspace_id="ws-…"`, or `organization=` + `workspace_name=`. |
| Idempotent `ensure_*` | A second call with the same spec makes **zero write requests** and returns `action="unchanged"`. |
| `dry_run=True` | Reads only, reports `changes`, makes zero write requests. |
| `summary()` on every result | Small, JSON-serializable, no secrets. Use it instead of putting a whole result into an agent's context. |
| Unset means unmanaged | A `WorkspaceSpec` field you never set is never touched; setting it to `None` clears it. |
| `*Spec` inputs reject typos | Unknown field names raise — unlike the SDK's `*Options` models, which silently drop them. |

## Reference

### Runs

| Workflow | Kind | Notes |
|---|---|---|
| `run_from_directory` | destructive (gated) | Upload a directory, plan, stop at the gate. The whole API-driven run. |
| `queue_run` | destructive (gated) | Run a workspace's **existing** configuration — the VCS case — and `refresh_only=True` for drift detection. |
| `ensure_configuration_version` | write | Create, package, upload and wait, without queueing a run. |
| `speculative_plan` | read | Never applies. The safe default for "what would this change?" |
| `wait_for_run` | read | Returns the `Run`, not a bool. `until="plan_done"` or `"terminal"`. |
| `plan_summary` | read | Counts and addresses, from plan JSON or the plan's own counters. |
| `analyze_plan` | read | Which attribute changed, plus `action_reason` so `replace_because_cannot_update` is visible. Paths only, never values. |
| `apply_with_gate` | destructive (gated) | Apply an already-planned run. |
| `diagnose_run` | read | Why a run failed, plus a suggested next step. |
| `resolve_policy_override` | destructive (gated) | Override a soft-failed policy and continue, or discard the run. |
| `cancel_run` | destructive (ungated) | Escalates to force-cancel after `force_after`. Cancelling destroys nothing. |
| `destroy_run` | destructive (gated) | Requires the workspace's `allow_destroy_plan`. |

### Workspaces

| Workflow | Kind | Notes |
|---|---|---|
| `find_workspaces` | read | Server-side filters where they exist, local filters where they do not. |
| `workspace_status` | read | One verdict: `ok`/`drifted`/`errored`/`locked`/`never_run`. |
| `ensure_workspace` | write | Create or converge. Idempotent, `dry_run`. |
| `ensure_variables` | write | Converge variables. Sensitive values are never echoed back. |
| `ensure_variable_set` | write | The set, its variables, and its workspace/project attachments. |
| `lock` / `unlock` | write | Idempotent. `unlock(force=True)` breaks another actor's lock. |
| `clone_workspace` | write | Copies settings and non-sensitive variables; sensitive ones are listed as manual follow-ups. |
| `teardown_workspace` | destructive (gated) | Destroy, then delete. Refuses while resources remain unless `force=True`. |

### State

| Workflow | Kind | Notes |
|---|---|---|
| `read_outputs` | read | Waits for `resources_processed` first — the step most scripts miss. |
| `download_state` | read | **Redacts by default**; `redacted_paths` says what went. |
| `state_inventory` | read | `include_attributes=True` carries each instance's attributes. |
| `push_state` | destructive (gated) | Locks, enforces the serial floor and lineage match, unlocks in a `finally`. |
| `rollback_state` | destructive (gated) | Uses the API's own rollback; no version is ever deleted. |
| `migrate_state` | destructive (gated) | Copies state between workspaces. |

### Fleet

All take `concurrency=` and resolve their work list before fanning out. One
workspace failing never aborts the others — its error is captured on the item.

| Workflow | Kind | Notes |
|---|---|---|
| `bulk_speculative_plan` | read | One directory planned against many workspaces. |
| `bulk_update` | write (gated) | Fleet-wide writes are gated even though single-workspace `ensure_workspace` is not. |
| `bulk_variable_rotate` | write (gated) | Credential rotation. |
| `org_inventory` | read | Every workspace's health; `to_csv()` included. |
| `resource_inventory` | read | "Where is this resource type deployed?" |

### Governance

| Workflow | Kind | Notes |
|---|---|---|
| `onboard_team` | write | Team, members, workspace access. Members are never removed unless `prune_members` **and** `confirmed`. |
| `ensure_policy_set` | write | Find-or-create, then attach workspaces. |
| `ensure_run_task` | write | Organization task plus per-workspace enforcement levels. |
| `ensure_notification` | write | Never logs `url` or `token` — a webhook URL often embeds a secret. |
| `ensure_run_trigger` | write | Converges inbound triggers with set semantics. |
| `ensure_project` | write | Find-or-create, then move workspaces in. |
| `setup_oidc_dynamic_credentials` | write | Writes the `TFC_*_PROVIDER_AUTH` variables. |
| `token_audit` | read | Organization, team and agent tokens with expiry. Values are never returned. |
| `setup_agent_pool` | write | The agent token is returned **once** and is excluded from `summary()`. |

### Stacks

A stack is not a workspace with more nouns: one configuration fans out to N
deployments, each with its own run, plan and approval, and `.tfdeploy.hcl` rules
may auto-approve some. So **results are a matrix keyed by deployment name**, the
gate is per deployment, and the verb is *approve*.

```python
result = stack_fetch_and_run(tfe, "st-abc")
if result.phase == "awaiting_approval":
    for name, d in result.deployments.items():
        print(name, d.status, "GATED" if d.awaiting_approval else "")
    approve_stack_plans(tfe, configuration_id=result.configuration_id, confirmed=True)
```

| Workflow | Kind | Notes |
|---|---|---|
| `stack_status` | read | Latest configuration, the per-deployment matrix, and a health verdict. |
| `wait_for_stack_configuration` | read | `prepared`, `plans_ready` (the moment a human is needed), or `completed`. |
| `stack_fetch_and_run` | destructive (gated) | The whole loop, fetching the configuration from the stack's VCS repository. |
| `stack_run_from_directory` | destructive (gated) | The same loop, uploading the configuration from a local directory. No VCS needed. |
| `speculative_stack_plan` | read | Never approves; doubles as configuration validation. |
| `approve_stack_plans` | destructive (gated) | Re-reads to confirm, and reports **partial** approval. |
| `diagnose_stack_configuration` | read | Separates a prepare failure from a failed deployment step. |
| `teardown_stack` | destructive (gated ×2) | Destroys via `destroy_all`, then deletes. `force=True` orphans resources. |

Three things to plan around:

- **Two ways in.** `stack_fetch_and_run` needs a VCS-backed stack;
  `stack_run_from_directory` uploads from disk and works with any stack.
  Everything after the source is identical. An uploaded directory must carry a
  `.terraform-version` and a `.terraform.lock.hcl` at its root, or the
  configuration fails at prepare — `diagnose_stack_configuration` names the
  missing file.
- **You decide whether a stack plan is safe.** Nothing on the Stacks API reports
  how destructive one is, so pass a `confirm` callback, or fetch the plan with
  `download_artifact` using each deployment's `plan_description_step_id`.
- **Approving clears a whole deployment group**, including a run that arrives
  between the enumeration and the approval. The result carries `enumerated_at`
  and the list it saw.

### Terraform Enterprise and the registry

| Workflow | Kind | Notes |
|---|---|---|
| `admin_bootstrap` | write | Creates the first organization. TFE only. |
| `identity_bootstrap` | write | SAML and SCIM settings. TFE only. |
| `tfe_health` | read | Composed from admin reads — see [Known gaps](#known-gaps). TFE only. |
| `publish_module_version` | write | Packages the directory itself. |
| `publish_provider_version` | write | Provider, version, `SHA256SUMS` + signature, then every platform binary. |
| `no_code_provision` | destructive (gated) | Workspace from a no-code module, then a gated first run. |

## Status classification

Usable on its own, and how you stop writing status strings into your own code:

```python
from pytfe.workflows import is_terminal, phase_of, run_is_confirmable

phase_of("planned_and_finished")   # RunPhase.TERMINAL
phase_of("policy_soft_failed")     # RunPhase.AWAITING_DECISION
phase_of("some_future_status")     # RunPhase.IN_PROGRESS — keep polling
```

`AWAITING_DECISION` is the distinction that matters: a run paused for a policy
override is **not** in progress and will never become terminal on its own. A
poller that treats it as in-progress hangs until timeout.

Prefer `run_is_confirmable(run)`, which reads the wire's own answer and falls
back to the status sets only when the API omitted it. Stacks have the same thing
at four levels in `stack_phases` — `run_is_awaiting_approval`,
`configuration_is_prepared`, and the level-prefixed frozensets.

## Using this from an agent

`pytfe.describe()` lists workflows separately from resources, because they
behave differently — a resource method is one request, a workflow may block for
minutes:

```python
manifest = pytfe.describe()
manifest["workflows"]["run_from_directory"]
# {'signature': '(client, directory, *, ...)',
#  'summary': 'Upload a configuration directory and drive it to a decision.',
#  'blocking': True, 'mutating': True, 'gated': True, 'dry_run': False}
```

Those four flags are what a signature cannot tell you. `pytfe.agent.classify()`
does the same for the resource methods, returning `read`/`write`/`destructive`/
`local` so a harness can gate on it, and `pytfe.llms_txt()` carries a short
orientation for a model working from the installed package.

## Known gaps

| Gap | What it means for you |
|---|---|
| `plans.logs()` / `applies.logs()` are placeholder stubs | `diagnose_run` cannot include log text. It exposes `log_read_url` so you can fetch it, and its structured signals — stage, status, policy failures, errored-state availability — are always populated. |
| `tfe_health` has no backing endpoint | Composed from admin reads, so it reports reachability and queue pressure rather than a server-reported status. |
| No user-token namespace | `token_audit` covers organization, team and agent tokens only, and says so in its warnings. |
| `setup_oidc_dynamic_credentials` writes variables | The `*_oidc_configurations` resources are HYOK-gated and cannot back an idempotent workflow; standard-tier dynamic credentials are the `TFC_*_PROVIDER_AUTH` variables. |

## See also

- [`docs/scenarios/`](../scenarios/) — the prose walkthroughs these workflows encode
- [`examples/workflows/`](../../examples/workflows/) — runnable end-to-end scripts
- [`docs/api/index.md`](../api/index.md) — the underlying resource API
- [`AGENTS.md`](../../AGENTS.md) — conventions for contributing
