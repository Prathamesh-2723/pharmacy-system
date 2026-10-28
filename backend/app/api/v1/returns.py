import urllib.parse
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.distributor import DistributorRule
from app.models.batch import Batch
from app.models.return_request import ReturnRequest, ReturnRequestItem, ReturnStatusEvent
from app.models.user import User
from app.schemas.return_request import (
    BulkApproveRequest,
    RenderSlipResponse,
    ReturnRequestItemResponse,
    ReturnRequestResponse,
    ReturnStatusEventResponse,
    TransitionStatusRequest,
)
from app.services.return_service import ReturnService
from app.services.template_service import template_renderer

router = APIRouter(prefix="/returns", tags=["Return Requests Workflow"])


def _format_return_response(r: ReturnRequest) -> ReturnRequestResponse:
    return ReturnRequestResponse(
        id=r.id,
        return_request_no=r.return_request_no,
        distributor_id=r.distributor_id,
        distributor_name=r.distributor.name if r.distributor else "Unknown",
        distributor_phone=r.distributor.phone if r.distributor else None,
        status=r.status,
        total_estimated_value=float(r.total_estimated_value),
        total_credit_received=float(r.total_credit_received),
        item_count=r.item_count,
        approved_at=r.approved_at,
        dispatched_at=r.dispatched_at,
        credit_sla_deadline=r.credit_sla_deadline,
        created_at=r.created_at,
        items=[
            ReturnRequestItemResponse(
                id=item.id,
                batch_id=item.batch_id,
                product_name=item.batch.product.name if item.batch and item.batch.product else "Medicine",
                category=item.batch.product.category if item.batch and item.batch.product else "General",
                batch_no=item.batch.batch_no if item.batch else "N/A",
                expiry_date=str(item.batch.expiry_date) if item.batch else "N/A",
                requested_qty=item.requested_qty,
                accepted_qty=item.accepted_qty,
                unit_purchase_price=float(item.unit_purchase_price),
                total_value=float(item.total_value),
                reason=item.reason,
            )
            for item in r.items
        ],
        events=[
            ReturnStatusEventResponse(
                id=ev.id,
                from_status=ev.from_status,
                to_status=ev.to_status,
                trigger=ev.trigger,
                triggered_by=ev.triggered_by,
                comment=ev.comment,
                created_at=ev.created_at,
            )
            for ev in r.events
        ],
    )


@router.post("/auto-generate", response_model=List[ReturnRequestResponse])
async def auto_generate_returns(
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    drafts = await ReturnService.auto_generate_draft_returns(
        session=session,
        tenant_id=current_user.tenant_id,
        today=date.today(),
    )
    # Reload with relationships
    return_ids = [d.id for d in drafts]
    if not return_ids:
        return []

    reloaded = (
        await session.scalars(
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items)
                .selectinload(ReturnRequestItem.batch)
                .selectinload(Batch.product),
                selectinload(ReturnRequest.events),
            )
            .where(ReturnRequest.id.in_(return_ids))
        )
    ).all()
    return [_format_return_response(r) for r in reloaded]


@router.get("", response_model=List[ReturnRequestResponse])
async def list_returns(
    status_filter: Optional[str] = Query(None, alias="status"),
    distributor_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(ReturnRequest)
        .options(
            selectinload(ReturnRequest.distributor),
            selectinload(ReturnRequest.items)
            .selectinload(ReturnRequestItem.batch)
            .selectinload(Batch.product),
            selectinload(ReturnRequest.events),
        )
        .where(ReturnRequest.tenant_id == current_user.tenant_id)
        .order_by(ReturnRequest.created_at.desc())
    )
    if status_filter:
        query = query.where(ReturnRequest.status == status_filter.upper())
    if distributor_id:
        query = query.where(ReturnRequest.distributor_id == distributor_id)

    results = (await session.scalars(query)).all()
    return [_format_return_response(r) for r in results]


