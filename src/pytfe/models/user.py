# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0
from pydantic import BaseModel, ConfigDict, Field

class TwoFactor(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    enabled: bool = Field(default=False, alias="enabled")
    verified: bool = Field(default=False, alias="verified")


class UserPermissions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    can_create_organizations: bool = Field(
        default=False, alias="can-create-organizations"
    )
    can_change_email: bool = Field(default=False, alias="can-change-email")
    can_change_username: bool = Field(default=False, alias="can-change-username")
    can_manage_user_tokens: bool = Field(default=False, alias="can-manage-user-tokens")
    can_view_2fa_settings: bool = Field(default=False, alias="can-view2fa-settings")
    can_manage_hcp_account: bool = Field(default=False, alias="can-manage-hcp-account")


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str = Field(..., alias="id")
    auth_method: str | None = Field(default=None, alias="auth-method")
    avatar_url: str | None = Field(default=None, alias="avatar-url")
    email: str | None = Field(default=None, alias="email")
    is_service_account: bool = Field(default=False, alias="is-service-account")
    two_factor: TwoFactor | None = Field(default=None, alias="two-factor")
    unconfirmed_email: str | None = Field(default=None, alias="unconfirmed-email")
    username: str = Field(default="", alias="username")
    v2_only: bool = Field(default=False, alias="v2-only")
    is_site_admin: bool | None = Field(
        default=None, alias="is-site-admin"
    )  # Deprecated
    is_admin: bool | None = Field(default=None, alias="is-admin")
    is_sso_login: bool | None = Field(default=None, alias="is-sso-login")
    permissions: UserPermissions | None = Field(default=None, alias="permissions")
    # Relations
    # authentication_tokens: AuthenticationTokens = Field(..., alias="authentication-tokens")

class UserUpdateCurrentOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    username: str | None = Field(default=None, alias="username")
    email: str | None = Field(default=None, alias="email")
