import uuid
from datetime import date
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.models.tenant import Tenant
from app.models.batch import Batch
from app.models.distributor import Distributor
from app.models.product import Product
from app.services.ingestion_service import IngestionService, parse_date
from app.services.invoice_parser import StubInvoiceParser


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


class TestIngestionService:
    def test_date_parser_formats(self):
        # YYYY-MM-DD
        assert parse_date("2026-11-30") == date(2026, 11, 30)
        # DD/MM/YYYY
        assert parse_date("15/12/2026") == date(2026, 12, 15)
        # MM/YYYY (resolves to end of month)
        d = parse_date("04/2027")
        assert d == date(2027, 4, 30)
        # Invalid
        assert parse_date("invalid-date") is None

    @pytest.mark.asyncio
    async def test_successful_csv_import(self, async_test_session: AsyncSession, sample_tenant_id: str):
        # Create tenant
        tenant = Tenant(id=sample_tenant_id, name="Test Pharmacy", slug="test-pharmacy")
        async_test_session.add(tenant)
        await async_test_session.commit()

        csv_data = """item,batch_no,expiry,distributor,qty,price,invoice_no,category
Amoxicillin 500mg,AMX-001,2026-12-31,Sun Pharma Distributors,100,14.50,INV-1001,Antibiotics
Paracetamol 650mg,PCM-002,2027-01-15,Cipla Logistics,250,8.00,INV-1002,Analgesic
"""
        result = await IngestionService.process_csv(async_test_session, sample_tenant_id, csv_data)

        assert result.total_rows == 2
        assert result.imported_count == 2
        assert result.updated_count == 0
        assert len(result.errors) == 0

        # Verify batches in DB
        batches = await async_test_session.scalars(select(Batch).where(Batch.tenant_id == sample_tenant_id))
        batch_list = list(batches.all())
        assert len(batch_list) == 2
        assert {b.batch_no for b in batch_list} == {"AMX-001", "PCM-002"}

    @pytest.mark.asyncio
    async def test_idempotent_reimport(self, async_test_session: AsyncSession, sample_tenant_id: str):
        tenant = Tenant(id=sample_tenant_id, name="Test Pharmacy", slug="test-pharmacy")
        async_test_session.add(tenant)
        await async_test_session.commit()

        csv_data_v1 = """item,batch_no,expiry,distributor,qty,price,invoice_no
Azithromycin 500mg,AZI-500,2026-11-20,Apex Med,50,22.00,INV-2001
"""
        res1 = await IngestionService.process_csv(async_test_session, sample_tenant_id, csv_data_v1)
        assert res1.imported_count == 1
        assert res1.updated_count == 0

        # Re-import same batch with updated quantity & price (idempotency check)
        csv_data_v2 = """item,batch_no,expiry,distributor,qty,price,invoice_no
Azithromycin 500mg,AZI-500,2026-11-20,Apex Med,75,21.50,INV-2001
"""
        res2 = await IngestionService.process_csv(async_test_session, sample_tenant_id, csv_data_v2)
        assert res2.imported_count == 0
        assert res2.updated_count == 1

        # Must still only have 1 batch in the database, with updated qty 75
        batches = await async_test_session.scalars(select(Batch).where(Batch.tenant_id == sample_tenant_id))
        batch_list = list(batches.all())
        assert len(batch_list) == 1
        assert batch_list[0].current_qty == 75
        assert batch_list[0].purchase_price == Decimal("21.50")

    @pytest.mark.asyncio
    async def test_row_level_error_reporting(self, async_test_session: AsyncSession, sample_tenant_id: str):
        tenant = Tenant(id=sample_tenant_id, name="Test Pharmacy", slug="test-pharmacy")
        async_test_session.add(tenant)
        await async_test_session.commit()

        # Row 2 is valid, Row 3 has bad date, Row 4 has negative qty, Row 5 has invalid price
        csv_with_errors = """item,batch_no,expiry,distributor,qty,price,invoice_no
Valid Medicine,VAL-01,2026-12-31,Apex Med,10,15.00,INV-99
Bad Date Med,BAD-01,not-a-date,Apex Med,10,15.00,INV-99
Bad Qty Med,BAD-02,2026-12-31,Apex Med,-5,15.00,INV-99
Bad Price Med,BAD-03,2026-12-31,Apex Med,10,free_gift,INV-99
"""
        res = await IngestionService.process_csv(async_test_session, sample_tenant_id, csv_with_errors)

        assert res.total_rows == 4
        assert res.imported_count == 1  # Only the valid row is imported
        assert len(res.errors) == 3

        error_rows = [e.row for e in res.errors]
        assert error_rows == [3, 4, 5]
        assert "Invalid expiry date" in res.errors[0].error
        assert "Invalid quantity" in res.errors[1].error
        assert "Invalid purchase price" in res.errors[2].error


class TestInvoiceParserStub:
    @pytest.mark.asyncio
    async def test_stub_invoice_parser(self):
        parser = StubInvoiceParser()
        result = await parser.parse_invoice(file_stream=None, filename="sample_invoice.pdf")
        assert result.invoice_no.startswith("INV-OCR-")
        assert len(result.items) == 2
        assert result.items[0].confidence_score >= 0.95
        assert result.parser_model == "stub_layoutlm_v1"
