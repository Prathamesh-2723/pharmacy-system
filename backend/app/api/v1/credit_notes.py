from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.credit_note import CreditNote
from app.models.user import User
from app.schemas.credit_note import CreditNoteResponse, ReconcileCreditNoteRequest
from app.services.credit_service import CreditService

router = APIRouter(prefix="/credits", tags=["Credit Note Reconciliation"])


@router.get("", response_model=List[CreditNoteResponse])
async def list_credit_notes(
    distributor_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    query = (
        select(CreditNote)
        .options(selectinload(CreditNote.distributor), selectinload(CreditNote.return_request))
        .where(CreditNote.tenant_id == current_user.tenant_id)
        .order_by(CreditNote.created_at.desc())
    )
    if distributor_id:
        query = query.where(CreditNote.distributor_id == distributor_id)
    if status_filter:
        query = query.where(CreditNote.status == status_filter.upper())

    notes = (await session.scalars(query)).all()
    return [
        CreditNoteResponse(
            id=c.id,
            distributor_id=c.distributor_id,
            distributor_name=c.distributor.name if c.distributor else "Unknown",
            return_request_id=c.return_request_id,
            return_request_no=c.return_request.return_request_no if c.return_request else None,
            credit_note_no=c.credit_note_no,
            credit_note_date=c.credit_note_date,
            expected_amount=float(c.expected_amount),
            credited_amount=float(c.credited_amount),
            shortfall_amount=float(c.shortfall_amount),
            status=c.status,
            remarks=c.remarks,
            created_at=c.created_at,
        )
        for c in notes
    ]


@router.post("/reconcile", response_model=CreditNoteResponse, status_code=status.HTTP_201_CREATED)
async def reconcile_credit_note(
    body: ReconcileCreditNoteRequest,
    current_user: User = Depends(require_roles(["owner", "pharmacist"])),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        cn = await CreditService.reconcile_credit_note(
            session=session,
            tenant_id=current_user.tenant_id,
            distributor_id=body.distributor_id,
            credit_note_no=body.credit_note_no,
            credit_note_date=body.credit_note_date,
            credited_amount=body.credited_amount,
            return_request_id=body.return_request_id,
            remarks=body.remarks,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    reloaded = (
        await session.scalars(
            select(CreditNote)
            .options(selectinload(CreditNote.distributor), selectinload(CreditNote.return_request))
            .where(CreditNote.id == cn.id)
        )
    ).first()

    return CreditNoteResponse(
        id=reloaded.id,
        distributor_id=reloaded.distributor_id,
        distributor_name=reloaded.distributor.name if reloaded.distributor else "Unknown",
        return_request_id=reloaded.return_request_id,
        return_request_no=reloaded.return_request.return_request_no if reloaded.return_request else None,
        credit_note_no=reloaded.credit_note_no,
        credit_note_date=reloaded.credit_note_date,
        expected_amount=float(reloaded.expected_amount),
        credited_amount=float(reloaded.credited_amount),
        shortfall_amount=float(reloaded.shortfall_amount),
        status=reloaded.status,
        remarks=reloaded.remarks,
        created_at=reloaded.created_at,
    )
