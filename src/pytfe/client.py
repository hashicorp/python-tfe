# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ._http import HTTPTransport
from .config import TFEConfig
from .resources.admin import AdminClient
from .resources.agent_pools import AgentPools
from .resources.agents import Agents, AgentTokens
from .resources.apply import Applies
from .resources.cidr_range_list import CIDRRangeLists, CIDRRanges
from .resources.comment import Comments
from .resources.configuration_version import ConfigurationVersions
from .resources.cost_estimate import CostEstimates
from .resources.explorer import Explorer
from .resources.github_app_installation import GitHubAppInstallations
from .resources.ip_ranges import IPRanges
from .resources.no_code_module import NoCodeModules
from .resources.notification_configuration import NotificationConfigurations
from .resources.oauth_client import OAuthClients
from .resources.oauth_token import OAuthTokens
from .resources.oidc_configurations import (
    AWSOIDCConfigurations,
    AzureOIDCConfigurations,
    GCPOIDCConfigurations,
    VaultOIDCConfigurations,
)
from .resources.org_token_ttl_policy import OrganizationTokenTTLPolicies
from .resources.organization_audit_configuration import OrganizationAuditConfigurations
from .resources.organization_membership import OrganizationMemberships
from .resources.organization_tags import OrganizationTags
from .resources.organization_token import OrganizationTokens
from .resources.organizations import Organizations
from .resources.plan import Plans
from .resources.plan_export import PlanExports
from .resources.policy import Policies
from .resources.policy_check import PolicyChecks
from .resources.policy_evaluation import PolicyEvaluations
from .resources.policy_set import PolicySets
from .resources.policy_set_outcome import PolicySetOutcomes
from .resources.policy_set_parameter import PolicySetParameters
from .resources.policy_set_version import PolicySetVersions
from .resources.projects import Projects
from .resources.query_run import QueryRuns
from .resources.registry import Registry
from .resources.registry_module import RegistryModules
from .resources.registry_provider import RegistryProviders
from .resources.registry_provider_platform import RegistryProviderPlatforms
from .resources.registry_provider_version import RegistryProviderVersions
from .resources.reserved_tag_key import ReservedTagKeys
from .resources.run import Runs
from .resources.run_event import RunEvents
from .resources.run_task import RunTasks
from .resources.run_task_integration import RunTaskIntegrations
from .resources.run_trigger import RunTriggers
from .resources.ssh_keys import SSHKeys
from .resources.stack import Stacks
from .resources.stack_configuration import StackConfigurations
from .resources.state_version_outputs import StateVersionOutputs
from .resources.state_versions import StateVersions
from .resources.task_result import TaskResults
from .resources.task_stage import TaskStages
from .resources.team import Teams
from .resources.team_project_access import TeamProjectAccesses
from .resources.team_token import TeamTokens
from .resources.team_workspace_access import TeamWorkspaceAccesses
from .resources.user import Users
from .resources.variable import Variables
from .resources.variable_sets import VariableSets, VariableSetVariables
from .resources.workspace_resources import WorkspaceResourcesService
from .resources.workspace_run_task import WorkspaceRunTasks
from .resources.workspaces import Workspaces


