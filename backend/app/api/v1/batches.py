import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.batch import Batch
from app.models.distributor import Distributor, DistributorRule
from app.models.product import Product
from app.models.user import User
from app.rules_engine.evaluator import evaluate
from app.rules_engine.types import BatchInput, RuleConfig
from app.schemas.batch import BatchDetailResponse, ManualBatchCreate

router = APIRouter(prefix="/batches", tags=["Batches & Expiry Risk"])


@router.get("", response_model=List[BatchDetailResponse])
async def list_batches(
    search: Optional[str] = Query(None, description="Search product name or batch no"),
    distributor_id: Optional[str] = Query(None),
    urgency_bucket: Optional[str] = Query(None),
    eligible_only: bool = Query(False),
    closing_soon_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(Batch)
        .options(selectinload(Batch.product), selectinload(Batch.distributor))
        .where(Batch.tenant_id == current_user.tenant_id, Batch.current_qty > 0)
    )
    if distributor_id:
        query = query.where(Batch.distributor_id == distributor_id)

    batches = (await session.scalars(query)).all()

    # Pre-fetch rules
    rules = (
        await session.scalars(
            select(DistributorRule).where(
                DistributorRule.tenant_id == current_user.tenant_id,
                DistributorRule.is_active == True,
            )
        )
    ).all()
    rules_map: Dict[str, RuleConfig] = {}
    for r in rules:
        cfg = r.rules_config or {}
        rules_map[r.distributor_id] = RuleConfig(
            return_window_start_days_before_expiry=cfg.get("return_window_start_days_before_expiry", 90),
            return_window_end_days_before_expiry=cfg.get("return_window_end_days_before_expiry", 15),
            excluded_categories=cfg.get("excluded_categories", []),
            requires_prior_authorization=cfg.get("requires_prior_authorization", False),
            return_format=cfg.get("return_format", "standard_v1"),
            credit_note_sla_days=cfg.get("credit_note_sla_days", 14),
            min_return_value=Decimal(str(cfg.get("min_return_value", "0.00"))),
            version=r.version,
        )

    today = date.today()
    results = []

    for b in batches:
        rule = rules_map.get(b.distributor_id, RuleConfig())
        p_name = b.product.name if b.product else "Unknown"
        p_cat = b.product.category if b.product else "General"
        d_name = b.distributor.name if b.distributor else "Unknown"

        # Search filter
        if search:
            q = search.lower()
            if q not in p_name.lower() and q not in b.batch_no.lower():
                continue

        batch_input = BatchInput(
            id=b.id,
            product_id=b.product_id,
            product_name=p_name,
            category=p_cat,
            batch_no=b.batch_no,
            expiry_date=b.expiry_date,
            current_qty=b.current_qty,
            purchase_price=b.purchase_price,
            distributor_id=b.distributor_id,
        )
        res = evaluate(batch_input, rule, today=today)

        # Filters
        if urgency_bucket and res.urgency_bucket.lower() != urgency_bucket.lower():
            continue
        if eligible_only and not res.eligible:
            continue
        closing_soon = res.eligible and (0 <= res.days_to_window_close <= 7)
        if closing_soon_only and not closing_soon:
            continue

        results.append(
            BatchDetailResponse(
                id=b.id,
                product_id=b.product_id,
                product_name=p_name,
                category=p_cat,
                distributor_id=b.distributor_id,
                distributor_name=d_name,
                batch_no=b.batch_no,
                expiry_date=b.expiry_date,
                initial_qty=b.initial_qty,
                current_qty=b.current_qty,
                purchase_price=float(b.purchase_price),
                mrp=float(b.mrp) if b.mrp else None,
                invoice_ref=b.invoice_ref,
                status=b.status,
                value_at_risk=float(res.value_at_risk),
                urgency_bucket=res.urgency_bucket,
                eligible=res.eligible,
                window_opens_on=str(res.window_opens_on),
                window_closes_on=str(res.window_closes_on),
                days_to_window_close=res.days_to_window_close,
                days_to_expiry=res.days_to_expiry,
                blocked_reason=res.blocked_reason,
                priority_score=res.priority_score,
                window_closing_soon=closing_soon,
            )
        )

    # Sort by priority score descending
    results.sort(key=lambda x: x.priority_score, reverse=True)
    return results


