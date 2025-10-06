from __future__ import annotations

from ._http import HTTPTransport
from .config import TFEConfig
from .resources.agent_pools import AgentPools
from .resources.agents import Agents, AgentTokens
from .resources.apply import Applies
from .resources.configuration_version import ConfigurationVersions
from .resources.oauth_client import OAuthClients
from .resources.oauth_token import OAuthTokens
from .resources.organizations import Organizations
from .resources.plan import Plans
from .resources.policy import Policies
from .resources.projects import Projects
from .resources.query_run import QueryRuns
from .resources.registry_module import RegistryModules
from .resources.registry_provider import RegistryProviders
from .resources.reserved_tag_key import ReservedTagKey
from .resources.run import Runs
from .resources.run_event import RunEvents
from .resources.run_task import RunTasks
from .resources.run_trigger import RunTriggers
from .resources.ssh_keys import SSHKeys
from .resources.state_version_outputs import StateVersionOutputs
from .resources.state_versions import StateVersions
from .resources.variable import Variables
from .resources.variable_sets import VariableSets, VariableSetVariables
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

        # Core resources
        self.configuration_versions = ConfigurationVersions(self._transport)
        self.applies = Applies(self._transport)
        self.plans = Plans(self._transport)
        self.organizations = Organizations(self._transport)
        self.projects = Projects(self._transport)
        self.variables = Variables(self._transport)
        self.variable_sets = VariableSets(self._transport)
        self.variable_set_variables = VariableSetVariables(self._transport)
        self.workspaces = Workspaces(self._transport)
        self.registry_modules = RegistryModules(self._transport)
        self.registry_providers = RegistryProviders(self._transport)

        # State and execution resources
        self.state_versions = StateVersions(self._transport)
        self.state_version_outputs = StateVersionOutputs(self._transport)
        self.run_tasks = RunTasks(self._transport)
        self.run_triggers = RunTriggers(self._transport)
        self.runs = Runs(self._transport)
        self.query_runs = QueryRuns(self._transport)
        self.run_events = RunEvents(self._transport)
        self.policies = Policies(self._transport)

        # SSH Keys
        self.ssh_keys = SSHKeys(self._transport)

        # Reserved Tag Key
        self.reserved_tag_key = ReservedTagKey(self._transport)

    def close(self) -> None:
        pass
