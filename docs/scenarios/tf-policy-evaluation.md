# Scenario: tf-policy evaluation and override

This scenario covers reading tf-policy compliance results for a run, filtering
policy-set outcomes, and overriding a `mandatory_overridable` failure. tf-policy
is HCP Terraform's native policy-as-code engine (distinct from Sentinel and
OPA) — evaluations are attached to a run's stages (Init/Plan/Apply) rather
than created directly, so this scenario reads and reacts to results rather
than authoring them.

> tf-policy is HCP Terraform only and gated behind an organization-level
> feature flag while in private beta. If policy-set creation with
> `kind=PolicyKind.TFPOLICY` fails validation, confirm the flag is enabled for
> your organization before assuming a client-side issue.

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

The workspace whose runs you're inspecting must be running a Terraform
version tf-policy supports (`>= 1.16.0-alpha20260626` at the time of writing —
check with your organization admin, since this is a fast-moving minimum on a
beta feature). Evaluations on an older version come back `errored` with an
`incompatible_terraform_version_error`, not a client-side exception.

## Step 1: List a run's tf-policy evaluations

A run has one evaluation per applicable stage, and each stage evaluates a
different scope (see [Evaluation and enforcement](https://developer.hashicorp.com/terraform/policy#evaluation-and-enforcement)):

- **Init** — provider and module policies, evaluated during workspace
  initialization, before Terraform installs providers or modules.
- **Plan** — resource policies whose referenced attributes are known at plan
  time, evaluated against the proposed plan before any infrastructure
  changes.
- **Apply** — resource policies that reference computed values (ARNs, IDs,
  and similar) that stay unknown until Terraform actually applies; these
  necessarily run after infrastructure changes are made.

An Init-stage evaluation only has an empty result if your policy set has no
provider/module policies — don't assume `list()[0]` is the interesting one
for a resource-policy scenario; find the evaluation whose stage matches what
your policy actually targets.

```python
from pytfe import TFEClient

client = TFEClient()
run_id = "run-abc123"

evaluations = list(client.tf_policy_evaluations.list(run_id))
for e in evaluations:
    print(e.id, e.stage_type, e.status, e.result_count)
```

## Step 2: Read one evaluation, with outcomes sideloaded

```python
from pytfe.models import TfPolicyEvaluationListOptions

opts = TfPolicyEvaluationListOptions(include="tf_policy_set_outcomes")
evaluation = client.tf_policy_evaluations.read(evaluations[0].id, options=opts)

print(evaluation.status, evaluation.actions, evaluation.permissions)
```

`evaluation.actions.is_overridable` and `evaluation.permissions.can_override`
both need to be `True` before an override call will succeed — check them
before attempting one rather than relying on the error path.

## Step 3: Inspect policy-set outcomes and diagnostics

```python
for outcome in client.tf_policy_evaluations.list_set_outcomes(evaluation.id):
    print(outcome.policy_set_name, outcome.result_count)
    for policy in outcome.outcomes:
        print(" ", policy.policy_name, policy.status, policy.enforcement_level)
        for diag in policy.diagnostics:
            print("    diag:", diag.summary, [r.resource_name for r in diag.resources])
```

Filter to just the failures, or just one enforcement level:

```python
from pytfe.models import TfPolicySetOutcomeListOptions

failed = client.tf_policy_evaluations.list_set_outcomes(
    evaluation.id,
    options=TfPolicySetOutcomeListOptions(filter_status="failed"),
)

mandatory_overridable = client.tf_policy_evaluations.list_set_outcomes(
    evaluation.id,
    options=TfPolicySetOutcomeListOptions(
        filter_enforcement_level="mandatory_overridable"
    ),
)
```

You can also read a single outcome directly if you already have its ID (e.g.
from a webhook payload) without listing through the evaluation:

```python
outcome = client.tf_policy_set_outcomes.read("tfpsout-abc123")
```

## Step 4: Override a `mandatory_overridable` failure

```python
from pytfe.models import TfPolicyEvaluationOverrideOptions

result = client.tf_policy_evaluations.override(
    evaluation.id,
    TfPolicyEvaluationOverrideOptions(comment="Approved by platform-team — ticket OPS-123"),
)
print(result.status)  # "overridden"
```

`comment` is optional — omit `options` entirely to override with no comment.
The override only succeeds while the evaluation is in `awaiting_override`
status; calling it again on an already-overridden evaluation raises `TFEError`
rather than silently no-op'ing, so guard on `status` first if you're looping
over a batch.

Override is only available for **Plan-stage** evaluations. Init and Apply
stage evaluations are never overridable, regardless of enforcement level or
`AWAITING_OVERRIDE` status — check `stage_type == TfPolicyStage.PLAN` (in
addition to `actions.is_overridable`) before attempting one:

```python
from pytfe.models import TfPolicyEvaluationStatus, TfPolicyStage

overridable = [
    e for e in evaluations
    if e.status == TfPolicyEvaluationStatus.AWAITING_OVERRIDE
    and e.stage_type == TfPolicyStage.PLAN
    and e.actions and e.actions.is_overridable
]
for e in overridable:
    client.tf_policy_evaluations.override(e.id)
```

## Step 5: Gate a downstream workflow on compliance

The read-only surface above is enough to build a pre-flight compliance gate —
this is the pattern the `hashicorp.terraform` Ansible collection's
`tf_policy_evaluation_info` module wraps:

```python
evaluations = list(client.tf_policy_evaluations.list(run_id))
non_compliant = [
    e for e in evaluations
    if e.status in (
        TfPolicyEvaluationStatus.FAILED,
        TfPolicyEvaluationStatus.ERRORED,
        TfPolicyEvaluationStatus.AWAITING_OVERRIDE,
    )
]
if non_compliant:
    raise SystemExit(f"Run {run_id} is not tf-policy compliant: {non_compliant}")
```

## Creating a `kind=tfpolicy` policy set

tf-policy policy sets are primarily supported as **VCS-connected** policy
sets — commit your `.policy.hcl` files to a repository and connect it via
`vcs_repo` on `PolicySetCreateOptions`, the same pattern as Sentinel/OPA
policy sets. That's the supported path for anything beyond local iteration.

For quick local testing without setting up a VCS/OAuth connection, the
direct-upload path below also works and is what this scenario uses:

```python
from pytfe.models import PolicyKind, PolicySetCreateOptions

policy_set = client.policy_sets.create(
    "my-organization",
    PolicySetCreateOptions(
        name="tfpolicy-guardrails",
        kind=PolicyKind.TFPOLICY,
        policy_tool_version="0.1.0",
        agent_enabled=True,
        overridable=True,
    ),
)

version = client.policy_set_versions.create(policy_set.id)
client.policy_set_versions.upload(version, "./policies")  # directory, not a tarball
```

`client.policy_set_versions.upload()` takes the `PolicySetVersion` object
itself (it reads the upload link off it), not a URL string — this differs
from `client.configuration_versions.upload()`, which does take the upload URL
directly. Easy to transpose the two if you're working with both in the same
script.

If your `.policy.hcl` files live in a subdirectory of the uploaded archive
rather than at its root, set `policies_path` on the policy set to point at
that subdirectory:

```python
from pytfe.models import PolicySetUpdateOptions

client.policy_sets.update(
    policy_set.id,
    PolicySetUpdateOptions(policies_path="policies"),
)
```

Without `policies_path` set, the engine looks for policy files at the
archive root. A nested layout with `policies_path` left unset is accepted
without error and silently evaluates zero policies — every evaluation
"passes" with `result_count` at all zeros, indistinguishable from a
genuinely compliant run until you notice nothing was actually checked.

## Cleanup

```python
client.policy_sets.delete(policy_set.id)
```

Evaluations themselves aren't deletable - they're immutable records tied to
the run that produced them and are cleaned up when the run/workspace is.

## Wire-format notes

- `TfPolicyEnforcementLevel.MANDATORY_OVERRIDABLE` serializes as
  `"mandatory_overridable"` - underscore, unlike the hyphenated style used
  elsewhere in the JSON:API surface.
- The `outcomes` array on `TfPolicySetOutcome`, and everything nested inside
  it (`PolicyOutcome`, `Diagnostic`, `OutcomeResource`, `TraversalValue`,
  `PassedResource`), is **snake_case on the wire** rather than dash-cased.
  The backend serializes that column verbatim from a stored value rather than
  passing it through the usual attribute-name transform, so the SDK models
  read it as-is — this is intentional, not a bug, if you're ever comparing
  raw JSON against the rest of the API's dash-case convention.
- `override()`'s request body is a bare `{"comment": "..."}`, not a JSON:API
  `{"data": {"attributes": {...}}}` envelope - the SDK handles this for you,
  but it's worth knowing if you're debugging against raw HTTP logs.
