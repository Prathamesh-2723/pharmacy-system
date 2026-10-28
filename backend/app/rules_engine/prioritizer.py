from datetime import date
from decimal import Decimal
from typing import Tuple


def compute_urgency_bucket(days_to_expiry: int) -> Tuple[str, float]:
    """
    Computes standard urgency bucket and corresponding multiplier.
    Returns (bucket_name, urgency_weight).
    """
    if days_to_expiry <= 0:
        return "EXPIRED", 5.0
    elif days_to_expiry <= 15:
        return "15D", 4.0
    elif days_to_expiry <= 30:
        return "30D", 3.0
    elif days_to_expiry <= 60:
        return "60D", 2.0
    elif days_to_expiry <= 90:
        return "90D", 1.0
    else:
        return "FUTURE", 0.5


def compute_priority_score(
    value_at_risk: Decimal,
    days_to_expiry: int,
    days_to_window_close: int,
    is_eligible: bool
) -> float:
    """
    Computes priority score = value_at_risk * urgency_weight * window_urgency_factor.
    
    Higher score indicates higher financial risk requiring immediate action before
    the distributor's return window permanently lapses.
    """
    if not is_eligible or value_at_risk <= Decimal("0.00"):
        return 0.0

    _, urgency_weight = compute_urgency_bucket(days_to_expiry)
    val = float(value_at_risk)

    # Window urgency factor: Batches with very few days left in the return window
    # have critical time sensitivity.
    # When days_to_window_close is 1 day, window factor is highest (~10.0).
    # When days_to_window_close is 60 days, window factor is lower (~1.5).
    effective_days = max(1, days_to_window_close)
    window_factor = max(1.0, 30.0 / (effective_days + 2))

    score = round(val * urgency_weight * window_factor, 2)
    return score
