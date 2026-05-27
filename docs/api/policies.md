# Policies

pyTFE supports policy libraries, policy sets, policy set parameters, policy set
versions, policy checks, policy evaluations, and policy set outcomes.

Upstream docs:

- Policies: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policies
- Policy sets: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets
- Policy checks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks
- Policy evaluations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-evaluations

Examples:

- [policy.py](../../examples/policy.py)
- [policy_set.py](../../examples/policy_set.py)
- [policy_check.py](../../examples/policy_check.py)
- [policy_evaluation.py](../../examples/policy_evaluation.py)

## Policies

| Method | Purpose |
|---|---|
| `client.policies.list(organization, options=None)` | Iterate policies. |
| `client.policies.read(policy_id)` | Read a policy. |
| `client.policies.create(organization, options)` | Create a policy. |
| `client.policies.update(policy_id, options)` | Update a policy. |
| `client.policies.delete(policy_id)` | Delete a policy. |
| `client.policies.upload(policy_id, content)` | Upload policy content. |
| `client.policies.download(policy_id)` | Download policy content. |

## Policy sets

| Method | Purpose |
|---|---|
| `client.policy_sets.list(organization, options=None)` | Iterate policy sets. |
| `client.policy_sets.read(policy_set_id)` | Read a policy set. |
| `client.policy_sets.read_with_options(policy_set_id, options)` | Read with includes. |
| `client.policy_sets.create(organization, options)` | Create a policy set. |
| `client.policy_sets.update(policy_set_id, options)` | Update a policy set. |
| `client.policy_sets.delete(policy_set_id)` | Delete a policy set. |
| `client.policy_sets.add_policies(...)` / `remove_policies(...)` | Attach or remove policies. |
| `client.policy_sets.add_workspaces(...)` / `remove_workspaces(...)` | Attach or remove workspaces. |
| `client.policy_sets.add_projects(...)` / `remove_projects(...)` | Attach or remove projects. |
| `client.policy_sets.add_workspace_exclusions(...)` / `remove_workspace_exclusions(...)` | Manage workspace exclusions. |
| `client.policy_sets.add_project_exclusions(...)` / `remove_project_exclusions(...)` | Manage project exclusions. |

## Policy checks

Policy checks are attached to runs:

```python
for check in client.policy_checks.list("run-abc123"):
    print(check.id, check.status)
```

Override a policy check only when your token has permission:

```python
client.policy_checks.override("polchk-abc123")
```

## Policy set parameters and versions

- `client.policy_set_parameters` manages parameter values for policy sets.
- `client.policy_set_versions` creates and uploads policy set versions.
- `client.policy_set_outcomes` reads outcome data.
- `client.policy_evaluations` lists policy evaluations.

