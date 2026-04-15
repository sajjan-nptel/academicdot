import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    # Core Identity
    node_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        server_default=func.gen_random_uuid(),
    )
    node_name: Mapped[str] = mapped_column(String(255), nullable=False)
    node_abbreviation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    node_slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    node_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Contact & Location
    node_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    node_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    node_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    node_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    node_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    node_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    time_zone: Mapped[str] = mapped_column(String(100), nullable=False, server_default="UTC")
    locale: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en-US")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")

    # Branding & Theme
    colour_theme: Mapped[str] = mapped_column(String(50), nullable=False, server_default="default")
    custom_theme_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand_colors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # URLs & Endpoints
    subdomain: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    custom_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system_frontend_url: Mapped[str] = mapped_column(String(255), nullable=False)
    system_backend_url: Mapped[str] = mapped_column(String(255), nullable=False)
    api_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_endpoint_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Database Connection
    db_host: Mapped[str] = mapped_column(String(255), nullable=False)
    db_port: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5432")
    db_name: Mapped[str] = mapped_column(String(100), nullable=False)
    db_user_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    db_password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    db_connection_pool_size: Mapped[int] = mapped_column(Integer, nullable=False, server_default="10")
    db_ssl_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Features & Limits
    features_enabled: Mapped[list | None] = mapped_column(JSONB, nullable=True, server_default="[]")
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    max_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_storage_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1000")

    # Status & Lifecycle
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint(r"subdomain ~ '^[a-z0-9-]+$'", name="valid_subdomain"),
    )
