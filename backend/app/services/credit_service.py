import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.credit_note import CreditNote
from app.models.return_request import ReturnRequest, ReturnStatusEvent


class CreditService:
    @classmethod
    async def reconcile_credit_note(
        cls,
        session: AsyncSession,
        tenant_id: str,
        distributor_id: str,
        credit_note_no: str,
        credit_note_date: date,
        credited_amount: Decimal,
        return_request_id: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> CreditNote:
        """
        Reconciles distributor credit note against expected return value,
        calculates shortfall, and transitions return request status.
        """
        expected_amount = Decimal("0.00")
        return_req: Optional[ReturnRequest] = None

        if return_request_id:
            return_req = (
                await session.scalars(
                    select(ReturnRequest)
                    .options(selectinload(ReturnRequest.items))
                    .where(
                        ReturnRequest.id == return_request_id,
                        ReturnRequest.tenant_id == tenant_id,
                    )
                )
            ).first()

            if return_req:
                expected_amount = return_req.total_estimated_value

        shortfall = max(Decimal("0.00"), expected_amount - credited_amount)

        if shortfall == Decimal("0.00") and expected_amount > Decimal("0.00"):
            status = "MATCHED"
        elif credited_amount > Decimal("0.00"):
            status = "PARTIAL"
        else:
            status = "DISPUTED"

        credit_note = CreditNote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            distributor_id=distributor_id,
            return_request_id=return_request_id,
            credit_note_no=credit_note_no,
            credit_note_date=credit_note_date,
            expected_amount=expected_amount,
            credited_amount=credited_amount,
            shortfall_amount=shortfall,
            status=status,
            remarks=remarks,
        )
        session.add(credit_note)

        # Update return request if matched
        if return_req:
            return_req.total_credit_received += credited_amount

            # Status transition based on settlement
            new_status = "SETTLED" if return_req.total_credit_received >= return_req.total_estimated_value else "CREDIT_ISSUED"
            from_status = return_req.status
            return_req.status = new_status

            event = ReturnStatusEvent(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                return_request_id=return_req.id,
                from_status=from_status,
                to_status=new_status,
                trigger="CREDIT_RECONCILIATION",
                comment=f"Credit note {credit_note_no} matched. Credited: ₹{credited_amount:.2f}, Shortfall: ₹{shortfall:.2f}.",
                metadata_json={
                    "credit_note_no": credit_note_no,
                    "credited_amount": str(credited_amount),
                    "shortfall": str(shortfall),
                },
            )
            session.add(event)

        await session.commit()
        return credit_note
