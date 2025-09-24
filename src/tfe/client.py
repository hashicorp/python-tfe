from __future__ import annotations

from ._http import HTTPTransport
from .config import TFEConfig
from .resources.organizations import Organizations
from .resources.projects import Projects
from .resources.registry_module import RegistryModules
from .resources.registry_provider import RegistryProviders
from .resources.run import Runs
from .resources.run_task import RunTasks
from .resources.run_trigger import RunTriggers
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
        self.organizations = Organizations(self._transport)
        self.projects = Projects(self._transport)
        self.variables = Variables(self._transport)
        self.variable_sets = VariableSets(self._transport)
        self.variable_set_variables = VariableSetVariables(self._transport)
        self.workspaces = Workspaces(self._transport)
        self.registry_modules = RegistryModules(self._transport)
        self.registry_providers = RegistryProviders(self._transport)

        self.state_versions = StateVersions(self._transport)
        self.state_version_outputs = StateVersionOutputs(self._transport)
        self.run_tasks = RunTasks(self._transport)
        self.run_triggers = RunTriggers(self._transport)
        self.runs = Runs(self._transport)

    def close(self) -> None:
        pass
