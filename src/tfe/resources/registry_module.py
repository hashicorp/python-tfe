from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

from ..errors import (
    ERR_INVALID_NAME,
    ERR_INVALID_ORG,
    ERR_INVALID_VERSION,
)
from ..models.registry_module_types import (
    AgentExecutionMode,
    Commit,
    CommitList,
    RegistryModule,
    RegistryModuleCreateOptions,
    RegistryModuleCreateVersionOptions,
    RegistryModuleCreateWithVCSConnectionOptions,
    RegistryModuleID,
    RegistryModuleListOptions,
    RegistryModulePermissions,
    RegistryModuleUpdateOptions,
    RegistryModuleVCSRepo,
    RegistryModuleVersion,
    RegistryModuleVersionStatuses,
    RegistryName,
    TerraformRegistryModule,
    TestConfig,
)
from ..utils import valid_string, valid_string_id, valid_version
from ._base import _Service


class RegistryModules(_Service):
    """Registry modules service for managing Terraform registry modules."""

    def list(
        self, organization: str, options: RegistryModuleListOptions | None = None
    ) -> Iterator[RegistryModule]:
        """List all the registry modules within an organization."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{organization}/registry-modules"
        params = {}

        if options:
            if options.include:
                params["include"] = ",".join(options.include)
            if options.search:
                params["q"] = options.search
            if options.provider:
                params["filter[provider]"] = options.provider
            if options.registry_name:
                params["filter[registry_name]"] = options.registry_name.value
            if options.organization_name:
                params["filter[organization_name]"] = options.organization_name
            if options.page_number:
                params["page[number]"] = str(options.page_number)
            if options.page_size:
                params["page[size]"] = str(options.page_size)

        for item in self._list(path, params=params):
            if item is None:
                continue  # type: ignore[unreachable]  # Skip None items
            yield self._parse_registry_module(item)

    def list_commits(self, module_id: RegistryModuleID) -> CommitList:
        """List the commits for the registry module.

        This returns the latest 20 commits for the connected VCS repo.
        Pagination is not applicable due to inconsistent support from the VCS providers.
        """
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        path = f"/api/v2/registry-modules/{module_id.organization}/{module_id.name}/{module_id.provider}/commits"

        response = self.t.request("GET", path)
        data = response.json()

        commits = []
        if "data" in data:
            for item in data["data"]:
                commits.append(self._parse_commit(item))

        return CommitList(items=commits)

    def create(
        self, organization: str, options: RegistryModuleCreateOptions
    ) -> RegistryModule:
        """Create a registry module without a VCS repo."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        if not self._validate_create_options(options):
            raise ValueError("Invalid create options")

        body = {
            "data": {
                "type": "registry-modules",
                "attributes": options.model_dump(exclude_none=True),
            }
        }

        path = f"/api/v2/organizations/{organization}/registry-modules"
        response = self.t.request("POST", path, json_body=body)
        data = response.json()["data"]

        return self._parse_registry_module(data)

    def create_version(
        self, module_id: RegistryModuleID, options: RegistryModuleCreateVersionOptions
    ) -> RegistryModuleVersion:
        """Create a registry module version."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        if not self._validate_create_version_options(options):
            raise ValueError("Invalid create version options")

        body = {
            "data": {
                "type": "registry-module-versions",
                "attributes": options.model_dump(exclude_none=True),
            }
        }

        path = f"/api/v2/registry-modules/{module_id.organization}/{module_id.name}/{module_id.provider}/versions"
        response = self.t.request("POST", path, json_body=body)
        data = response.json()["data"]

        return self._parse_registry_module_version(data)

    def create_with_vcs_connection(
        self, options: RegistryModuleCreateWithVCSConnectionOptions
    ) -> RegistryModule:
        """Create and publish a registry module with a VCS repo."""
        if not self._validate_create_with_vcs_options(options):
            raise ValueError("Invalid VCS connection options")

        body = {
            "data": {
                "type": "registry-modules",
                "attributes": options.model_dump(exclude_none=True, by_alias=True),
            }
        }

        # Determine the URL based on options - exactly like Go implementation
        if options.vcs_repo.oauth_token_id and not options.vcs_repo.branch:
            path = "/api/v2/registry-modules"
        else:
            if not options.vcs_repo.organization_name:
                raise ValueError(
                    "organization_name is required in vcs_repo for VCS connection"
                )
            path = f"/api/v2/organizations/{options.vcs_repo.organization_name}/registry-modules/vcs"

        # Validate agent execution mode like Go implementation
        if (
            options.test_config
            and options.test_config.agent_execution_mode == AgentExecutionMode.REMOTE
            and options.test_config.agent_pool_id
        ):
            raise ValueError("Agent pool not required for remote execution")

        response = self.t.request("POST", path, json_body=body)
        data = response.json()["data"]

        return self._parse_registry_module(data)

    def read(self, module_id: RegistryModuleID) -> RegistryModule:
        """Read a specific registry module."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        if module_id.id:
            path = f"/api/v2/registry-modules/{module_id.id}"
        else:
            registry_name = module_id.registry_name or RegistryName.PRIVATE
            namespace = module_id.namespace or module_id.organization

            path = (
                f"/api/v2/organizations/{module_id.organization}/"
                f"registry-modules/{registry_name.value}/{namespace}/"
                f"{module_id.name}/{module_id.provider}"
            )

        response = self.t.request("GET", path)
        data = response.json()["data"]

        return self._parse_registry_module(data)

    def read_version(
        self, module_id: RegistryModuleID, version: str
    ) -> RegistryModuleVersion:
        """Read a registry module version."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        if not valid_string(version) or not valid_string_id(version):
            raise ValueError(ERR_INVALID_VERSION)

        path = (
            f"/api/v2/organizations/{module_id.organization}/"
            f"registry-modules/private/{module_id.organization}/"
            f"{module_id.name}/{module_id.provider}/version"
            f"?module_version={version}"
        )

        response = self.t.request("GET", path)
        data = response.json()["data"]

        return self._parse_registry_module_version(data)

    def list_versions(self, module_id: RegistryModuleID) -> list[RegistryModuleVersion]:  # type: ignore[valid-type]
        """List all versions of a registry module."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        try:
            if module_id.id:
                path = f"/api/v2/registry-modules/{module_id.id}/versions"
            else:
                registry_name = module_id.registry_name or RegistryName.PRIVATE
                namespace = module_id.namespace or module_id.organization

                path = (
                    f"/api/v2/organizations/{module_id.organization}/"
                    f"registry-modules/{registry_name.value}/{namespace}/"
                    f"{module_id.name}/{module_id.provider}/versions"
                )

            response = self.t.request("GET", path)
            response_data = response.json()

            # Handle the case where data might be None or empty
            data = response_data.get("data", []) if response_data else []

            versions = []
            for item in data:
                if item:  # Skip None items
                    versions.append(self._parse_registry_module_version(item))

            return versions

        except Exception:
            # Fallback: If the API endpoint doesn't exist, try to get versions from the module itself
            try:
                module = self.read(module_id)
                versions = []

                # Convert version_statuses to RegistryModuleVersion objects
                for vs in module.version_statuses:
                    # Create a minimal RegistryModuleVersion from version status
                    version_data = {
                        "id": f"modver-{vs.version}",
                        "type": "registry-module-versions",
                        "attributes": {
                            "version": vs.version,
                            "status": vs.status.value,
                            "created-at": None,
                            "updated-at": None,
                            "error": getattr(vs, "error", None),
                        },
                    }
                    versions.append(self._parse_registry_module_version(version_data))

                return versions
            except Exception:
                return []  # Return empty list if all methods fail

    def read_terraform_registry_module(
        self, module_id: RegistryModuleID, version: str
    ) -> TerraformRegistryModule:
        """Read a registry module from the Terraform Registry."""
        if module_id.registry_name == RegistryName.PUBLIC:
            path = (
                f"/api/registry/public/v1/modules/{module_id.namespace}/"
                f"{module_id.name}/{module_id.provider}/{version}"
            )
        else:
            path = (
                f"/api/registry/v1/modules/{module_id.namespace}/"
                f"{module_id.name}/{module_id.provider}/{version}"
            )

        response = self.t.request("GET", path)
        data = response.json()

        return TerraformRegistryModule(**data)

    def delete(self, organization: str, name: str) -> None:
        """Delete the entire registry module.

        Warning: This method is deprecated and will be removed from a future version.
        Use delete_by_name instead.
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        if not valid_string(name) or not valid_string_id(name):
            raise ValueError(ERR_INVALID_NAME)

        path = f"/api/v2/registry-modules/actions/delete/{organization}/{name}"
        self.t.request("POST", path, json_body={})

    def delete_by_name(self, module_id: RegistryModuleID) -> None:
        """Delete the entire registry module by name."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        path = (
            f"/api/v2/registry-modules/actions/delete/"
            f"{module_id.organization}/{module_id.name}"
        )
        self.t.request("POST", path, json_body={})

    def delete_provider(self, module_id: RegistryModuleID) -> None:
        """Delete a specified provider for the given module along with all its versions."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        path = (
            f"/api/v2/registry-modules/actions/delete/"
            f"{module_id.organization}/{module_id.name}/{module_id.provider}"
        )
        self.t.request("POST", path, json_body={})

    def delete_version(self, module_id: RegistryModuleID, version: str) -> None:
        """Delete a specified version for the given provider of the module."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        if not valid_string(version) or not valid_version(version):
            raise ValueError(ERR_INVALID_VERSION)

        path = (
            f"/api/v2/registry-modules/actions/delete/"
            f"{module_id.organization}/{module_id.name}/"
            f"{module_id.provider}/{version}"
        )
        self.t.request("POST", path, json_body={})

    def update(
        self, module_id: RegistryModuleID, options: RegistryModuleUpdateOptions
    ) -> RegistryModule:
        """Update properties of a registry module."""
        if not self._validate_module_id(module_id):
            raise ValueError("Invalid module ID")

        body = {
            "data": {
                "type": "registry-modules",
                "attributes": options.model_dump(exclude_none=True),
            }
        }

        registry_name = module_id.registry_name or RegistryName.PRIVATE
        namespace = module_id.namespace or module_id.organization

        path = (
            f"/api/v2/organizations/{module_id.organization}/"
            f"registry-modules/{registry_name.value}/{namespace}/"
            f"{module_id.name}/{module_id.provider}"
        )

        response = self.t.request("PATCH", path, json_body=body)
        data = response.json()["data"]

        return self._parse_registry_module(data)

    def upload(self, rmv: RegistryModuleVersion, path: str) -> None:
        """Upload Terraform configuration files for the provided registry module version.

        It requires a path to the configuration files on disk, which will be packaged
        before being uploaded.
        """
        upload_url = rmv.links.get("upload")
        if not upload_url:
            raise ValueError(
                "provided RegistryModuleVersion does not contain an upload link"
            )

        # This would need implementation for packaging files from path
        # For now, this is a placeholder
        raise NotImplementedError("File packaging and upload not implemented yet")

    def upload_tar_gzip(self, upload_url: str, archive: io.IOBase) -> None:
        """Upload a tar gzip archive to the specified upload URL.

        Any stream implementing io.IOBase can be passed into this method.

        Note: This method does not validate the content being uploaded and is therefore
        the caller's responsibility to ensure the raw content is a valid Terraform configuration.
        """
        # Use the httpx client for direct upload to external URL
        response = self.t._sync.put(upload_url, content=archive.read())
        response.raise_for_status()

    # Helper methods for validation and parsing
    def _validate_module_id(self, module_id: RegistryModuleID) -> bool:
        """Validate registry module ID."""
        if module_id.id and valid_string_id(module_id.id):
            return True

        if not valid_string_id(module_id.organization):
            return False

        if not valid_string(module_id.name) or not valid_string_id(module_id.name):
            return False

        if not valid_string(module_id.provider) or not valid_string_id(
            module_id.provider
        ):
            return False

        if module_id.registry_name == RegistryName.PUBLIC:
            if not valid_string(module_id.namespace):
                return False

        return True

    def _validate_create_options(self, options: RegistryModuleCreateOptions) -> bool:
        """Validate create options."""
        if not valid_string(options.name) or not valid_string_id(options.name):
            return False

        if not valid_string(options.provider) or not valid_string_id(options.provider):
            return False

        if options.registry_name == RegistryName.PUBLIC:
            if not valid_string(options.namespace):
                return False
        elif options.registry_name == RegistryName.PRIVATE:
            if valid_string(options.namespace):
                return False

        return True

    def _validate_create_version_options(
        self, options: RegistryModuleCreateVersionOptions
    ) -> bool:
        """Validate create version options."""
        if not valid_string(options.version):
            return False

        if not valid_version(options.version):
            return False

        return True

    def _validate_create_with_vcs_options(
        self, options: RegistryModuleCreateWithVCSConnectionOptions
    ) -> bool:
        """Validate create with VCS connection options."""
        # Must have VCS repo
        if not options.vcs_repo:
            return False

        # Validate VCS repo options
        if not valid_string(options.vcs_repo.identifier):
            return False

        if not valid_string(options.vcs_repo.display_identifier):
            return False

        # If branch is specified, organization_name is required
        if valid_string(options.vcs_repo.branch) and not valid_string(
            options.vcs_repo.organization_name
        ):
            return False

        # Cannot have both tags and branch set
        if options.vcs_repo.tags and valid_string(options.vcs_repo.branch):
            return False

        # Agent execution mode validation
        if (
            options.test_config
            and options.test_config.agent_execution_mode == AgentExecutionMode.REMOTE
            and options.test_config.agent_pool_id
        ):
            return False

        return True

    def _parse_registry_module(self, data: dict[str, Any]) -> RegistryModule:
        """Parse registry module from API response."""
        if data is None:
            raise ValueError("Cannot parse registry module: data is None")

        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})

        # Parse organization relationship
        organization = None
        if "organization" in relationships:
            org_data = relationships["organization"].get("data", {})
            if org_data:
                organization = {"name": org_data.get("attributes", {}).get("name", "")}

        # Parse permissions with field name mapping
        permissions = None
        if "permissions" in data:
            perm_data = data["permissions"]
            permissions = RegistryModulePermissions(
                can_delete=perm_data.get("can-delete", False),
                can_resync=perm_data.get("can-resync", False),
                can_retry=perm_data.get("can-retry", False),
            )

        # Parse VCS repo with field name mapping
        vcs_repo = None
        if "vcs-repo" in attributes:
            vcs_data = attributes["vcs-repo"]
            vcs_repo = RegistryModuleVCSRepo(
                branch=vcs_data.get("branch"),
                display_identifier=vcs_data.get("display-identifier"),
                identifier=vcs_data.get("identifier"),
                ingress_submodules=vcs_data.get("ingress-submodules"),
                oauth_token_id=vcs_data.get("oauth-token-id"),
                repository_http_url=vcs_data.get("repository-http-url"),
                service_provider=vcs_data.get("service-provider"),
                webhook_url=vcs_data.get("webhook-url"),
                tags=vcs_data.get("tags"),
                source_directory=vcs_data.get("source-directory"),
                tag_prefix=vcs_data.get("tag-prefix"),
            )

        # Parse test config with field name mapping
        test_config = None
        if "test-config" in attributes:
            test_data = attributes["test-config"]
            if test_data is not None:
                test_config = TestConfig(
                    tests_enabled=test_data.get("tests-enabled", False),
                    agent_execution_mode=AgentExecutionMode(
                        test_data.get("agent-execution-mode", "remote")
                    ),
                )

        # Parse version statuses with field name mapping
        version_statuses = []
        if "version-statuses" in attributes:
            for vs in attributes["version-statuses"]:
                version_statuses.append(
                    RegistryModuleVersionStatuses(
                        version=vs.get("version", ""),
                        status=vs.get("status", ""),
                        error=vs.get("error"),
                    )
                )

        return RegistryModule(
            id=data.get("id", ""),
            name=attributes.get("name", ""),
            provider=attributes.get("provider", ""),
            registry_name=RegistryName(attributes.get("registry-name", "private")),
            namespace=attributes.get("namespace", ""),
            no_code=attributes.get("no-code", False),
            permissions=permissions,
            publishing_mechanism=attributes.get("publishing-mechanism"),
            status=attributes.get("status"),
            test_config=test_config,
            vcs_repo=vcs_repo,
            version_statuses=version_statuses,
            created_at=attributes.get("created-at"),
            updated_at=attributes.get("updated-at"),
            organization=organization,
        )

    def _parse_registry_module_version(
        self, data: dict[str, Any]
    ) -> RegistryModuleVersion:
        """Parse registry module version from API response."""
        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})
        links = data.get("links", {})

        # Parse registry module relationship
        registry_module = None
        if "registry-module" in relationships:
            rm_data = relationships["registry-module"].get("data", {})
            if rm_data:
                registry_module = self._parse_registry_module(rm_data)

        return RegistryModuleVersion(
            id=data.get("id", ""),
            source=attributes.get("source"),
            status=attributes.get("status"),
            version=attributes.get("version", ""),
            created_at=attributes.get("created-at"),
            updated_at=attributes.get("updated-at"),
            registry_module=registry_module,
            links=links,
        )

    def _parse_commit(self, data: dict[str, Any]) -> Commit:
        """Parse commit from API response."""
        attributes = data.get("attributes", {})

        return Commit(
            id=data.get("id", ""),
            sha=attributes.get("sha", ""),
            date=attributes.get("date", ""),
            url=attributes.get("url"),
            author=attributes.get("author"),
            author_avatar_url=attributes.get("author-avatar-url"),
            author_html_url=attributes.get("author-html-url"),
            message=attributes.get("message"),
        )
