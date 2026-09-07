# Workflows

`pytfe.workflows` is the layer between "one method, one HTTP request" and the
multi-step jobs people actually do. Every resource method in pytfe is a single
round trip; an API-driven run is eight calls with a polling loop in the middle,
and until now the SDK never said which run states are final.

Everything here is built strictly on the public API — `client.<resource>.<verb>`,
typed options models, typed errors. It never touches the transport or the
pagination helper, which `tests/contract/test_isolation.py` enforces.

## Why this exists

Before this package, the repository contained:

| | |
|---|---|
| Hand-rolled polling loops | 10, across 7 files |
| Blind `sleep`-then-read sites | 12, across 5 example files |
| Definitions of "terminal run state" | 4, mutually inconsistent |
| Waiters shipped in the SDK | 0 |

`RunStatus` has 33 members and no way to ask whether one is final, so four call
sites each invented their own set — and one of them
(`examples/oidc_aws_e2e.py:509`) omits `cost_estimated` and `policy_checked`
from a confirmable set that the same file gets right 50 lines earlier. Another
set contains `force_canceled`, which is not a `RunStatus` member at all.

The gap was never that people could not poll. It was that the SDK never told
them what to poll for.

## Quick start

```python
from pytfe import TFEClient
from pytfe.workflows import run_from_directory, apply_with_gate

with TFEClient() as tfe:
    result = run_from_directory(
        tfe, "./terraform", organization="acme", workspace_name="web"
    )

    if result.phase == "awaiting_confirmation":
        print(result.plan)   # +3 ~1 -0 (no destroys)
        print(result.url)    # hand this to a human

        # ...after a human approves:
        apply_with_gate(tfe, result.run_id, confirmed=True)
```

## Safety model

Nothing applies, deletes, or overrides by default. This is the rule the whole
package is built around, and it holds even when a caller asks nicely.

- A destructive step with neither `confirmed=True` nor a `confirm` callback
  **stops and returns** `phase="awaiting_confirmation"`. It does not raise, and
  it does not proceed.
- `confirmed=True` means *the caller asserts a human approved this*. An agent
  sets it only after explicit human approval.
- A plan containing destroys or replaces is **refused** unless
  `allow_destroy=True` is passed as well — `confirmed=True` alone is not enough.
- There is no `auto_apply=True` anywhere in this package.

To hand an agent a client that physically cannot mutate anything:

```python
tfe = TFEClient(TFEConfig(read_only=True))    # or PYTFE_READ_ONLY=1
```

Every write raises `ReadOnlyViolation`, including configuration-version and
registry-module uploads, which bypass `HTTPTransport.request` and would slip
past a naive gate. `TFEConfig(before_request=hook)` sees every request, and the
hook may raise to block one.

## Conventions

| Rule | Detail |
|---|---|
| Identifiers first, options last | Matches the resource layer. |
| Either addressing form | `workspace_id="ws-…"`, or `organization=` + `workspace_name=`. |
| Idempotent `ensure_*` | A second call with the same spec makes zero write requests and returns `action="unchanged"`. |
| `dry_run=True` | Reads only, reports `changes`, makes zero write requests. |
| Explicit timeouts | Every wait takes `timeout=` and raises `WorkflowTimeout`, which carries the last observed value on `.last`. |
| `summary()` on every result | Small, JSON-serializable, never contains secrets. Use it instead of dumping a whole result into an agent's context. |
| Unset means unmanaged | A `WorkspaceSpec` field you never set is never touched; setting it to `None` clears it. |
| Errors are typed | Everything subclasses `TFEError`, so `except TFEError:` keeps working. Most carry an actionable `.hint`. |

## Workflows

### Runs

| Workflow | Kind | Notes |
|---|---|---|
| `run_from_directory` | destructive (gated) | Upload a directory, plan, stop at the gate. The whole API-driven run. |
| `speculative_plan` | read | Never applies. The safe default for "what would this change?" |
| `wait_for_run` | read | Returns the `Run`, not a bool. `until="plan_done"` or `"terminal"`. |
| `plan_summary` | read | Counts and addresses from plan JSON, falling back to plan attributes. |
| `apply_with_gate` | destructive (gated) | Apply an already-planned run. |
| `diagnose_run` | read | Why a run failed, plus a suggested next step. |
| `resolve_policy_override` | destructive (gated) | Override a soft-failed policy and continue, or discard the run. |
| `cancel_run` | destructive (ungated) | Escalates to force-cancel after `force_after`. Cancelling destroys nothing, so it is not gated. |
| `destroy_run` | destructive (gated) | Requires the workspace's `allow_destroy_plan`. Gated unconditionally — there is no `allow_destroy` to set, because destruction is the point. |

