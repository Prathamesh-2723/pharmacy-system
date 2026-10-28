from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.rules_engine.types import BatchInput, RuleConfig
from app.rules_engine.evaluator import evaluate
from app.rules_engine.prioritizer import compute_urgency_bucket, compute_priority_score


@pytest.fixture
def base_rule() -> RuleConfig:
    return RuleConfig(
        return_window_start_days_before_expiry=90,
        return_window_end_days_before_expiry=15,
        excluded_categories=["Cold Chain", "Schedule X", "Breakage"],
        requires_prior_authorization=False,
        return_format="standard_v1",
        pickup_days=["Monday", "Thursday"],
        credit_note_sla_days=14,
        min_return_value=Decimal("500.00"),
        version=1,
    )


@pytest.fixture
def base_batch() -> BatchInput:
    # Expiry 45 days in future: right in the 90-15 day return window
    today = date(2026, 11, 1)
    expiry = today + timedelta(days=45)
    return BatchInput(
        id="batch-001",
        product_id="prod-001",
        product_name="Amoxicillin 500mg",
        category="Antibiotics",
        batch_no="AMX-2026-B1",
        expiry_date=expiry,
        current_qty=100,
        purchase_price=Decimal("15.50"),
        mrp=Decimal("22.00"),
        distributor_id="dist-001",
    )


