# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from pytfe.models.configuration_version import IngressAttributes

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import InvalidStackConfigurationIDError, NotFound
from ..models.stack import Stack
from ..models.stack_configuration import (
    StackConfiguration,
    StackConfigurationCreateOptions,
    StackConfigurationListOptions,
    StackConfigurationReadOptions,
    StackConfigurationSource,
)
from ..utils import valid_string_id
from ._base import _Service

#: Both reasons a configuration has no upload URL. HCP returns a bare 404 for
#: each, so the difference has to be explained rather than reported.
_NO_UPLOAD_URL_HINT = (
    "Only a configuration created with source=MANUAL awaits an upload, and only "
    "until its source arrives: a VCS-sourced configuration never has an upload "
    "URL, and a manual one stops having one once it has been uploaded. Create a "
    "new configuration to upload again."
)


class StackConfigurations(_Service):
    """Service for managing Terraform stack configurations."""

    def create(
        self,
        stack_id: str,
        options: StackConfigurationCreateOptions | None = None,
        source: StackConfigurationSource = StackConfigurationSource.MANUAL,
    ) -> StackConfiguration:
        """Create a stack configuration for the given stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xyz789"``).
            options: Optional creation settings, as a
                :class:`StackConfigurationCreateOptions`.
            source: How to source the configuration, as a
                :class:`StackConfigurationSource`.

        Returns:
            The created :class:`StackConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import StackConfigurationCreateOptions
            >>> config = client.stack_configurations.create(
            ...     "st-xyz789",
            ...     StackConfigurationCreateOptions(speculative_enabled=True),
            ... )
        """
        path = f"/api/v2/stacks/{stack_id}/stack-configurations"
        params: dict[str, str] = {}
        if source != StackConfigurationSource.MANUAL:
            params["source"] = source.value

        attributes: dict[str, Any] = {}
        if options:
            attributes = options.model_dump(by_alias=True, exclude_none=True)

        payload = {
            "data": {
                "type": "stack-configurations",
                "attributes": attributes,
            }
        }
        r = self.t.request("POST", path=path, json_body=payload, params=params)
        data = r.json().get("data", {})
        return self._stack_configuration_from(data)

    def list(
        self,
        stack_id: str,
        options: StackConfigurationListOptions | None = None,
    ) -> Iterator[StackConfiguration]:
        """List stack configurations for the given stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-xyz789"``).
            options: Optional pagination and includes, as a
                :class:`StackConfigurationListOptions`.

        Returns:
            A single-use ``Iterator[StackConfiguration]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> for config in client.stack_configurations.list("st-xyz789"):
            ...     print(config.id, config.status)
        """
        path = f"/api/v2/stacks/{stack_id}/stack-configurations"
        params: dict[str, Any] = {}
        if options:
            if options.page_size is not None:
                params["page[size]"] = options.page_size
            if options.include:
                params["include"] = ",".join([i.value for i in options.include])
        for item in self._list(path=path, params=params):
            yield self._stack_configuration_from(item)

    def read(
        self,
        stack_configuration_id: str,
        options: StackConfigurationReadOptions | None = None,
    ) -> StackConfiguration:
        """Read a stack configuration by its ID.

        Args:
            stack_configuration_id: The stack configuration ID (e.g. ``"stc-abc123"``).
            options: Optional related resources, as a
                :class:`StackConfigurationReadOptions`.

        Returns:
            The :class:`StackConfiguration`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> config = client.stack_configurations.read("stc-abc123")
            >>> print(config.sequence_number)
        """
        path = f"/api/v2/stack-configurations/{stack_configuration_id}"
        params: dict[str, str] = {}
        if options and options.include:
            params["include"] = ",".join([i.value for i in options.include])
        r = self.t.request("GET", path=path, params=params)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_configuration_from(data, payload.get("included"))

    def upload_url(self, stack_configuration_id: str) -> str:
        """Return the URL to upload a stack configuration's source.

        A configuration created with :attr:`StackConfigurationSource.MANUAL`
        waits for its source to be uploaded. The create response does not carry
        the upload location, so it is fetched separately.

        Args:
            stack_configuration_id: The configuration ID (e.g. ``"stc-abc123"``).

        Returns:
            The presigned upload URL.

        Raises:
            InvalidStackConfigurationIDError: If the ID is empty or malformed.
            NotFound: If the configuration has no upload pending - because its
                source came from VCS, or because it has already been uploaded.
                The exception's ``hint`` says which.
            TFEError: If the API request fails.

        Example:
            >>> configuration = client.stack_configurations.create("st-xyz789")
            >>> client.stack_configurations.upload_url(configuration.id)
            'https://archivist.terraform.io/v1/object/...'
        """
        if not valid_string_id(stack_configuration_id):
            raise InvalidStackConfigurationIDError()

        path = f"/api/v2/stack-configurations/{stack_configuration_id}/upload-url"
        try:
            payload = self.t.request("GET", path).json()
        except NotFound as exc:
            # The API answers 404 rather than an empty body, and does so in two
            # cases worth telling apart from a mistyped ID.
            raise NotFound(
                f"stack configuration {stack_configuration_id} has no upload URL",
                status=404,
                hint=_NO_UPLOAD_URL_HINT,
            ) from exc
        # This endpoint does not return a JSON:API resource object: `data` is a
        # bare object carrying only `source-upload-url`.
        data = payload.get("data") or {}
        url = data.get("source-upload-url")
        if not isinstance(url, str) or not url:
            raise NotFound(
                f"stack configuration {stack_configuration_id} has no upload URL",
                status=404,
                hint=_NO_UPLOAD_URL_HINT,
            )
        return url

    def upload(self, stack_configuration_id: str, archive: bytes) -> None:
        """Upload a packaged stack configuration.

        Resolves the upload URL and PUTs the archive to it.

        Args:
            stack_configuration_id: The configuration ID (e.g. ``"stc-abc123"``).
            archive: The ``.tar.gz`` bytes. Build one with
                :func:`pytfe.workflows.package_directory`, which applies
                Terraform's own exclusions.

        Returns:
            None.

        Raises:
            InvalidStackConfigurationIDError: If the ID is empty or malformed.
            ValueError: If ``archive`` is empty.
            NotFound: If the configuration has no upload pending.
            TFEError: If the upload fails.

        Example:
            >>> from pytfe.workflows import package_directory
            >>> configuration = client.stack_configurations.create("st-xyz789")
            >>> client.stack_configurations.upload(
            ...     configuration.id, package_directory("./stack")
            ... )
        """
        if not archive:
            raise ValueError("archive must not be empty")
        url = self.upload_url(stack_configuration_id)
        self.upload_to(url, archive)

    def upload_to(self, upload_url: str, archive: bytes) -> None:
        """PUT a packaged stack configuration to an already-resolved URL.

        Use :meth:`upload` unless you resolved the URL yourself.

        Args:
            upload_url: The presigned URL from :meth:`upload_url`.
            archive: The ``.tar.gz`` bytes.

        Returns:
            None.

        Raises:
            ValueError: If ``archive`` is empty.
            NotFound: If the upload URL has expired.
            AuthError: If the token may not upload to this URL.
            TFEError: If the upload fails.

        Example:
            >>> url = client.stack_configurations.upload_url("stc-abc123")
            >>> client.stack_configurations.upload_to(url, archive)
        """
        if not archive:
            raise ValueError("archive must not be empty")
        # Through the transport, so the upload inherits retries, typed error
        # translation and the read-only gate. The bearer token is required:
        # these URLs point at HashiCorp's Archivist.
        self.t.request(
            "PUT",
            upload_url,
            data=archive,
            headers={"Content-Type": "application/octet-stream"},
        )

    def _stack_configuration_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackConfiguration:
        """Parse a StackConfiguration from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack": Stack, "ingress-attributes": IngressAttributes},
                included=included,
            )
        )
        return attach_jsonapi(StackConfiguration.model_validate(attrs), data, included)