@router.get("/{id}", response_model=ReturnRequestResponse)
async def get_return_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    ret = (
        await session.scalars(
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items)
                .selectinload(ReturnRequestItem.batch)
                .selectinload(Batch.product),
                selectinload(ReturnRequest.events),
            )
            .where(ReturnRequest.id == id, ReturnRequest.tenant_id == current_user.tenant_id)
        )
    ).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")
    return _format_return_response(ret)


@router.post("/{id}/transition", response_model=ReturnRequestResponse)
async def transition_return(
    id: str,
    body: TransitionStatusRequest,
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        updated = await ReturnService.transition_status(
            session=session,
            return_request_id=id,
            to_status=body.to_status.upper(),
            user_id=current_user.id,
            comment=body.comment,
            tenant_id=current_user.tenant_id,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    # Reload with relationships
    reloaded = (
        await session.scalars(
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items)
                .selectinload(ReturnRequestItem.batch)
                .selectinload(Batch.product),
                selectinload(ReturnRequest.events),
            )
            .where(ReturnRequest.id == id)
        )
    ).first()
    return _format_return_response(reloaded)


@router.post("/bulk-approve", response_model=List[ReturnRequestResponse])
async def bulk_approve_returns(
    body: BulkApproveRequest,
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    approved_list = await ReturnService.bulk_approve(
        session=session,
        return_ids=body.return_request_ids,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )
    if not approved_list:
        return []

    reloaded = (
        await session.scalars(
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items)
                .selectinload(ReturnRequestItem.batch)
                .selectinload(Batch.product),
                selectinload(ReturnRequest.events),
            )
            .where(ReturnRequest.id.in_([a.id for a in approved_list]))
        )
    ).all()
    return [_format_return_response(r) for r in reloaded]


@router.get("/{id}/render", response_model=RenderSlipResponse)
async def render_return_dispatch_slip(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    ret = (
        await session.scalars(
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.distributor),
                selectinload(ReturnRequest.items)
                .selectinload(ReturnRequestItem.batch)
                .selectinload(Batch.product),
                selectinload(ReturnRequest.tenant),
            )
            .where(ReturnRequest.id == id, ReturnRequest.tenant_id == current_user.tenant_id)
        )
    ).first()
    if not ret:
        raise HTTPException(status_code=404, detail="Return request not found")

    # Fetch SLA days
    rule = (
        await session.scalars(
            select(DistributorRule).where(
                DistributorRule.distributor_id == ret.distributor_id,
                DistributorRule.is_active == True,
            )
        )
    ).first()
    sla_days = rule.rules_config.get("credit_note_sla_days", 14) if rule and rule.rules_config else 14

    items_context = [
        {
            "product_name": item.batch.product.name if item.batch and item.batch.product else "Item",
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
        "pharmacy_name": ret.tenant.name if ret.tenant else "Pharmacy",
        "pharmacy_gstin": ret.tenant.gstin if ret.tenant else None,
        "distributor_name": ret.distributor.name if ret.distributor else "Distributor",
        "distributor_gstin": ret.distributor.gstin if ret.distributor else None,
        "distributor_phone": ret.distributor.phone if ret.distributor else None,
        "date_str": date.today().strftime("%d %b %Y"),
        "item_count": ret.item_count,
        "total_value": float(ret.total_estimated_value),
        "credit_sla_days": sla_days,
        "status": ret.status,
        "items": items_context,
    }

    html_slip = template_renderer.render_html_slip(context)
    whatsapp_summary = template_renderer.render_whatsapp_summary(context)
    phone_clean = ret.distributor.phone.replace("+", "").replace("-", "").replace(" ", "") if ret.distributor and ret.distributor.phone else ""
    share_url = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(whatsapp_summary)}"

    return RenderSlipResponse(
        html_slip=html_slip,
        whatsapp_summary=whatsapp_summary,
        whatsapp_share_url=share_url,
    )
