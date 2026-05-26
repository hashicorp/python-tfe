# Scenario: Policy enforcement

This scenario shows a basic policy workflow: create a policy, create a policy
set, attach it to a workspace or project, inspect policy checks, and override
when permitted.

Upstream docs:

- Policies: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policies
- Policy sets: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets
- Policy checks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
- Policy evaluations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-evaluations

## Create a policy

```python
from pytfe import TFEClient
from pytfe.models import (
    EnforcementLevel,
    Policy,
    PolicyCreateOptions,
    PolicyKind,
    PolicySetAddPoliciesOptions,
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetRemovePoliciesOptions,
    Workspace,
)


client = TFEClient()
organization = "my-organization"

policy = client.policies.create(
    organization,
    PolicyCreateOptions(
        name="require-tags",
        kind=PolicyKind.OPA,
        query="data.terraform.main.deny",
        enforcement_level=EnforcementLevel.ENFORCEMENT_ADVISORY,
        description="Example policy managed by pyTFE",
    ),
)

client.policies.upload(policy.id, b'package terraform.main\n\ndeny := []\n')
```

## Create a policy set and attach resources

```python
policy_set = client.policy_sets.create(
    organization,
    PolicySetCreateOptions(
        name="platform-guardrails",
        description="Platform policy set",
        kind=PolicyKind.OPA,
        Global=False,
    ),
)

client.policy_sets.add_policies(
    policy_set.id,
    PolicySetAddPoliciesOptions(policies=[Policy(id=policy.id)]),
)

client.policy_sets.add_workspaces(
    policy_set.id,
    PolicySetAddWorkspacesOptions(workspaces=[Workspace(id="ws-abc123")]),
)
```

Use project relationships when every workspace in a project should share the
same policy set.

## Inspect checks on a run

```python
for check in client.policy_checks.list("run-abc123"):
    print(check.id, check.status)
```

Read logs for a check:

```python
logs = client.policy_checks.logs("polchk-abc123")
print(logs)
```

## Override when allowed

```python
client.policy_checks.override("polchk-abc123")
```

Overrides require server-side permission and policy configuration that allows
overrides.

## Cleanup

```python
client.policy_sets.remove_policies(
    policy_set.id,
    PolicySetRemovePoliciesOptions(policies=[Policy(id=policy.id)]),
)
client.policy_sets.delete(policy_set.id)
client.policies.delete(policy.id)
```
