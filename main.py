import logging
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from encryption import encrypt, is_encryption_configured
from models import Tenant
from schemas import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title="AcademicDot Tenants API",
    description="CRUD API for managing multi-tenant organisations in AcademicDot.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _to_response(tenant: Tenant) -> TenantResponse:
    """Convert ORM model → response schema, masking encrypted fields."""
    data = {col.key: getattr(tenant, col.key) for col in tenant.__table__.columns}
    data["has_api_key"] = bool(tenant.api_endpoint_key_encrypted)
    return TenantResponse(**data)


async def _get_active_tenant_by_id(node_id: int, db: AsyncSession) -> Tenant:
    result = await db.execute(
        select(Tenant).where(
            Tenant.node_id == node_id,
            Tenant.deleted_at.is_(None),
        )
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with node_id={node_id} not found.",
        )
    return tenant


# ---------------------------------------------------------------------------
# Startup / Shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("AcademicDot Tenants API starting up.")
    if not is_encryption_configured():
        logger.warning(
            "ENCRYPTION_KEY is not set. Encrypted-field operations will fail."
        )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("AcademicDot Tenants API shutting down.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /tenants/search  — must be registered BEFORE /tenants/{tenant_id}
# ---------------------------------------------------------------------------


@app.get(
    "/tenants/search",
    response_model=TenantListResponse,
    tags=["Tenants"],
    summary="Search tenants by name or email",
)
async def search_tenants(
    db: DbSession,
    q: str = Query(..., min_length=1, description="Search term"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TenantListResponse:
    """Full-text style search across *node_name*, *node_email*, and *node_slug*."""
    like_term = f"%{q}%"
    base_query = select(Tenant).where(
        Tenant.deleted_at.is_(None),
        or_(
            Tenant.node_name.ilike(like_term),
            Tenant.node_email.ilike(like_term),
            Tenant.node_slug.ilike(like_term),
        ),
    )

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total: int = count_result.scalar_one()

    rows = await db.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    )
    tenants = rows.scalars().all()

    return TenantListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_response(t) for t in tenants],
    )


# ---------------------------------------------------------------------------
# GET /tenants/by-subdomain/{subdomain}
# ---------------------------------------------------------------------------


@app.get(
    "/tenants/by-subdomain/{subdomain}",
    response_model=TenantResponse,
    tags=["Tenants"],
    summary="Get tenant by subdomain",
)
async def get_tenant_by_subdomain(subdomain: str, db: DbSession) -> TenantResponse:
    result = await db.execute(
        select(Tenant).where(
            Tenant.subdomain == subdomain,
            Tenant.deleted_at.is_(None),
        )
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with subdomain='{subdomain}' not found.",
        )
    return _to_response(tenant)


# ---------------------------------------------------------------------------
# GET /tenants/by-slug/{node_slug}
# ---------------------------------------------------------------------------


@app.get(
    "/tenants/by-slug/{node_slug}",
    response_model=TenantResponse,
    tags=["Tenants"],
    summary="Get tenant by slug",
)
async def get_tenant_by_slug(node_slug: str, db: DbSession) -> TenantResponse:
    result = await db.execute(
        select(Tenant).where(
            Tenant.node_slug == node_slug,
            Tenant.deleted_at.is_(None),
        )
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with node_slug='{node_slug}' not found.",
        )
    return _to_response(tenant)


# ---------------------------------------------------------------------------
# GET /tenants/
# ---------------------------------------------------------------------------


@app.get(
    "/tenants/",
    response_model=TenantListResponse,
    tags=["Tenants"],
    summary="List all active tenants with pagination",
)
async def list_tenants(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True, description="Return only active (non-suspended) tenants"),
) -> TenantListResponse:
    base_query = select(Tenant).where(Tenant.deleted_at.is_(None))
    if active_only:
        base_query = base_query.where(Tenant.active.is_(True), Tenant.suspended.is_(False))

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total: int = count_result.scalar_one()

    rows = await db.execute(
        base_query.order_by(Tenant.node_id).offset((page - 1) * page_size).limit(page_size)
    )
    tenants = rows.scalars().all()

    return TenantListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_response(t) for t in tenants],
    )


