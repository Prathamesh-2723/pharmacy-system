from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReturnRequestItemResponse(BaseModel):
    id: str
    batch_id: str
    product_name: str
    category: str
    batch_no: str
    expiry_date: str
    requested_qty: int
    accepted_qty: Optional[int]
    unit_purchase_price: float
    total_value: float
    reason: str

    class Config:
        from_attributes = True


class ReturnStatusEventResponse(BaseModel):
    id: str
    from_status: Optional[str]
    to_status: str
    trigger: str
    triggered_by: Optional[str]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReturnRequestResponse(BaseModel):
    id: str
    return_request_no: str
    distributor_id: str
    distributor_name: str
    distributor_phone: Optional[str]
    status: str
    total_estimated_value: float
    total_credit_received: float
    item_count: int
    approved_at: Optional[datetime]
    dispatched_at: Optional[datetime]
    credit_sla_deadline: Optional[datetime]
    created_at: datetime
    items: List[ReturnRequestItemResponse] = []
    events: List[ReturnStatusEventResponse] = []

    class Config:
        from_attributes = True


class TransitionStatusRequest(BaseModel):
    to_status: str = Field(..., description="Target lifecycle state")
    comment: Optional[str] = None


class BulkApproveRequest(BaseModel):
    return_request_ids: List[str]


class RenderSlipResponse(BaseModel):
    html_slip: str
    whatsapp_summary: str
    whatsapp_share_url: str
