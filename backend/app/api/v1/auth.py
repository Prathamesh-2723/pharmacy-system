from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserMeResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    user = (
        await session.scalars(
            select(User)
            .options(selectinload(User.tenant))
            .where(User.email == body.email)
        )
    ).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        tenant_id=user.tenant_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        full_name=user.full_name,
        tenant_name=user.tenant.name if user.tenant else "Pharmacy",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = (
        await session.scalars(
            select(User)
            .options(selectinload(User.tenant))
            .where(User.id == user_id, User.tenant_id == tenant_id)
        )
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active",
        )

    new_access = create_access_token(subject=user.id, tenant_id=user.tenant_id, role=user.role)
    new_refresh = create_refresh_token(subject=user.id, tenant_id=user.tenant_id)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
        full_name=user.full_name,
        tenant_name=user.tenant.name if user.tenant else "Pharmacy",
    )


@router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name if current_user.tenant else "Pharmacy",
        tenant_slug=current_user.tenant.slug if current_user.tenant else "pharmacy",
    )