### Workspaces

| Workflow | Kind | Notes |
|---|---|---|
| `find_workspaces` | read | Server-side filters where they exist, local filters where they do not. |
| `workspace_status` | read | One `health` verdict: `ok`/`drifted`/`errored`/`locked`/`never_run`. |
| `ensure_workspace` | write | Create or converge. Idempotent, `dry_run`. |
| `ensure_variables` | write | Converge variables. Sensitive values are never echoed back. |

### Workspaces (lifecycle)

| Workflow | Kind | Notes |
|---|---|---|
| `lock` / `unlock` | write | Idempotent. `unlock(force=True)` breaks another actor's lock. |
| `ensure_variable_set` | write | Converges the set, its variables, and its workspace/project attachments. |
| `clone_workspace` | write | Copies settings and non-sensitive variables. Sensitive values cannot be read back, so each one is listed in `manual_followups`. |
| `teardown_workspace` | destructive (gated) | Destroy, then delete. Refuses while resources remain unless `force=True`. |

### State

| Workflow | Kind | Notes |
|---|---|---|
| `read_outputs` | read | Waits for `resources_processed` first — the step most scripts miss. |
| `download_state` | read | `summary()` omits the state body; it is large and may hold secrets. |
| `state_inventory` | read | Prefers the workspace-resources endpoint over downloading state. |
| `push_state` | destructive (gated) | Locks, enforces the serial floor and lineage match, unlocks in a `finally`. Reports `still_locked` if the unlock fails. |
| `rollback_state` | destructive (gated) | Uses the API's own rollback endpoint. No version is ever deleted. |
| `migrate_state` | destructive (gated) | Copies state between workspaces; warns if the target already has state. |

### Fleet

All take `concurrency` and resolve their work list on the calling thread before
fanning out. One workspace failing never aborts the others.

| Workflow | Kind | Notes |
|---|---|---|
| `bulk_speculative_plan` | read | Plans one directory against many workspaces. Never applies. |
| `bulk_update` | write (gated) | Fleet-wide writes are gated even though single-workspace `ensure_workspace` is not. |
| `bulk_variable_rotate` | write (gated) | Built for credential rotation. |
| `org_inventory` | read | Every workspace's health; renders as CSV via `to_csv()`. |
| `resource_inventory` | read | "Where is this resource type deployed?" across an organization. |

### Governance

| Workflow | Kind | Notes |
|---|---|---|
| `onboard_team` | write | Team, members, workspace access. Members are never removed unless `prune_members=True` and `confirmed=True`. |
| `ensure_policy_set` | write | Find-or-create, then attach workspaces. |
| `ensure_run_task` | write | Organization task plus per-workspace enforcement levels. |
| `ensure_notification` | write | Never logs `url` or `token` — a webhook URL routinely embeds a secret. |
| `ensure_run_trigger` | write | Converges inbound triggers with set semantics. |
| `ensure_project` | write | Find-or-create, then move workspaces in. |
| `setup_oidc_dynamic_credentials` | write | Writes the `TFC_*_PROVIDER_AUTH` env variables. See the note below. |
| `token_audit` | read | Organization, team and agent tokens with expiry. Values are never returned. |
| `setup_agent_pool` | write | The agent token is returned **once** on the result and excluded from `summary()`. |

### Terraform Enterprise only

Each refuses to run against HCP Terraform.

| Workflow | Kind | Notes |
|---|---|---|
| `admin_bootstrap` | write | Creates the first organization. The admin API has no org-create endpoint, so the normal one is used. |
| `identity_bootstrap` | write | SAML and SCIM settings. |
| `tfe_health` | read | Composed from admin reads — see the note below. |

### Registry

| Workflow | Kind | Notes |
|---|---|---|
| `publish_module_version` | write | Packages the directory itself, because `registry_modules.upload()` raises `NotImplementedError`. |
| `no_code_provision` | destructive (gated) | Creates a workspace from a no-code module and gates its first run. |
| `publish_provider_version` | — | Raises `CoreGap`. See the gaps table below. |

