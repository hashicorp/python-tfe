"""
Organization models for the PyTFE SDK.

This module contains Pydantic models for organization-related entities
in the Terraform Enterprise/Cloud API.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class OrganizationPermissions(BaseModel):
    """Organization permissions model."""
    model_config = ConfigDict(extra="allow")
    
    can_update: bool = Field(alias="can-update")
    can_destroy: bool = Field(alias="can-destroy")
    can_access_via_teams: bool = Field(alias="can-access-via-teams")
    can_create_module: bool = Field(alias="can-create-module")
    can_create_team: bool = Field(alias="can-create-team")
    can_create_workspace: bool = Field(alias="can-create-workspace")
    can_manage_users: bool = Field(alias="can-manage-users")
    can_manage_subscription: bool = Field(alias="can-manage-subscription")
    can_manage_sso: bool = Field(alias="can-manage-sso")
    can_update_oauth: bool = Field(alias="can-update-oauth")
    can_update_sentinel: bool = Field(alias="can-update-sentinel")
    can_update_ssh_keys: bool = Field(alias="can-update-ssh-keys")
    can_update_api_token: bool = Field(alias="can-update-api-token")
    can_traverse: bool = Field(alias="can-traverse")
    can_start_trial: Optional[bool] = Field(None, alias="can-start-trial")
    can_update_agent_pools: Optional[bool] = Field(None, alias="can-update-agent-pools")
    can_manage_tags: Optional[bool] = Field(None, alias="can-manage-tags")
    can_manage_varsets: Optional[bool] = Field(None, alias="can-manage-varsets")
    can_read_varsets: Optional[bool] = Field(None, alias="can-read-varsets")
    can_manage_public_providers: Optional[bool] = Field(None, alias="can-manage-public-providers")
    can_create_provider: Optional[bool] = Field(None, alias="can-create-provider")
    can_manage_public_modules: Optional[bool] = Field(None, alias="can-manage-public-modules")
    can_manage_custom_providers: Optional[bool] = Field(None, alias="can-manage-custom-providers")
    can_manage_run_tasks: Optional[bool] = Field(None, alias="can-manage-run-tasks")
    can_read_run_tasks: Optional[bool] = Field(None, alias="can-read-run-tasks")
    can_manage_membership: Optional[bool] = Field(None, alias="can-manage-membership")
    can_manage_owners: Optional[bool] = Field(None, alias="can-manage-owners")


class Organization(BaseModel):
    """Organization model representing a Terraform Enterprise/Cloud organization."""
    model_config = ConfigDict(extra="allow")
    
    id: str
    type: str = "organizations"
    
    # Attributes
    name: str
    email: Optional[str] = None
    session_timeout: Optional[int] = Field(None, alias="session-timeout")
    session_remember: Optional[int] = Field(None, alias="session-remember")
    collaborator_auth_policy: Optional[str] = Field(None, alias="collaborator-auth-policy")
    plan_expired: Optional[bool] = Field(None, alias="plan-expired")
    plan_expires_at: Optional[datetime] = Field(None, alias="plan-expires-at")
    plan_is_trial: Optional[bool] = Field(None, alias="plan-is-trial")
    plan_is_enterprise: Optional[bool] = Field(None, alias="plan-is-enterprise")
    plan_identifier: Optional[str] = Field(None, alias="plan-identifier")
    cost_estimation_enabled: Optional[bool] = Field(None, alias="cost-estimation-enabled")
    send_passing_statuses_for_untriggered_speculative_plans: Optional[bool] = Field(
        None, alias="send-passing-statuses-for-untriggered-speculative-plans"
    )
    aggregated_commit_status_enabled: Optional[bool] = Field(
        None, alias="aggregated-commit-status-enabled"
    )
    assessments_enforced: Optional[bool] = Field(None, alias="assessments-enforced")
    public_providers: Optional[bool] = Field(None, alias="public-providers")
    public_modules: Optional[bool] = Field(None, alias="public-modules")
    fair_run_queuing_enabled: Optional[bool] = Field(None, alias="fair-run-queuing-enabled")
    default_execution_mode: Optional[str] = Field(None, alias="default-execution-mode")
    permissions: Optional[OrganizationPermissions] = None
    saml_enabled: Optional[bool] = Field(None, alias="saml-enabled")
    owners_team_saml_role_id: Optional[str] = Field(None, alias="owners-team-saml-role-id")
    two_factor_conformant: Optional[bool] = Field(None, alias="two-factor-conformant")
    external_id: Optional[str] = Field(None, alias="external-id")
    created_at: Optional[datetime] = Field(None, alias="created-at")


class OrganizationCreateRequest(BaseModel):
    """Request model for creating an organization."""
    model_config = ConfigDict(extra="forbid")
    
    data: Dict[str, Any] = Field(...)
    
    @classmethod
    def create(
        cls,
        name: str,
        email: str,
        session_timeout: Optional[int] = None,
        session_remember: Optional[int] = None,
        collaborator_auth_policy: Optional[str] = None,
        cost_estimation_enabled: Optional[bool] = None,
        owners_team_saml_role_id: Optional[str] = None,
        send_passing_statuses_for_untriggered_speculative_plans: Optional[bool] = None,
        aggregated_commit_status_enabled: Optional[bool] = None,
        assessments_enforced: Optional[bool] = None,
        **kwargs: Any,
    ) -> "OrganizationCreateRequest":
        """Create an organization creation request."""
        attributes = {
            "name": name,
            "email": email,
        }
        
        # Add optional attributes
        if session_timeout is not None:
            attributes["session-timeout"] = session_timeout
        if session_remember is not None:
            attributes["session-remember"] = session_remember
        if collaborator_auth_policy is not None:
            attributes["collaborator-auth-policy"] = collaborator_auth_policy
        if cost_estimation_enabled is not None:
            attributes["cost-estimation-enabled"] = cost_estimation_enabled
        if owners_team_saml_role_id is not None:
            attributes["owners-team-saml-role-id"] = owners_team_saml_role_id
        if send_passing_statuses_for_untriggered_speculative_plans is not None:
            attributes["send-passing-statuses-for-untriggered-speculative-plans"] = (
                send_passing_statuses_for_untriggered_speculative_plans
            )
        if aggregated_commit_status_enabled is not None:
            attributes["aggregated-commit-status-enabled"] = aggregated_commit_status_enabled
        if assessments_enforced is not None:
            attributes["assessments-enforced"] = assessments_enforced
        
        # Add any additional attributes
        attributes.update(kwargs)
        
        data = {
            "type": "organizations",
            "attributes": attributes,
        }
        
        return cls(data=data)


class OrganizationUpdateRequest(BaseModel):
    """Request model for updating an organization."""
    model_config = ConfigDict(extra="forbid")
    
    data: Dict[str, Any] = Field(...)
    
    @classmethod
    def create(
        cls,
        name: Optional[str] = None,
        email: Optional[str] = None,
        session_timeout: Optional[int] = None,
        session_remember: Optional[int] = None,
        collaborator_auth_policy: Optional[str] = None,
        cost_estimation_enabled: Optional[bool] = None,
        owners_team_saml_role_id: Optional[str] = None,
        send_passing_statuses_for_untriggered_speculative_plans: Optional[bool] = None,
        aggregated_commit_status_enabled: Optional[bool] = None,
        assessments_enforced: Optional[bool] = None,
        **kwargs: Any,
    ) -> "OrganizationUpdateRequest":
        """Create an organization update request."""
        attributes = {}
        
        # Add provided attributes
        if name is not None:
            attributes["name"] = name
        if email is not None:
            attributes["email"] = email
        if session_timeout is not None:
            attributes["session-timeout"] = session_timeout
        if session_remember is not None:
            attributes["session-remember"] = session_remember
        if collaborator_auth_policy is not None:
            attributes["collaborator-auth-policy"] = collaborator_auth_policy
        if cost_estimation_enabled is not None:
            attributes["cost-estimation-enabled"] = cost_estimation_enabled
        if owners_team_saml_role_id is not None:
            attributes["owners-team-saml-role-id"] = owners_team_saml_role_id
        if send_passing_statuses_for_untriggered_speculative_plans is not None:
            attributes["send-passing-statuses-for-untriggered-speculative-plans"] = (
                send_passing_statuses_for_untriggered_speculative_plans
            )
        if aggregated_commit_status_enabled is not None:
            attributes["aggregated-commit-status-enabled"] = aggregated_commit_status_enabled
        if assessments_enforced is not None:
            attributes["assessments-enforced"] = assessments_enforced
        
        # Add any additional attributes
        attributes.update(kwargs)
        
        data = {
            "type": "organizations",
            "attributes": attributes,
        }
        
        return cls(data=data)


class OrganizationListOptions(BaseModel):
    """Options for listing organizations."""
    model_config = ConfigDict(extra="forbid")
    
    page_number: Optional[int] = Field(None, alias="page[number]")
    page_size: Optional[int] = Field(None, alias="page[size]")
    
    def to_params(self) -> Dict[str, Any]:
        """Convert to query parameters."""
        params = {}
        if self.page_number is not None:
            params["page[number]"] = self.page_number
        if self.page_size is not None:
            params["page[size]"] = self.page_size
        return params