class TFEClient:
    def __init__(self, config: TFEConfig | None = None):
        cfg = config or TFEConfig.from_env()
        self._transport = HTTPTransport(
            cfg.address,
            cfg.token,
            timeout=cfg.timeout,
            verify_tls=cfg.verify_tls,
            user_agent_suffix=cfg.user_agent_suffix,
            max_retries=cfg.max_retries,
            backoff_base=cfg.backoff_base,
            backoff_cap=cfg.backoff_cap,
            backoff_jitter=cfg.backoff_jitter,
            http2=cfg.http2,
            proxies=cfg.proxies,
            ca_bundle=cfg.ca_bundle,
        )
        self.oauth_clients = OAuthClients(self._transport)
        self.oauth_tokens = OAuthTokens(self._transport)
        # Agent resources
        self.agent_pools = AgentPools(self._transport)
        self.agents = Agents(self._transport)
        self.agent_tokens = AgentTokens(self._transport)

        # TFE admin namespace (SAML / SCIM / SCIM tokens)
        self.admin = AdminClient(self._transport)

        # GitHub App installation discovery
        self.github_app_installations = GitHubAppInstallations(self._transport)

        # Org-wide API-token TTL policy (pairs with max_ttl_enabled on
        # the parent organisation)
        self.organization_token_ttl_policies = OrganizationTokenTTLPolicies(
            self._transport
        )

        # Core resources
        self.configuration_versions = ConfigurationVersions(self._transport)
        self.notification_configurations = NotificationConfigurations(self._transport)
        self.applies = Applies(self._transport)
        self.plans = Plans(self._transport)
        self.plan_exports = PlanExports(self._transport)
        self.cost_estimates = CostEstimates(self._transport)
        # Meta endpoint: HCP Terraform / TFE outbound IP ranges
        self.ip_ranges = IPRanges(self._transport)
        # IP allowlists (JSON:API cidr-range-lists / cidr-ranges)
        self.cidr_range_lists = CIDRRangeLists(self._transport)
        self.cidr_ranges = CIDRRanges(self._transport)
        self.organizations = Organizations(self._transport)
        self.organization_memberships = OrganizationMemberships(self._transport)
        self.organization_audit_configurations = OrganizationAuditConfigurations(
            self._transport
        )
        self.explorer = Explorer(
            self._transport
        )  # org Explorer queries and saved views

        self.users = Users(self._transport)
        self.task_results = TaskResults(self._transport)
        self.organization_tags = OrganizationTags(self._transport)
        self.organization_tokens = OrganizationTokens(self._transport)
        self.projects = Projects(self._transport)
        self.variables = Variables(self._transport)
        self.variable_sets = VariableSets(self._transport)
        self.variable_set_variables = VariableSetVariables(self._transport)
        self.workspaces = Workspaces(self._transport)
        self.workspace_resources = WorkspaceResourcesService(self._transport)
        self.workspace_run_tasks = WorkspaceRunTasks(self._transport)
        self.registry_modules = RegistryModules(self._transport)
        self.no_code_modules = NoCodeModules(self._transport)
        # Public Terraform Registry (registry.terraform.io), unauthenticated
        self.registry = Registry(self._transport)

        # HYOK OIDC configurations (AWS / Azure / GCP / Vault)
        self.aws_oidc_configurations = AWSOIDCConfigurations(self._transport)
        self.azure_oidc_configurations = AzureOIDCConfigurations(self._transport)
        self.gcp_oidc_configurations = GCPOIDCConfigurations(self._transport)
        self.vault_oidc_configurations = VaultOIDCConfigurations(self._transport)
        self.registry_providers = RegistryProviders(self._transport)
        self.registry_provider_versions = RegistryProviderVersions(self._transport)
        self.registry_provider_platforms = RegistryProviderPlatforms(self._transport)

        # Stack resources
        self.stacks = Stacks(self._transport)
        self.stack_configurations = StackConfigurations(self._transport)

        # State and execution resources
        self.state_versions = StateVersions(self._transport)
        self.state_version_outputs = StateVersionOutputs(self._transport)
        self.run_tasks = RunTasks(self._transport)
        self.run_task_integrations = RunTaskIntegrations(self._transport)
        self.run_triggers = RunTriggers(self._transport)
        self.runs = Runs(self._transport)
        self.task_stages = TaskStages(self._transport)
        self.query_runs = QueryRuns(self._transport)
        self.run_events = RunEvents(self._transport)
        self.comments = Comments(self._transport)
        self.policies = Policies(self._transport)
        self.policy_evaluations = PolicyEvaluations(self._transport)
        self.policy_checks = PolicyChecks(self._transport)
        self.policy_sets = PolicySets(self._transport)
        self.policy_set_parameters = PolicySetParameters(self._transport)
        self.policy_set_outcomes = PolicySetOutcomes(self._transport)
        self.policy_set_versions = PolicySetVersions(self._transport)

        # SSH Keys
        self.ssh_keys = SSHKeys(self._transport)

        # Team project access
        self.teams = Teams(self._transport)
        self.team_project_accesses = TeamProjectAccesses(self._transport)
        self.team_tokens = TeamTokens(self._transport)
        self.team_workspace_accesses = TeamWorkspaceAccesses(self._transport)

        # Reserved Tag Key
        self.reserved_tag_key = ReservedTagKeys(self._transport)

    def close(self) -> None:
        try:
            self._transport._sync.close()
        except Exception:
            pass
