from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.rules_engine.types import BatchInput, RuleConfig, EvaluationResult
from app.rules_engine.prioritizer import compute_urgency_bucket, compute_priority_score


def evaluate(batch: BatchInput, rule: RuleConfig, today: Optional[date] = None) -> EvaluationResult:
    """
    Pure, side-effect-free evaluation of a batch against a distributor's return rule.
    
    Returns an EvaluationResult containing eligibility status, open/close dates,
    urgency classification, financial value at risk, and priority score.
    """
    if today is None:
        today = date.today()

    # Calculate return window dates relative to batch expiry
    window_opens_on = batch.expiry_date - timedelta(days=rule.return_window_start_days_before_expiry)
    window_closes_on = batch.expiry_date - timedelta(days=rule.return_window_end_days_before_expiry)

    days_to_expiry = (batch.expiry_date - today).days
    days_to_window_close = (window_closes_on - today).days
    days_to_window_open = (window_opens_on - today).days

    urgency_bucket, _ = compute_urgency_bucket(days_to_expiry)
    value_at_risk = Decimal(str(batch.current_qty)) * batch.purchase_price

    blocked_reason: Optional[str] = None
    eligible = True

    # 1. Zero or negative quantity check
    if batch.current_qty <= 0:
        eligible = False
        blocked_reason = "No stock available (current quantity is 0)"

    # 2. Rule version effective date checks
    elif rule.effective_from and today < rule.effective_from:
        eligible = False
        blocked_reason = f"Rule version {rule.version} is not yet effective (effective from {rule.effective_from})"

    elif rule.effective_to and today > rule.effective_to:
        eligible = False
        blocked_reason = f"Rule version {rule.version} has expired (effective until {rule.effective_to})"

    # 3. Already expired check
    elif days_to_expiry <= 0:
        eligible = False
        blocked_reason = "Stock has already expired; distributor return policy does not accept post-expiry returns"

    # 4. Excluded category check (case-insensitive)
    elif any(exc.strip().lower() == batch.category.strip().lower() for exc in rule.excluded_categories):
        eligible = False
        blocked_reason = f"Category '{batch.category}' is explicitly excluded by distributor return policy"

    # 5. Window boundary checks
    elif today < window_opens_on:
        eligible = False
        blocked_reason = (
            f"Return window has not opened yet (opens on {window_opens_on}, in {days_to_window_open} days)"
        )

    elif today > window_closes_on:
        eligible = False
        days_past = -days_to_window_close
        blocked_reason = (
            f"Return window closed on {window_closes_on} ({days_past} day{'s' if days_past != 1 else ''} ago)"
        )

    # 6. Minimum return value threshold
    elif value_at_risk < rule.min_return_value:
        eligible = False
        blocked_reason = (
            f"Estimated return value ₹{value_at_risk:.2f} is below minimum distributor threshold ₹{rule.min_return_value:.2f}"
        )

    # Calculate risk priority score
    priority_score = compute_priority_score(
        value_at_risk=value_at_risk,
        days_to_expiry=days_to_expiry,
        days_to_window_close=days_to_window_close,
        is_eligible=eligible
    )

    return EvaluationResult(
        eligible=eligible,
        window_opens_on=window_opens_on,
        window_closes_on=window_closes_on,
        days_to_window_close=days_to_window_close,
        days_to_expiry=days_to_expiry,
        urgency_bucket=urgency_bucket,
        blocked_reason=blocked_reason,
        value_at_risk=value_at_risk,
        priority_score=priority_score,
        requires_prior_auth=rule.requires_prior_authorization,
        return_format=rule.return_format
    )