## Run-status classification

The piece with the highest value per line. Every `RunStatus` member belongs to
exactly one phase, and a test asserts it, so a new upstream status fails CI
instead of silently making a waiter spin until timeout.

```python
from pytfe.workflows import phase_of, is_terminal, run_is_confirmable

phase_of("planned_and_finished")   # RunPhase.TERMINAL
phase_of("policy_soft_failed")     # RunPhase.AWAITING_DECISION
phase_of("some_future_status")     # RunPhase.IN_PROGRESS - keep polling
```

`AWAITING_DECISION` is the distinction that matters and that no hand-rolled set
in this repository made: a run paused for a policy override is **not** in
progress and will never become terminal on its own. A waiter that treats it as
in-progress hangs until timeout.

Prefer `run_is_confirmable(run)`, which reads `run.actions.is_confirmable` from
the wire and only falls back to the status sets when the API omitted the block.

## Packaging configuration directories

`package_directory` applies Terraform's own exclusions (`.git/`, `.terraform/`,
any `.terraformignore`, with `.terraform/modules/` re-included) and produces a
byte-reproducible archive.

This is not the same as `pytfe.utils.pack_contents`, which
`configuration_versions.upload` uses: that walks the whole tree with no
exclusions, so it uploads `.git/`, cached provider binaries, and any
`*.auto.tfvars` secrets file. `run_from_directory` uses `package_directory` and
the public `upload_tar_gzip` instead.

## Discovery from an installed wheel

```python
import pytfe

manifest = pytfe.describe()
manifest["workflows"]["run_from_directory"]
# {'signature': '(client, directory, *, ...)',
#  'summary': 'Upload a configuration directory and drive it to a decision.',
#  'blocking': True, 'mutating': True, 'gated': True, 'dry_run': False}
```

Workflows are reported as a sibling key to `resources`, not mixed into it: a
resource method is one request, a workflow may block for minutes. The
`blocking`/`mutating`/`gated`/`dry_run` flags are the things a signature cannot
tell you. `pytfe.llms_txt()` carries the same orientation in prose.

## Two workflows that differ from the obvious design

**`setup_oidc_dynamic_credentials` writes variables, not OIDC configurations.**
The `aws_/azure_/gcp_/vault_oidc_configurations` namespaces look like the right
target and are not: they are gated behind the HYOK entitlement, they are four
disjoint namespaces with four disjoint option models, and none of them exposes
`list()` — so they cannot back an idempotent, single-entry-point workflow.
Standard-tier dynamic credentials are the `TFC_*_PROVIDER_AUTH` environment
variables, exactly as `docs/scenarios/oidc-dynamic-credentials.md` describes.
The per-provider variable names live in one table, `OIDC_VARIABLES`.

**`tfe_health` is composed, not reported.** There is no health or ping endpoint
in the API, and `client.admin` has no general-settings namespace — only the
eleven enumerated sub-namespaces. So `tfe_health` assembles a summary from the
admin endpoints that do exist (organizations, users, runs, Terraform versions).
It tells you reachability and queue pressure, not a server-reported status.

## Known gaps

| Gap | Effect |
|---|---|
| `plans.logs()` / `applies.logs()` are placeholder stubs returning `""` | `diagnose_run` cannot include a log excerpt. It records a warning and exposes `log_read_url` so a caller can fetch the log directly. Its structured signals — stage, status, policy failures, errored-state availability — are derived without logs and are always populated. |
| `registry_modules.upload()` raises `NotImplementedError` | `publish_module_version` packages the directory itself and uses the public `upload_tar_gzip`. |
| No method uploads provider SHASUMS, signatures or platform binaries | `publish_provider_version` raises `CoreGap`. It needs new methods in `resources/`. |
| `client.users` exposes no user-token namespace | `token_audit` cannot enumerate user API tokens, and says so in its warnings. |

## See also

- [`docs/scenarios/`](../scenarios/) — the prose walkthroughs these workflows encode
- [`examples/workflows/`](../../examples/workflows/) — runnable end-to-end scripts
- [`AGENTS.md`](../../AGENTS.md) — conventions for contributing