# ---------------------------------------------------------------------------
# GET /tenants/{tenant_id}
# ---------------------------------------------------------------------------


@app.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    tags=["Tenants"],
    summary="Get specific tenant by node_id",
)
async def get_tenant(tenant_id: int, db: DbSession) -> TenantResponse:
    tenant = await _get_active_tenant_by_id(tenant_id, db)
    return _to_response(tenant)


# ---------------------------------------------------------------------------
# POST /tenants/
# ---------------------------------------------------------------------------


@app.post(
    "/tenants/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tenants"],
    summary="Create a new tenant",
)
async def create_tenant(payload: TenantCreate, db: DbSession) -> TenantResponse:
    # Check uniqueness constraints
    dup = await db.execute(
        select(Tenant).where(
            or_(
                Tenant.subdomain == payload.subdomain,
                Tenant.node_slug == payload.node_slug,
            ),
            Tenant.deleted_at.is_(None),
        )
    )
    if dup.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tenant with the same subdomain or slug already exists.",
        )

    # Encrypt sensitive fields
    try:
        db_user_encrypted = encrypt(payload.db_user)
        db_password_encrypted = encrypt(payload.db_password)
        api_key_encrypted = encrypt(payload.api_endpoint_key) if payload.api_endpoint_key else None
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption error: {exc}",
        )

    tenant_data = payload.model_dump(
        exclude={"db_user", "db_password", "api_endpoint_key"}
    )
    tenant = Tenant(
        **tenant_data,
        db_user_encrypted=db_user_encrypted,
        db_password_encrypted=db_password_encrypted,
        api_endpoint_key_encrypted=api_key_encrypted,
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return _to_response(tenant)


# ---------------------------------------------------------------------------
# PUT /tenants/{tenant_id}
# ---------------------------------------------------------------------------


@app.put(
    "/tenants/{tenant_id}",
    response_model=TenantResponse,
    tags=["Tenants"],
    summary="Update existing tenant",
)
async def update_tenant(
    tenant_id: int, payload: TenantUpdate, db: DbSession
) -> TenantResponse:
    tenant = await _get_active_tenant_by_id(tenant_id, db)

    update_data = payload.model_dump(exclude_none=True)

    # Handle encrypted fields
    if "db_user" in update_data:
        try:
            tenant.db_user_encrypted = encrypt(update_data.pop("db_user"))
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=f"Encryption error: {exc}")
    else:
        update_data.pop("db_user", None)

    if "db_password" in update_data:
        try:
            tenant.db_password_encrypted = encrypt(update_data.pop("db_password"))
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=f"Encryption error: {exc}")
    else:
        update_data.pop("db_password", None)

    if "api_endpoint_key" in update_data:
        try:
            tenant.api_endpoint_key_encrypted = encrypt(update_data.pop("api_endpoint_key"))
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=f"Encryption error: {exc}")
    else:
        update_data.pop("api_endpoint_key", None)

    # Check slug/subdomain uniqueness if being changed
    new_slug = update_data.get("node_slug")
    new_subdomain = update_data.get("subdomain")
    if new_slug or new_subdomain:
        conditions = []
        if new_slug:
            conditions.append(Tenant.node_slug == new_slug)
        if new_subdomain:
            conditions.append(Tenant.subdomain == new_subdomain)
        dup = await db.execute(
            select(Tenant).where(
                or_(*conditions),
                Tenant.node_id != tenant_id,
                Tenant.deleted_at.is_(None),
            )
        )
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another tenant already uses the same subdomain or slug.",
            )

    update_data["updated_at"] = datetime.now(timezone.utc)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.flush()
    await db.refresh(tenant)
    return _to_response(tenant)


# ---------------------------------------------------------------------------
# DELETE /tenants/{tenant_id}  (soft delete)
# ---------------------------------------------------------------------------


@app.delete(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tenants"],
    summary="Soft delete tenant",
)
async def delete_tenant(
    tenant_id: int,
    db: DbSession,
    deleted_by: Optional[int] = Query(None, description="Admin user ID performing the deletion"),
) -> None:
    tenant = await _get_active_tenant_by_id(tenant_id, db)
    tenant.deleted_at = datetime.now(timezone.utc)
    tenant.deleted_by = deleted_by
    tenant.active = False
    await db.flush()
