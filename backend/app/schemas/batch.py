from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class ManualBatchCreate(BaseModel):
    product_name: str = Field(..., min_length=2)
    category: str = Field(default="General")
    distributor_id: str
    batch_no: str = Field(..., min_length=1)
    expiry_date: date
    qty: int = Field(..., gt=0)
    purchase_price: Decimal = Field(..., gt=Decimal("0.00"))
    mrp: Optional[Decimal] = None
    invoice_ref: Optional[str] = None


class BatchDetailResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    category: str
    distributor_id: str
    distributor_name: str
    batch_no: str
    expiry_date: date
    initial_qty: int
    current_qty: int
    purchase_price: float
    mrp: Optional[float]
    invoice_ref: Optional[str]
    status: str
    value_at_risk: float
    urgency_bucket: str
    eligible: bool
    window_opens_on: str
    window_closes_on: str
    days_to_window_close: int
    days_to_expiry: int
    blocked_reason: Optional[str]
    priority_score: float
    window_closing_soon: bool

    class Config:
        from_attributes = True
