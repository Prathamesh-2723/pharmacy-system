import uuid
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.distributor import Distributor, DistributorRule
from app.models.return_request import ReturnRequest
from app.models.credit_note import CreditNote
from app.models.user import User
from app.schemas.distributor import (
    DistributorCreate,
    DistributorRuleCreate,
    DistributorRuleResponse,
    DistributorScorecard,
)

router = APIRouter(prefix="/distributors", tags=["Distributors"])


@router.get("", response_model=List[DistributorScorecard])
async def list_distributors(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    # Fetch distributors with their rules
    dists = (
        await session.scalars(
            select(Distributor)
            .options(selectinload(Distributor.rules))
            .where(Distributor.tenant_id == current_user.tenant_id)
            .order_by(Distributor.name)
        )
    ).all()

    # Preload return request stats for tenant
    ret_reqs = (
        await session.scalars(
            select(ReturnRequest).where(ReturnRequest.tenant_id == current_user.tenant_id)
        )
    ).all()

    # Group metrics per distributor
    dist_returns_count = {}
    dist_returned_val = {}
    for r in ret_reqs:
        dist_returns_count[r.distributor_id] = dist_returns_count.get(r.distributor_id, 0) + (
            1 if r.status in ["SENT", "ACKNOWLEDGED", "PICKED_UP", "CREDIT_ISSUED"] else 0
        )
        dist_returned_val[r.distributor_id] = dist_returned_val.get(r.distributor_id, 0.0) + float(
            r.total_credit_received
        )

    scorecards = []
    for d in dists:
        active_r = next((r for r in d.rules if r.is_active), None)
        rule_cfg = active_r.rules_config if active_r else None
        scorecards.append(
            DistributorScorecard(
                id=d.id,
                name=d.name,
                code=d.code,
                contact_person=d.contact_person,
                phone=d.phone,
                email=d.email,
                is_active=d.is_active,
                active_rule=rule_cfg,
                active_returns_count=dist_returns_count.get(d.id, 0),
                total_returned_value=dist_returned_val.get(d.id, 0.0),
                avg_credit_turnaround_days=float(rule_cfg.get("credit_note_sla_days", 14) if rule_cfg else 14),
                rejection_rate_percent=0.0,
            )
        )
    return scorecards


@router.post("", response_model=DistributorScorecard, status_code=status.HTTP_201_CREATED)
async def create_distributor(
    body: DistributorCreate,
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    dist_id = str(uuid.uuid4())
    dist = Distributor(
        id=dist_id,
        tenant_id=current_user.tenant_id,
        name=body.name,
        code=body.code or body.name[:6].upper().replace(" ", ""),
        contact_person=body.contact_person,
        email=body.email,
        phone=body.phone,
        address=body.address,
        gstin=body.gstin,
    )
    session.add(dist)
    await session.flush()

    rule_dict = (
        body.rule.model_dump(mode="json")
        if body.rule
        else {
            "return_window_start_days_before_expiry": 90,
            "return_window_end_days_before_expiry": 15,
            "excluded_categories": ["Cold Chain"],
            "requires_prior_authorization": False,
            "return_format": "standard_v1",
            "pickup_days": ["Monday", "Thursday"],
            "credit_note_sla_days": 14,
            "min_return_value": 0.0,
        }
    )
    rule = DistributorRule(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        distributor_id=dist_id,
        version=1,
        rules_config=rule_dict,
        is_active=True,
    )
    session.add(rule)
    await session.commit()

    return DistributorScorecard(
        id=dist.id,
        name=dist.name,
        code=dist.code,
        contact_person=dist.contact_person,
        phone=dist.phone,
        email=dist.email,
        is_active=dist.is_active,
        active_rule=rule_dict,
    )


@router.get("/{id}/rules", response_model=List[DistributorRuleResponse])
async def get_distributor_rules(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    rules = (
        await session.scalars(
            select(DistributorRule)
            .where(DistributorRule.distributor_id == id, DistributorRule.tenant_id == current_user.tenant_id)
            .order_by(DistributorRule.version.desc())
        )
    ).all()
    return rules


@router.post("/{id}/rules", response_model=DistributorRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_new_rule_version(
    id: str,
    body: DistributorRuleCreate,
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify distributor belongs to tenant
    dist = (
        await session.scalars(
            select(Distributor).where(Distributor.id == id, Distributor.tenant_id == current_user.tenant_id)
        )
    ).first()
    if not dist:
        raise HTTPException(status_code=404, detail="Distributor not found")

    # Get max current version
    current_max_v = await session.scalar(
        select(func.coalesce(func.max(DistributorRule.version), 0)).where(
            DistributorRule.distributor_id == id, DistributorRule.tenant_id == current_user.tenant_id
        )
    )
    new_version = current_max_v + 1

    # Deactivate existing active rules
    existing_rules = (
        await session.scalars(
            select(DistributorRule).where(
                DistributorRule.distributor_id == id, DistributorRule.tenant_id == current_user.tenant_id
            )
        )
    ).all()
    for r in existing_rules:
        r.is_active = False

    new_rule = DistributorRule(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        distributor_id=id,
        version=new_version,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
        rules_config=body.rules_config.model_dump(mode="json"),
        is_active=True,
    )
    session.add(new_rule)
    await session.commit()
    await session.refresh(new_rule)
    return new_rule
