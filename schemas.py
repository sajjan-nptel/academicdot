import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Base / shared
# ---------------------------------------------------------------------------


class TenantBase(BaseModel):
    """Fields shared between create and update requests."""

    node_name: str = Field(..., max_length=255)
    node_abbreviation: str | None = Field(None, max_length=20)
    node_slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    node_description: str | None = None

    # Contact & Location
    node_website: str | None = Field(None, max_length=255)
    node_email: str | None = Field(None, max_length=255)
    node_phone: str | None = Field(None, max_length=50)
    node_city: str | None = Field(None, max_length=100)
    node_state: str | None = Field(None, max_length=100)
    node_country: str | None = Field(None, max_length=100)
    time_zone: str = Field("UTC", max_length=100)
    locale: str = Field("en-US", max_length=10)
    currency: str = Field("USD", max_length=3)

    # Branding & Theme
    colour_theme: str = Field("default", max_length=50)
    custom_theme_config: dict[str, Any] | None = None
    logo_url: str | None = Field(None, max_length=500)
    favicon_url: str | None = Field(None, max_length=500)
    brand_colors: dict[str, Any] | None = None

    # URLs & Endpoints
    subdomain: str = Field(..., max_length=100, pattern=r"^[a-z0-9-]+$")
    custom_domain: str | None = Field(None, max_length=255)
    system_frontend_url: str = Field(..., max_length=255)
    system_backend_url: str = Field(..., max_length=255)
    api_endpoint: str | None = Field(None, max_length=255)

    # Database Connection
    db_host: str = Field(..., max_length=255)
    db_port: int = Field(5432, ge=1, le=65535)
    db_name: str = Field(..., max_length=100)
    db_connection_pool_size: int = Field(10, ge=1, le=100)
    db_ssl_enabled: bool = True

    # Features & Limits
    features_enabled: list[str] | None = Field(default_factory=list)
    subscription_plan: str | None = Field(None, max_length=50)
    subscription_ends_at: datetime | None = None
    max_users: int | None = Field(None, ge=1)
    max_storage_gb: int | None = Field(None, ge=1)
    rate_limit_per_hour: int = Field(1000, ge=0)

    # Status
    active: bool = True
    suspended: bool = False
    suspension_reason: str | None = None


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TenantCreate(TenantBase):
    """Request body for POST /tenants/."""

    # These are passed in plain text and will be encrypted before storage
    db_user: str = Field(..., max_length=100)
    db_password: str = Field(..., min_length=8)
    api_endpoint_key: str | None = None

    # Audit
    created_by: int | None = None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TenantUpdate(BaseModel):
    """Request body for PUT /tenants/{tenant_id}. All fields optional."""

    node_name: str | None = Field(None, max_length=255)
    node_abbreviation: str | None = Field(None, max_length=20)
    node_slug: str | None = Field(None, max_length=100, pattern=r"^[a-z0-9-]+$")
    node_description: str | None = None

    node_website: str | None = Field(None, max_length=255)
    node_email: str | None = Field(None, max_length=255)
    node_phone: str | None = Field(None, max_length=50)
    node_city: str | None = Field(None, max_length=100)
    node_state: str | None = Field(None, max_length=100)
    node_country: str | None = Field(None, max_length=100)
    time_zone: str | None = Field(None, max_length=100)
    locale: str | None = Field(None, max_length=10)
    currency: str | None = Field(None, max_length=3)

    colour_theme: str | None = Field(None, max_length=50)
    custom_theme_config: dict[str, Any] | None = None
    logo_url: str | None = Field(None, max_length=500)
    favicon_url: str | None = Field(None, max_length=500)
    brand_colors: dict[str, Any] | None = None

    subdomain: str | None = Field(None, max_length=100, pattern=r"^[a-z0-9-]+$")
    custom_domain: str | None = Field(None, max_length=255)
    system_frontend_url: str | None = Field(None, max_length=255)
    system_backend_url: str | None = Field(None, max_length=255)
    api_endpoint: str | None = Field(None, max_length=255)
    api_endpoint_key: str | None = None  # plain text, encrypted before storage

    db_host: str | None = Field(None, max_length=255)
    db_port: int | None = Field(None, ge=1, le=65535)
    db_name: str | None = Field(None, max_length=100)
    db_user: str | None = Field(None, max_length=100)  # plain text
    db_password: str | None = Field(None, min_length=8)  # plain text
    db_connection_pool_size: int | None = Field(None, ge=1, le=100)
    db_ssl_enabled: bool | None = None

    features_enabled: list[str] | None = None
    subscription_plan: str | None = Field(None, max_length=50)
    subscription_ends_at: datetime | None = None
    max_users: int | None = Field(None, ge=1)
    max_storage_gb: int | None = Field(None, ge=1)
    rate_limit_per_hour: int | None = Field(None, ge=0)

    active: bool | None = None
    suspended: bool | None = None
    suspension_reason: str | None = None

    updated_by: int | None = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class TenantResponse(BaseModel):
    """Full tenant response (encrypted fields are masked)."""

    model_config = ConfigDict(from_attributes=True)

    node_id: int
    node_uuid: uuid.UUID
    node_name: str
    node_abbreviation: str | None
    node_slug: str
    node_description: str | None

    node_website: str | None
    node_email: str | None
    node_phone: str | None
    node_city: str | None
    node_state: str | None
    node_country: str | None
    time_zone: str
    locale: str
    currency: str

    colour_theme: str
    custom_theme_config: dict[str, Any] | None
    logo_url: str | None
    favicon_url: str | None
    brand_colors: dict[str, Any] | None

    subdomain: str
    custom_domain: str | None
    system_frontend_url: str
    system_backend_url: str
    api_endpoint: str | None
    # Encrypted key is never returned in plain text
    has_api_key: bool = False

    db_host: str
    db_port: int
    db_name: str
    # Encrypted credentials are never returned
    db_connection_pool_size: int
    db_ssl_enabled: bool

    features_enabled: list[str] | None
    subscription_plan: str | None
    subscription_ends_at: datetime | None
    max_users: int | None
    max_storage_gb: int | None
    rate_limit_per_hour: int

    active: bool
    suspended: bool
    suspension_reason: str | None

    created_at: datetime | None
    created_by: int | None
    updated_at: datetime | None
    updated_by: int | None
    deleted_at: datetime | None
    deleted_by: int | None

    @field_validator("has_api_key", mode="before")
    @classmethod
    def _derive_has_api_key(cls, v: Any) -> bool:
        # This field is computed in the router before serialisation
        return bool(v)


class TenantListResponse(BaseModel):
    """Paginated list wrapper."""

    total: int
    page: int
    page_size: int
    items: list[TenantResponse]
