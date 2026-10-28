import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.models.tenant import Tenant
from app.models.distributor import Distributor, DistributorRule
from app.models.product import Product
from app.models.batch import Batch
from app.models.return_request import ReturnRequest, ReturnStatusEvent
from app.services.return_service import ReturnService
from app.services.credit_service import CreditService
from app.services.template_service import template_renderer


@pytest_asyncio.fixture
async def async_test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_tenant_id():
    return str(uuid.uuid4())


class TestReturnLifecycleAndReconciliation:
    @pytest.mark.asyncio
    async def test_auto_generate_draft_returns(self, async_test_session: AsyncSession, sample_tenant_id: str):
        # Setup tenant
        tenant = Tenant(id=sample_tenant_id, name="MedLife Pharmacy", slug="medlife")
        async_test_session.add(tenant)
        await async_test_session.flush()

        # Setup distributor with rule (window 90 to 15 days)
        dist = Distributor(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            name="Apex Healthcare Ltd",
            phone="+919876543210",
        )
        async_test_session.add(dist)
        await async_test_session.flush()

        rule = DistributorRule(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            distributor_id=dist.id,
            version=1,
            rules_config={
                "return_window_start_days_before_expiry": 90,
                "return_window_end_days_before_expiry": 15,
                "excluded_categories": [],
                "credit_note_sla_days": 10,
                "min_return_value": "0.00",
            },
        )
        async_test_session.add(rule)

        # Batch 1: 40 days to expiry (ELIGIBLE)
        prod1 = Product(id=str(uuid.uuid4()), tenant_id=sample_tenant_id, sku="P1", name="Amox 500")
        async_test_session.add(prod1)
        await async_test_session.flush()

        b1 = Batch(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            product_id=prod1.id,
            distributor_id=dist.id,
            batch_no="AMX-40D",
            expiry_date=date.today() + timedelta(days=40),
            current_qty=100,
            purchase_price=Decimal("10.00"),
            status="ACTIVE",
        )
        # Batch 2: 120 days to expiry (NOT ELIGIBLE, window opens at 90d)
        prod2 = Product(id=str(uuid.uuid4()), tenant_id=sample_tenant_id, sku="P2", name="Vitamin C")
        async_test_session.add(prod2)
        await async_test_session.flush()

        b2 = Batch(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            product_id=prod2.id,
            distributor_id=dist.id,
            batch_no="VIT-120D",
            expiry_date=date.today() + timedelta(days=120),
            current_qty=50,
            purchase_price=Decimal("5.00"),
            status="ACTIVE",
        )
        async_test_session.add_all([b1, b2])
        await async_test_session.commit()

        # Run auto-generate
        drafts = await ReturnService.auto_generate_draft_returns(
            async_test_session, sample_tenant_id, today=date.today()
        )

        assert len(drafts) == 1
        d = drafts[0]
        assert d.status == "DRAFT"
        assert d.item_count == 1
        assert d.total_estimated_value == Decimal("1000.00")
        assert d.distributor_id == dist.id

        # Verify b1 marked RETURNING
        updated_b1 = await async_test_session.get(Batch, b1.id)
        assert updated_b1.status == "RETURNING"

    @pytest.mark.asyncio
    async def test_lifecycle_state_machine_and_bulk_approve(
        self, async_test_session: AsyncSession, sample_tenant_id: str
    ):
        tenant = Tenant(id=sample_tenant_id, name="MedLife Pharmacy", slug="medlife2")
        dist = Distributor(id=str(uuid.uuid4()), tenant_id=sample_tenant_id, name="Sun Pharma")
        async_test_session.add_all([tenant, dist])
        await async_test_session.flush()

        ret = ReturnRequest(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            distributor_id=dist.id,
            return_request_no="RET-TEST-001",
            status="DRAFT",
            total_estimated_value=Decimal("5000.00"),
            item_count=5,
        )
        async_test_session.add(ret)
        await async_test_session.commit()

        # Invalid transition: DRAFT cannot skip directly to SETTLED
        with pytest.raises(ValueError, match="Invalid transition"):
            await ReturnService.transition_status(
                async_test_session, ret.id, to_status="SETTLED", tenant_id=sample_tenant_id
            )

        # Bulk approve (DRAFT -> APPROVED)
        approved = await ReturnService.bulk_approve(
            async_test_session, [ret.id], tenant_id=sample_tenant_id
        )
        assert len(approved) == 1
        assert approved[0].status == "APPROVED"
        assert approved[0].approved_at is not None

        # Transition APPROVED -> SENT (dispatches notification)
        sent_ret = await ReturnService.transition_status(
            async_test_session, ret.id, to_status="SENT", tenant_id=sample_tenant_id
        )
        assert sent_ret.status == "SENT"
        assert sent_ret.dispatched_at is not None
        assert sent_ret.credit_sla_deadline is not None

        # Verify status events logged
        events = (
            await async_test_session.scalars(
                select(ReturnStatusEvent).where(ReturnStatusEvent.return_request_id == ret.id)
            )
        ).all()
        to_statuses = [e.to_status for e in events]
        assert "APPROVED" in to_statuses
        assert "SENT" in to_statuses

    @pytest.mark.asyncio
    async def test_credit_note_reconciliation_shortfall(
        self, async_test_session: AsyncSession, sample_tenant_id: str
    ):
        tenant = Tenant(id=sample_tenant_id, name="MedLife Pharmacy", slug="medlife3")
        dist = Distributor(id=str(uuid.uuid4()), tenant_id=sample_tenant_id, name="Cipla")
        async_test_session.add_all([tenant, dist])
        await async_test_session.flush()

        ret = ReturnRequest(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant_id,
            distributor_id=dist.id,
            return_request_no="RET-TEST-002",
            status="PICKED_UP",
            total_estimated_value=Decimal("10000.00"),
            total_credit_received=Decimal("0.00"),
            item_count=10,
        )
        async_test_session.add(ret)
        await async_test_session.commit()

        # Reconcile partial credit note: distributor credited 8,500 instead of 10,000
        cn = await CreditService.reconcile_credit_note(
            session=async_test_session,
            tenant_id=sample_tenant_id,
            distributor_id=dist.id,
            return_request_id=ret.id,
            credit_note_no="CN-CIPLA-8821",
            credit_note_date=date.today(),
            credited_amount=Decimal("8500.00"),
            remarks="Distributor deducted 15% handling charges",
        )

        assert cn.expected_amount == Decimal("10000.00")
        assert cn.credited_amount == Decimal("8500.00")
        assert cn.shortfall_amount == Decimal("1500.00")
        assert cn.status == "PARTIAL"

        # Check that return request received credit and advanced to CREDIT_ISSUED
        updated_ret = await async_test_session.get(ReturnRequest, ret.id)
        assert updated_ret.status == "CREDIT_ISSUED"
        assert updated_ret.total_credit_received == Decimal("8500.00")

    def test_template_rendering(self):
        context = {
            "return_request_no": "RET-2026-001",
            "pharmacy_name": "Apollo Care",
            "distributor_name": "Sun Pharma Logistics",
            "distributor_gstin": "27ABCDE1234F1Z5",
            "distributor_phone": "+919876543210",
            "pharmacy_gstin": "27XYZ1234F1Z1",
            "date_str": "28 Oct 2026",
            "item_count": 2,
            "total_value": 3500.00,
            "credit_sla_days": 14,
            "status": "APPROVED",
            "items": [
                {
                    "product_name": "Paracetamol 650",
                    "batch_no": "PCM-01",
                    "expiry_date": "2026-12-01",
                    "requested_qty": 100,
                    "unit_price": 15.00,
                    "total_value": 1500.00,
                },
                {
                    "product_name": "Ceftriaxone 1g",
                    "batch_no": "CEF-02",
                    "expiry_date": "2026-11-20",
                    "requested_qty": 20,
                    "unit_price": 100.00,
                    "total_value": 2000.00,
                },
            ],
        }
        wa_text = template_renderer.render_whatsapp_summary(context)
        assert "RET-2026-001" in wa_text
        assert "Paracetamol 650" in wa_text
        assert "*Credit SLA:* 14 days" in wa_text

        html_slip = template_renderer.render_html_slip(context)
        assert "<title>Return Request Slip - RET-2026-001</title>" in html_slip
        assert "Total Estimated Credit Value: ₹3500.00" in html_slip
