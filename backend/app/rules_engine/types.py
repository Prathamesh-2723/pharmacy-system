from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from decimal import Decimal


@dataclass(frozen=True)
class RuleConfig:
    """Configurable distributor return rule parameters."""
    return_window_start_days_before_expiry: int = 90  # Window opens X days before expiry
    return_window_end_days_before_expiry: int = 15    # Window closes Y days before expiry
    excluded_categories: List[str] = field(default_factory=list)
    requires_prior_authorization: bool = False
    return_format: str = "standard_v1"
    pickup_days: List[str] = field(default_factory=lambda: ["Monday", "Thursday"])
    credit_note_sla_days: int = 14
    min_return_value: Decimal = Decimal("0.00")
    version: int = 1
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


@dataclass(frozen=True)
class BatchInput:
    """Batch input data required for rule evaluation."""
    id: str
    product_id: str
    product_name: str
    category: str
    batch_no: str
    expiry_date: date
    current_qty: int
    purchase_price: Decimal
    mrp: Optional[Decimal] = None
    distributor_id: Optional[str] = None


@dataclass(frozen=True)
class EvaluationResult:
    """Evaluation result detailing return eligibility, windows, and priority score."""
    eligible: bool
    window_opens_on: date
    window_closes_on: date
    days_to_window_close: int
    days_to_expiry: int
    urgency_bucket: str  # "EXPIRED" | "15D" | "30D" | "60D" | "90D" | "FUTURE"
    blocked_reason: Optional[str] = None
    value_at_risk: Decimal = Decimal("0.00")
    priority_score: float = 0.0
    requires_prior_auth: bool = False
    return_format: str = "standard_v1"