class TestRulesEngineBoundaries:
    def test_eligible_inside_window(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        res = evaluate(base_batch, base_rule, today=today)

        assert res.eligible is True
        assert res.blocked_reason is None
        assert res.urgency_bucket == "60D"
        assert res.value_at_risk == Decimal("1550.00")
        assert res.priority_score > 0
        assert res.window_opens_on == base_batch.expiry_date - timedelta(days=90)
        assert res.window_closes_on == base_batch.expiry_date - timedelta(days=15)

    def test_exact_day_window_opens(self, base_rule):
        today = date(2026, 11, 1)
        expiry = today + timedelta(days=90)  # Exactly 90 days away
        batch = BatchInput(
            id="batch-exact-open",
            product_id="prod-001",
            product_name="Paracetamol",
            category="Analgesic",
            batch_no="PCM-90",
            expiry_date=expiry,
            current_qty=50,
            purchase_price=Decimal("20.00"),
        )
        res = evaluate(batch, base_rule, today=today)
        assert res.eligible is True
        assert res.days_to_window_close == 75
        assert res.blocked_reason is None

    def test_one_day_before_window_opens(self, base_rule):
        today = date(2026, 11, 1)
        expiry = today + timedelta(days=91)  # 91 days away, window starts at 90
        batch = BatchInput(
            id="batch-early",
            product_id="prod-001",
            product_name="Paracetamol",
            category="Analgesic",
            batch_no="PCM-91",
            expiry_date=expiry,
            current_qty=50,
            purchase_price=Decimal("20.00"),
        )
        res = evaluate(batch, base_rule, today=today)
        assert res.eligible is False
        assert "Return window has not opened yet" in res.blocked_reason
        assert res.priority_score == 0.0

    def test_exact_day_window_closes(self, base_rule):
        today = date(2026, 11, 1)
        expiry = today + timedelta(days=15)  # Exactly 15 days away (window closes at 15d)
        batch = BatchInput(
            id="batch-exact-close",
            product_id="prod-001",
            product_name="Paracetamol",
            category="Analgesic",
            batch_no="PCM-15",
            expiry_date=expiry,
            current_qty=50,
            purchase_price=Decimal("20.00"),
        )
        res = evaluate(batch, base_rule, today=today)
        assert res.eligible is True
        assert res.days_to_window_close == 0
        assert res.blocked_reason is None

    def test_one_day_after_window_closes(self, base_rule):
        today = date(2026, 11, 1)
        expiry = today + timedelta(days=14)  # 14 days away, window closed at 15d
        batch = BatchInput(
            id="batch-late",
            product_id="prod-001",
            product_name="Paracetamol",
            category="Analgesic",
            batch_no="PCM-14",
            expiry_date=expiry,
            current_qty=50,
            purchase_price=Decimal("20.00"),
        )
        res = evaluate(batch, base_rule, today=today)
        assert res.eligible is False
        assert "Return window closed on" in res.blocked_reason
        assert res.priority_score == 0.0


class TestRulesEngineExclusionsAndConstraints:
    def test_excluded_category_case_insensitive(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        # "Cold Chain" is in exclusions; test with lowercase
        cold_batch = BatchInput(
            id=base_batch.id,
            product_id=base_batch.product_id,
            product_name="Insulin Regular",
            category="cold chain",
            batch_no="INS-001",
            expiry_date=base_batch.expiry_date,
            current_qty=50,
            purchase_price=Decimal("150.00"),
        )
        res = evaluate(cold_batch, base_rule, today=today)
        assert res.eligible is False
        assert "Category 'cold chain' is explicitly excluded" in res.blocked_reason

    def test_zero_and_negative_quantity(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        zero_qty_batch = BatchInput(
            id=base_batch.id,
            product_id=base_batch.product_id,
            product_name=base_batch.product_name,
            category=base_batch.category,
            batch_no=base_batch.batch_no,
            expiry_date=base_batch.expiry_date,
            current_qty=0,
            purchase_price=base_batch.purchase_price,
        )
        res = evaluate(zero_qty_batch, base_rule, today=today)
        assert res.eligible is False
        assert "No stock available" in res.blocked_reason

    def test_already_expired_stock(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        expired_batch = BatchInput(
            id=base_batch.id,
            product_id=base_batch.product_id,
            product_name=base_batch.product_name,
            category=base_batch.category,
            batch_no=base_batch.batch_no,
            expiry_date=date(2026, 10, 15),  # in the past
            current_qty=20,
            purchase_price=Decimal("50.00"),
        )
        res = evaluate(expired_batch, base_rule, today=today)
        assert res.eligible is False
        assert "Stock has already expired" in res.blocked_reason

    def test_below_minimum_return_value(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        # min_return_value is 500.00, qty=5, price=20 -> total=100.00
        low_val_batch = BatchInput(
            id=base_batch.id,
            product_id=base_batch.product_id,
            product_name=base_batch.product_name,
            category=base_batch.category,
            batch_no=base_batch.batch_no,
            expiry_date=base_batch.expiry_date,
            current_qty=5,
            purchase_price=Decimal("20.00"),
        )
        res = evaluate(low_val_batch, base_rule, today=today)
        assert res.eligible is False
        assert "below minimum distributor threshold" in res.blocked_reason


class TestRuleVersioningAndPrioritization:
    def test_rule_version_not_yet_effective(self, base_batch, base_rule):
        today = date(2026, 11, 1)
        future_rule = RuleConfig(
            version=2,
            effective_from=date(2026, 12, 1),
            effective_to=date(2027, 12, 1),
        )
        res = evaluate(base_batch, future_rule, today=today)
        assert res.eligible is False
        assert "is not yet effective" in res.blocked_reason

    def test_rule_version_expired(self, base_batch):
        today = date(2026, 11, 1)
        past_rule = RuleConfig(
            version=1,
            effective_from=date(2025, 1, 1),
            effective_to=date(2026, 10, 31),
        )
        res = evaluate(base_batch, past_rule, today=today)
        assert res.eligible is False
        assert "has expired" in res.blocked_reason

    def test_urgency_buckets_and_priority_order(self, base_rule):
        today = date(2026, 11, 1)
        # Batch A: 20 days to expiry (close to window end of 15d -> 5 days to close)
        batch_urgent = BatchInput(
            id="urgent",
            product_id="prod-1",
            product_name="Medicine A",
            category="General",
            batch_no="B1",
            expiry_date=today + timedelta(days=20),
            current_qty=100,
            purchase_price=Decimal("100.00"),  # Value 10,000
        )
        # Batch B: 80 days to expiry (window closes in 65 days)
        batch_relaxed = BatchInput(
            id="relaxed",
            product_id="prod-2",
            product_name="Medicine B",
            category="General",
            batch_no="B2",
            expiry_date=today + timedelta(days=80),
            current_qty=100,
            purchase_price=Decimal("100.00"),  # Same value 10,000
        )

        res_urgent = evaluate(batch_urgent, base_rule, today=today)
        res_relaxed = evaluate(batch_relaxed, base_rule, today=today)

        assert res_urgent.eligible is True
        assert res_relaxed.eligible is True
        assert res_urgent.urgency_bucket == "30D"
        assert res_relaxed.urgency_bucket == "90D"
        # Urgent batch has significantly higher priority score because its return window is about to close
        assert res_urgent.priority_score > res_relaxed.priority_score