@router.post("/manual", response_model=BatchDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_batch(
    body: ManualBatchCreate,
    current_user: User = Depends(require_roles(["owner", "pharmacist", "staff"])),
    session: AsyncSession = Depends(get_db_session),
):
    # Verify distributor exists
    dist = (
        await session.scalars(
            select(Distributor).where(
                Distributor.id == body.distributor_id,
                Distributor.tenant_id == current_user.tenant_id,
            )
        )
    ).first()
    if not dist:
        raise HTTPException(status_code=404, detail="Distributor not found")

    # Find or create product
    prod = (
        await session.scalars(
            select(Product).where(
                Product.tenant_id == current_user.tenant_id,
                Product.name == body.product_name,
            )
        )
    ).first()
    if not prod:
        prod = Product(
            id=str(uuid.uuid4()),
            tenant_id=current_user.tenant_id,
            sku=f"SKU-{abs(hash(body.product_name)) % 100000:05d}",
            name=body.product_name,
            category=body.category,
            default_distributor_id=dist.id,
        )
        session.add(prod)
        await session.flush()

    batch = Batch(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        product_id=prod.id,
        distributor_id=dist.id,
        batch_no=body.batch_no,
        expiry_date=body.expiry_date,
        initial_qty=body.qty,
        current_qty=body.qty,
        purchase_price=body.purchase_price,
        mrp=body.mrp or (body.purchase_price * Decimal("1.25")),
        invoice_ref=body.invoice_ref,
        purchase_date=date.today(),
        status="ACTIVE",
    )
    session.add(batch)
    await session.commit()

    # Rule evaluation
    rule_db = (
        await session.scalars(
            select(DistributorRule).where(
                DistributorRule.distributor_id == dist.id,
                DistributorRule.is_active == True,
            )
        )
    ).first()
    rule_cfg = (
        RuleConfig(
            return_window_start_days_before_expiry=rule_db.rules_config.get("return_window_start_days_before_expiry", 90),
            return_window_end_days_before_expiry=rule_db.rules_config.get("return_window_end_days_before_expiry", 15),
            excluded_categories=rule_db.rules_config.get("excluded_categories", []),
        )
        if rule_db and rule_db.rules_config
        else RuleConfig()
    )

    b_input = BatchInput(
        id=batch.id,
        product_id=prod.id,
        product_name=prod.name,
        category=prod.category,
        batch_no=batch.batch_no,
        expiry_date=batch.expiry_date,
        current_qty=batch.current_qty,
        purchase_price=batch.purchase_price,
        distributor_id=dist.id,
    )
    res = evaluate(b_input, rule_cfg, today=date.today())

    return BatchDetailResponse(
        id=batch.id,
        product_id=prod.id,
        product_name=prod.name,
        category=prod.category,
        distributor_id=dist.id,
        distributor_name=dist.name,
        batch_no=batch.batch_no,
        expiry_date=batch.expiry_date,
        initial_qty=batch.initial_qty,
        current_qty=batch.current_qty,
        purchase_price=float(batch.purchase_price),
        mrp=float(batch.mrp) if batch.mrp else None,
        invoice_ref=batch.invoice_ref,
        status=batch.status,
        value_at_risk=float(res.value_at_risk),
        urgency_bucket=res.urgency_bucket,
        eligible=res.eligible,
        window_opens_on=str(res.window_opens_on),
        window_closes_on=str(res.window_closes_on),
        days_to_window_close=res.days_to_window_close,
        days_to_expiry=res.days_to_expiry,
        blocked_reason=res.blocked_reason,
        priority_score=res.priority_score,
        window_closing_soon=res.eligible and (0 <= res.days_to_window_close <= 7),
    )
