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

### Workspaces

| Workflow | Kind | Notes |
|---|---|---|
| `find_workspaces` | read | Server-side filters where they exist, local filters where they do not. |
| `workspace_status` | read | One `health` verdict: `ok`/`drifted`/`errored`/`locked`/`never_run`. |
| `ensure_workspace` | write | Create or converge. Idempotent, `dry_run`. |
| `ensure_variables` | write | Converge variables. Sensitive values are never echoed back. |

### State

| Workflow | Kind | Notes |
|---|---|---|
| `read_outputs` | read | Waits for `resources_processed` first — the step most scripts miss. |

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

## Known gaps

| Gap | Effect |
|---|---|
| `plans.logs()` / `applies.logs()` are placeholder stubs returning `""` | `diagnose_run` cannot include a log excerpt. It records a warning and exposes `log_read_url` so a caller can fetch the log directly. Its structured signals — stage, status, policy failures, errored-state availability — are derived without logs and are always populated. |
| `registry_modules.upload()` raises `NotImplementedError` | No module-publishing workflow ships. |

## See also

- [`docs/scenarios/`](../scenarios/) — the prose walkthroughs these workflows encode
- [`examples/workflows/`](../../examples/workflows/) — runnable end-to-end scripts
- [`AGENTS.md`](../../AGENTS.md) — conventions for contributing
