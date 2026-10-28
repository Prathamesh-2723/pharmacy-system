from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleConfigSchema(BaseModel):
    return_window_start_days_before_expiry: int = Field(default=90, ge=1, le=365)
    return_window_end_days_before_expiry: int = Field(default=15, ge=0, le=180)
    excluded_categories: List[str] = Field(default_factory=list)
    requires_prior_authorization: bool = False
    return_format: str = "standard_v1"
    pickup_days: List[str] = Field(default_factory=lambda: ["Monday", "Thursday"])
    credit_note_sla_days: int = Field(default=14, ge=1, le=120)
    min_return_value: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class DistributorRuleCreate(BaseModel):
    rules_config: RuleConfigSchema
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class DistributorRuleResponse(BaseModel):
    id: str
    version: int
    effective_from: Optional[date]
    effective_to: Optional[date]
    rules_config: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


class DistributorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    rule: Optional[RuleConfigSchema] = None


class DistributorScorecard(BaseModel):
    id: str
    name: str
    code: Optional[str]
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: bool
    active_rule: Optional[Dict[str, Any]]
    active_returns_count: int = 0
    total_returned_value: float = 0.0
    avg_credit_turnaround_days: float = 0.0
    rejection_rate_percent: float = 0.0

    class Config:
        from_attributes = True
