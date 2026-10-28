import asyncio
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.batch import Batch
from app.models.distributor import Distributor, DistributorRule
from app.models.product import Product
from app.rules_engine.evaluator import evaluate
from app.rules_engine.types import BatchInput, RuleConfig, EvaluationResult
from app.tasks.celery_app import celery_app


async def scan_batches_for_tenant(
    session,
    tenant_id: Optional[str] = None,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Core scanner logic: evaluates all active batches, classifies urgency buckets,
    computes priority scores, and identifies return-window-closing-soon batches.
    """
    if today is None:
        today = date.today()

    query = (
        select(Batch)
        .options(selectinload(Batch.product), selectinload(Batch.distributor))
        .where(Batch.status == "ACTIVE", Batch.current_qty > 0)
    )
    if tenant_id:
        query = query.where(Batch.tenant_id == tenant_id)

    batches = (await session.scalars(query)).all()

    # Pre-fetch distributor active rules
    dist_ids = list({b.distributor_id for b in batches})
    rules_map: Dict[str, RuleConfig] = {}
    if dist_ids:
        rules_query = select(DistributorRule).where(
            DistributorRule.distributor_id.in_(dist_ids),
            DistributorRule.is_active == True,
        )
        if tenant_id:
            rules_query = rules_query.where(DistributorRule.tenant_id == tenant_id)
        rules = (await session.scalars(rules_query)).all()
        for r in rules:
            cfg = r.rules_config or {}
            rules_map[r.distributor_id] = RuleConfig(
                return_window_start_days_before_expiry=cfg.get("return_window_start_days_before_expiry", 90),
                return_window_end_days_before_expiry=cfg.get("return_window_end_days_before_expiry", 15),
                excluded_categories=cfg.get("excluded_categories", []),
                requires_prior_authorization=cfg.get("requires_prior_authorization", False),
                return_format=cfg.get("return_format", "standard_v1"),
                pickup_days=cfg.get("pickup_days", ["Monday", "Thursday"]),
                credit_note_sla_days=cfg.get("credit_note_sla_days", 14),
                min_return_value=Decimal(str(cfg.get("min_return_value", "0.00"))),
                version=r.version,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
            )

    scanned_results: List[Dict[str, Any]] = []
    bucket_summary = {"EXPIRED": 0, "15D": 0, "30D": 0, "60D": 0, "90D": 0, "FUTURE": 0}
    total_value_at_risk = Decimal("0.00")
    closing_soon_count = 0
    eligible_count = 0

    for b in batches:
        rule = rules_map.get(b.distributor_id, RuleConfig())
        batch_input = BatchInput(
            id=b.id,
            product_id=b.product_id,
            product_name=b.product.name if b.product else "Unknown",
            category=b.product.category if b.product else "General",
            batch_no=b.batch_no,
            expiry_date=b.expiry_date,
            current_qty=b.current_qty,
            purchase_price=b.purchase_price,
            mrp=b.mrp,
            distributor_id=b.distributor_id,
        )
        res = evaluate(batch_input, rule, today=today)

        bucket_summary[res.urgency_bucket] = bucket_summary.get(res.urgency_bucket, 0) + 1
        if res.eligible:
            eligible_count += 1
            total_value_at_risk += res.value_at_risk
            # Flag window closing soon (7 days or less before window closes)
            if 0 <= res.days_to_window_close <= 7:
                closing_soon_count += 1

        scanned_results.append({
            "batch_id": b.id,
            "batch_no": b.batch_no,
            "product_name": batch_input.product_name,
            "distributor_id": b.distributor_id,
            "distributor_name": b.distributor.name if b.distributor else "Unknown",
            "expiry_date": str(b.expiry_date),
            "current_qty": b.current_qty,
            "purchase_price": float(b.purchase_price),
            "value_at_risk": float(res.value_at_risk),
            "urgency_bucket": res.urgency_bucket,
            "eligible": res.eligible,
            "window_opens_on": str(res.window_opens_on),
            "window_closes_on": str(res.window_closes_on),
            "days_to_window_close": res.days_to_window_close,
            "days_to_expiry": res.days_to_expiry,
            "blocked_reason": res.blocked_reason,
            "priority_score": res.priority_score,
            "window_closing_soon": res.eligible and (0 <= res.days_to_window_close <= 7),
        })

    # Sort batches by priority score descending
    scanned_results.sort(key=lambda x: x["priority_score"], reverse=True)

    return {
        "scan_date": str(today),
        "total_batches_scanned": len(batches),
        "eligible_for_return": eligible_count,
        "window_closing_soon": closing_soon_count,
        "total_value_at_risk": float(total_value_at_risk),
        "bucket_summary": bucket_summary,
        "batches": scanned_results,
    }


@celery_app.task(name="app.tasks.expiry_scanner.run_daily_expiry_scan")
def run_daily_expiry_scan():
    """Celery beat task entry point."""
    async def _runner():
        async with async_session_factory() as session:
            return await scan_batches_for_tenant(session)

    loop = asyncio.get_event_loop()
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _runner()).result()
    else:
        return asyncio.run(_runner())
