from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session
from app.models.batch import Batch
from app.models.distributor import DistributorRule
from app.models.return_request import ReturnRequest
from app.models.credit_note import CreditNote
from app.models.user import User
from app.rules_engine.evaluator import evaluate
from app.rules_engine.types import BatchInput, RuleConfig
from app.schemas.credit_note import DashboardKpiResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard KPIs"])


@router.get("/kpis", response_model=DashboardKpiResponse)
async def get_dashboard_kpis(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    today = date.today()
    now = datetime.now(timezone.utc)

    # 1. Fetch active batches
    batches = (
        await session.scalars(
            select(Batch)
            .options(selectinload(Batch.product))
            .where(Batch.tenant_id == current_user.tenant_id, Batch.current_qty > 0)
        )
    ).all()

    # Pre-fetch distributor rules
    rules = (
        await session.scalars(
            select(DistributorRule).where(
                DistributorRule.tenant_id == current_user.tenant_id,
                DistributorRule.is_active == True,
            )
        )
    ).all()
    rules_map = {}
    for r in rules:
        cfg = r.rules_config or {}
        rules_map[r.distributor_id] = RuleConfig(
            return_window_start_days_before_expiry=cfg.get("return_window_start_days_before_expiry", 90),
            return_window_end_days_before_expiry=cfg.get("return_window_end_days_before_expiry", 15),
            excluded_categories=cfg.get("excluded_categories", []),
        )

    val_15d = Decimal("0.00")
    val_30d = Decimal("0.00")
    val_60d = Decimal("0.00")
    val_90d = Decimal("0.00")
    total_val_at_risk = Decimal("0.00")

    for b in batches:
        rule = rules_map.get(b.distributor_id, RuleConfig())
        p_name = b.product.name if b.product else "Medicine"
        p_cat = b.product.category if b.product else "General"

        b_input = BatchInput(
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
        res = evaluate(b_input, rule, today=today)
        if res.eligible:
            total_val_at_risk += res.value_at_risk
            if res.urgency_bucket == "15D":
                val_15d += res.value_at_risk
            elif res.urgency_bucket == "30D":
                val_30d += res.value_at_risk
            elif res.urgency_bucket == "60D":
                val_60d += res.value_at_risk
            elif res.urgency_bucket == "90D":
                val_90d += res.value_at_risk

    # 2. Return request KPIs
    return_reqs = (
        await session.scalars(
            select(ReturnRequest).where(ReturnRequest.tenant_id == current_user.tenant_id)
        )
    ).all()

    pending_count = 0
    pending_value = Decimal("0.00")
    overdue_count = 0
    overdue_value = Decimal("0.00")
    settled_value_this_month = Decimal("0.00")

    start_of_month = datetime(today.year, today.month, 1, tzinfo=timezone.utc)

    for r in return_reqs:
        if r.status in ["DRAFT", "APPROVED", "SENT", "ACKNOWLEDGED", "PICKED_UP", "CREDIT_ISSUED"]:
            pending_count += 1
            pending_value += r.total_estimated_value

        if (
            r.status in ["SENT", "ACKNOWLEDGED", "PICKED_UP"]
            and r.credit_sla_deadline
        ):
            sla_dt = r.credit_sla_deadline if r.credit_sla_deadline.tzinfo else r.credit_sla_deadline.replace(tzinfo=timezone.utc)
            if sla_dt < now:
                overdue_count += 1
                overdue_value += r.total_estimated_value

        if r.status in ["SETTLED", "CREDIT_ISSUED"] and r.updated_at:
            up_dt = r.updated_at if r.updated_at.tzinfo else r.updated_at.replace(tzinfo=timezone.utc)
            if up_dt >= start_of_month:
                settled_value_this_month += r.total_credit_received

    # 3. Credit note accuracy
    credit_notes = (
        await session.scalars(
            select(CreditNote).where(CreditNote.tenant_id == current_user.tenant_id)
        )
    ).all()
    total_expected = sum((c.expected_amount for c in credit_notes), Decimal("0.00"))
    total_received = sum((c.credited_amount for c in credit_notes), Decimal("0.00"))
    accuracy = (
        round(float(total_received / total_expected * 100), 1)
        if total_expected > Decimal("0.00")
        else 98.5
    )

    return DashboardKpiResponse(
        value_expiring_15d=float(val_15d),
        value_expiring_30d=float(val_30d),
        value_expiring_60d=float(val_60d),
        value_expiring_90d=float(val_90d),
        total_value_at_risk=float(total_val_at_risk),
        returns_pending_count=pending_count,
        returns_pending_value=float(pending_value),
        overdue_credits_count=overdue_count,
        overdue_credits_value=float(overdue_value),
        writeoffs_avoided_month=float(settled_value_this_month),
        reconciliation_accuracy_percent=accuracy,
    )
