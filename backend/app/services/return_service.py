import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tenant import Tenant
from app.models.distributor import Distributor, DistributorRule
from app.models.batch import Batch
from app.models.return_request import ReturnRequest, ReturnRequestItem, ReturnStatusEvent
from app.models.notification import Notification
from app.rules_engine.evaluator import evaluate
from app.rules_engine.types import BatchInput, RuleConfig
from app.services.template_service import template_renderer
from app.services.notifications import get_notification_provider, NotificationMessage


VALID_TRANSITIONS = {
    "DRAFT": ["APPROVED", "REJECTED"],
    "APPROVED": ["SENT", "REJECTED"],
    "SENT": ["ACKNOWLEDGED", "PICKED_UP", "DISPUTED", "REJECTED"],
    "ACKNOWLEDGED": ["PICKED_UP", "CREDIT_ISSUED", "DISPUTED", "REJECTED"],
    "PICKED_UP": ["CREDIT_ISSUED", "SETTLED", "DISPUTED"],
    "CREDIT_ISSUED": ["SETTLED", "DISPUTED"],
    "DISPUTED": ["CREDIT_ISSUED", "SETTLED", "REJECTED"],
    "REJECTED": ["DRAFT"],
    "SETTLED": [],
}


class ReturnService:
    @classmethod
    async def auto_generate_draft_returns(
        cls,
        session: AsyncSession,
        tenant_id: str,
        today: Optional[date] = None,
    ) -> List[ReturnRequest]:
        """
        Scans all eligible active batches and groups them per distributor
        into draft return requests.
        """
        if today is None:
            today = date.today()

        # Find active batches with positive quantity
        batches = (
            await session.scalars(
                select(Batch)
                .options(selectinload(Batch.product), selectinload(Batch.distributor))
                .where(
                    Batch.tenant_id == tenant_id,
                    Batch.status == "ACTIVE",
                    Batch.current_qty > 0,
                )
            )
        ).all()

        if not batches:
            return []

        # Fetch active rules for distributors
        dist_ids = list({b.distributor_id for b in batches})
        rules_query = select(DistributorRule).where(
            DistributorRule.tenant_id == tenant_id,
            DistributorRule.distributor_id.in_(dist_ids),
            DistributorRule.is_active == True,
        )
        rules = (await session.scalars(rules_query)).all()
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

        # Evaluate eligibility and group by distributor
        distributor_eligible_batches: Dict[str, List[Tuple[Batch, Decimal]]] = {}

        for b in batches:
            rule = rules_map.get(b.distributor_id, RuleConfig())
            b_input = BatchInput(
                id=b.id,
                product_id=b.product_id,
                product_name=b.product.name if b.product else "Unknown",
                category=b.product.category if b.product else "General",
                batch_no=b.batch_no,
                expiry_date=b.expiry_date,
                current_qty=b.current_qty,
                purchase_price=b.purchase_price,
                distributor_id=b.distributor_id,
            )
            eval_res = evaluate(b_input, rule, today=today)
            if eval_res.eligible:
                if b.distributor_id not in distributor_eligible_batches:
                    distributor_eligible_batches[b.distributor_id] = []
                distributor_eligible_batches[b.distributor_id].append((b, eval_res.value_at_risk))

        created_returns: List[ReturnRequest] = []

        # Existing draft return requests for each distributor
        for dist_id, items in distributor_eligible_batches.items():
            if not items:
                continue

            # Check if an open DRAFT already exists for this distributor
            existing_draft = (
                await session.scalars(
                    select(ReturnRequest).where(
                        ReturnRequest.tenant_id == tenant_id,
                        ReturnRequest.distributor_id == dist_id,
                        ReturnRequest.status == "DRAFT",
                    )
                )
            ).first()

            if existing_draft:
                draft_return = existing_draft
            else:
                req_no = f"RET-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
                draft_return = ReturnRequest(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    distributor_id=dist_id,
                    return_request_no=req_no,
                    status="DRAFT",
                    total_estimated_value=Decimal("0.00"),
                    item_count=0,
                )
                session.add(draft_return)
                await session.flush()

                # Audit event
                session.add(
                    ReturnStatusEvent(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        return_request_id=draft_return.id,
                        from_status=None,
                        to_status="DRAFT",
                        trigger="AUTO_SCANNER",
                        comment="Auto-drafted by return rules scanner",
                    )
                )

            total_added_val = Decimal("0.00")
            count_added = 0

            # Attach items
            for batch, val in items:
                # Check if item already in this return
                existing_item = (
                    await session.scalars(
                        select(ReturnRequestItem).where(
                            ReturnRequestItem.return_request_id == draft_return.id,
                            ReturnRequestItem.batch_id == batch.id,
                        )
                    )
                ).first()

                if not existing_item:
                    item_rec = ReturnRequestItem(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        return_request_id=draft_return.id,
                        batch_id=batch.id,
                        requested_qty=batch.current_qty,
                        unit_purchase_price=batch.purchase_price,
                        total_value=val,
                        reason="Near Expiry Window Active",
                    )
                    session.add(item_rec)
                    batch.status = "RETURNING"
                    total_added_val += val
                    count_added += 1

            draft_return.total_estimated_value += total_added_val
            draft_return.item_count += count_added
            created_returns.append(draft_return)

        await session.commit()
        return created_returns

    @classmethod
    async def transition_status(
        cls,
        session: AsyncSession,
        return_request_id: str,
        to_status: str,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ReturnRequest:
        """
        Executes return state machine transition with validation,
        audit logging, and dispatch triggering.
        """
        query = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items).selectinload(ReturnRequestItem.batch).selectinload(Batch.product),
                selectinload(ReturnRequest.tenant),
            )
            .where(ReturnRequest.id == return_request_id)
        )
        if tenant_id:
            query = query.where(ReturnRequest.tenant_id == tenant_id)

        ret = (await session.scalars(query)).first()
        if not ret:
            raise ValueError(f"ReturnRequest with ID {return_request_id} not found")

        from_status = ret.status
        allowed = VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed:
            raise ValueError(
                f"Invalid transition from {from_status} to {to_status}. Allowed: {allowed}"
            )

        now = datetime.now(timezone.utc)
        ret.status = to_status

        # Transition specifics
        if to_status == "APPROVED":
            ret.approved_at = now
            ret.approved_by = user_id

        elif to_status == "SENT":
            ret.dispatched_at = now
            # Compute Credit SLA deadline
            sla_days = 14
            # Look up active rule
            rule = (
                await session.scalars(
                    select(DistributorRule).where(
                        DistributorRule.distributor_id == ret.distributor_id,
                        DistributorRule.is_active == True,
                    )
                )
            ).first()
            if rule and rule.rules_config:
                sla_days = rule.rules_config.get("credit_note_sla_days", 14)
            ret.credit_sla_deadline = now + timedelta(days=sla_days)

            # Generate notification and dispatch
            await cls._dispatch_notification(session, ret, sla_days)

        elif to_status == "REJECTED":
            # Revert batch statuses back to ACTIVE
            for item in ret.items:
                if item.batch:
                    item.batch.status = "ACTIVE"

        elif to_status == "SETTLED":
            # Mark batches as RETURNED
            for item in ret.items:
                if item.batch:
                    item.batch.status = "RETURNED"
                    item.batch.current_qty = max(0, item.batch.current_qty - item.requested_qty)

        # Audit event
        event = ReturnStatusEvent(
            id=str(uuid.uuid4()),
            tenant_id=ret.tenant_id,
            return_request_id=ret.id,
            from_status=from_status,
            to_status=to_status,
            trigger="USER",
            triggered_by=user_id,
            comment=comment or f"Transitioned to {to_status}",
        )
        session.add(event)
        await session.commit()
        return ret

    @classmethod
    async def bulk_approve(
        cls,
        session: AsyncSession,
        return_ids: List[str],
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[ReturnRequest]:
        """Bulk approve multiple draft return requests in one atomic transaction."""
        approved = []
        for rid in return_ids:
            try:
                res = await cls.transition_status(
                    session=session,
                    return_request_id=rid,
                    to_status="APPROVED",
                    user_id=user_id,
                    comment="Bulk approved by pharmacist",
                    tenant_id=tenant_id,
                )
                approved.append(res)
            except ValueError:
                continue
        return approved

    @classmethod
    async def _dispatch_notification(
        cls,
        session: AsyncSession,
        ret: ReturnRequest,
        sla_days: int,
    ) -> None:
        """Render templates and dispatch notification to distributor."""
        pharmacy_name = ret.tenant.name if ret.tenant else "ExpiryOS Pharmacy"
        distributor_name = ret.distributor.name if ret.distributor else "Distributor"
        recipient_phone = ret.distributor.phone if ret.distributor and ret.distributor.phone else "+919876543210"

        items_context = [
            {
                "product_name": item.batch.product.name if (item.batch and item.batch.product) else "Item",
                "batch_no": item.batch.batch_no if item.batch else "N/A",
                "expiry_date": str(item.batch.expiry_date) if item.batch else "N/A",
                "requested_qty": item.requested_qty,
                "unit_price": float(item.unit_purchase_price),
                "total_value": float(item.total_value),
            }
            for item in ret.items
        ]

        context = {
            "return_request_no": ret.return_request_no,
            "pharmacy_name": pharmacy_name,
            "distributor_name": distributor_name,
            "distributor_gstin": ret.distributor.gstin if ret.distributor else None,
            "distributor_phone": ret.distributor.phone if ret.distributor else None,
            "pharmacy_gstin": ret.tenant.gstin if ret.tenant else None,
            "date_str": date.today().strftime("%d %b %Y"),
            "item_count": ret.item_count,
            "total_value": float(ret.total_estimated_value),
            "credit_sla_days": sla_days,
            "status": ret.status,
            "items": items_context,
        }

        # Render WhatsApp summary
        msg_body = template_renderer.render_whatsapp_summary(context)

        # Dispatch via provider
        provider = get_notification_provider("whatsapp")
        msg = NotificationMessage(
            recipient=recipient_phone,
            subject=f"Return Dispatch - {ret.return_request_no}",
            body=msg_body,
            template_id="return_dispatch_v1",
        )
        resp = await provider.send_message(msg)

        # Audit in Notification table
        notification_rec = Notification(
            id=str(uuid.uuid4()),
            tenant_id=ret.tenant_id,
            channel="WHATSAPP",
            recipient=recipient_phone,
            template_id="return_dispatch_v1",
            status="SENT" if resp.success else "FAILED",
            payload=msg_body,
            sent_at=datetime.now(timezone.utc),
        )
        session.add(notification_rec)
