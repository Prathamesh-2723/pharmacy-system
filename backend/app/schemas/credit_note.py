from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ReconcileCreditNoteRequest(BaseModel):
    distributor_id: str
    return_request_id: Optional[str] = None
    credit_note_no: str = Field(..., min_length=2)
    credit_note_date: date
    credited_amount: Decimal = Field(..., gt=Decimal("0.00"))
    remarks: Optional[str] = None


class CreditNoteResponse(BaseModel):
    id: str
    distributor_id: str
    distributor_name: str
    return_request_id: Optional[str]
    return_request_no: Optional[str]
    credit_note_no: str
    credit_note_date: date
    expected_amount: float
    credited_amount: float
    shortfall_amount: float
    status: str
    remarks: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardKpiResponse(BaseModel):
    value_expiring_15d: float
    value_expiring_30d: float
    value_expiring_60d: float
    value_expiring_90d: float
    total_value_at_risk: float
    returns_pending_count: int
    returns_pending_value: float
    overdue_credits_count: int
    overdue_credits_value: float
    writeoffs_avoided_month: float
    reconciliation_accuracy_percent: float
