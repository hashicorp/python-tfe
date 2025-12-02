from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str = Field(..., alias="id")
    avatar_url: str = Field(default="", alias="avatar-url")
    email: str = Field(default="", alias="email")
    is_service_account: bool = Field(default=False, alias="is-service-account")
    two_factor: dict = Field(default_factory=dict, alias="two-factor")
    unconfirmed_email: str = Field(default="", alias="unconfirmed-email")
    username: str = Field(default="", alias="username")
    v2_only: bool = Field(default=False, alias="v2-only")
    is_site_admin: bool = Field(default=False, alias="is-site-admin")  # Deprecated
    is_admin: bool = Field(default=False, alias="is-admin")
    is_sso_login: bool = Field(default=False, alias="is-sso-login")
    permissions: dict = Field(default_factory=dict, alias="permissions")

    # Relations
    # authentication_tokens: AuthenticationTokens = Field(..., alias="authentication-tokens")
