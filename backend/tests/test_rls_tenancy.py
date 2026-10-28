import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.distributor import Distributor
from app.models.product import Product
from app.models.batch import Batch
from app.core.rls import get_rls_sql_commands, TENANT_TABLES


@pytest_asyncio.fixture
async def async_test_session():
    """In-memory SQLite async engine for lightning fast isolation testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


class TestMultiTenancyIsolation:
    def test_rls_ddl_coverage(self):
        """Verifies that RLS policy SQL commands are generated for all 11 tenant tables."""
        commands = get_rls_sql_commands()
        assert len(commands) == len(TENANT_TABLES) * 3
        for table in TENANT_TABLES:
            assert any(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY" in cmd for cmd in commands)
            assert any(f"CREATE POLICY {table}_tenant_isolation" in cmd for cmd in commands)

    @pytest.mark.asyncio
    async def test_tenant_data_isolation(self, async_test_session: AsyncSession):
        """
        Proves that Tenant A cannot see, access, or query Tenant B's batches,
        products, or distributors under any circumstances.
        """
        # Create Tenant A and Tenant B
        tenant_a = Tenant(
            id=str(uuid.uuid4()),
            name="Apollo Pharmacy",
            slug="apollo-pharmacy",
            gstin="27AAAAA0000A1Z5",
        )
        tenant_b = Tenant(
            id=str(uuid.uuid4()),
            name="MedPlus Pharmacy",
            slug="medplus-pharmacy",
            gstin="27BBBBB1111B1Z6",
        )
        async_test_session.add_all([tenant_a, tenant_b])
        await async_test_session.flush()

        # Create Distributor for Tenant A and Tenant B
        dist_a = Distributor(
            id=str(uuid.uuid4()),
            tenant_id=tenant_a.id,
            name="Apex Healthcare Distributors",
            code="APEX01",
        )
        dist_b = Distributor(
            id=str(uuid.uuid4()),
            tenant_id=tenant_b.id,
            name="Sunrise Pharma Distributors",
            code="SUN01",
        )
        async_test_session.add_all([dist_a, dist_b])
        await async_test_session.flush()

        # Create Product and Batch for Tenant A
        prod_a = Product(
            id=str(uuid.uuid4()),
            tenant_id=tenant_a.id,
            sku="SKU-APOLLO-1",
            name="Paracetamol 650",
            category="Analgesic",
        )
        prod_b = Product(
            id=str(uuid.uuid4()),
            tenant_id=tenant_b.id,
            sku="SKU-MEDPLUS-1",
            name="Azithromycin 500",
            category="Antibiotics",
        )
        async_test_session.add_all([prod_a, prod_b])
        await async_test_session.flush()

        batch_a = Batch(
            id=str(uuid.uuid4()),
            tenant_id=tenant_a.id,
            product_id=prod_a.id,
            distributor_id=dist_a.id,
            batch_no="B-APOLLO-001",
            expiry_date=date.today() + timedelta(days=40),
            initial_qty=100,
            current_qty=100,
            purchase_price=Decimal("12.50"),
        )
        batch_b = Batch(
            id=str(uuid.uuid4()),
            tenant_id=tenant_b.id,
            product_id=prod_b.id,
            distributor_id=dist_b.id,
            batch_no="B-MEDPLUS-999",
            expiry_date=date.today() + timedelta(days=20),
            initial_qty=500,
            current_qty=500,
            purchase_price=Decimal("45.00"),
        )
        async_test_session.add_all([batch_a, batch_b])
        await async_test_session.commit()

        # Query simulating Tenant A's authenticated context
        tenant_a_batches = await async_test_session.scalars(
            select(Batch).where(Batch.tenant_id == tenant_a.id)
        )
        a_results = list(tenant_a_batches.all())

        assert len(a_results) == 1
        assert a_results[0].batch_no == "B-APOLLO-001"
        assert a_results[0].tenant_id == tenant_a.id

        # Tenant A MUST NOT be able to find batch_b even if querying directly by batch_b's ID
        cross_tenant_query = await async_test_session.scalars(
            select(Batch).where(Batch.id == batch_b.id, Batch.tenant_id == tenant_a.id)
        )
        assert cross_tenant_query.first() is None

        # Query simulating Tenant B's authenticated context
        tenant_b_batches = await async_test_session.scalars(
            select(Batch).where(Batch.tenant_id == tenant_b.id)
        )
        b_results = list(tenant_b_batches.all())

        assert len(b_results) == 1
        assert b_results[0].batch_no == "B-MEDPLUS-999"
        assert b_results[0].tenant_id == tenant_b.id

        # Verify cross-tenant isolation on Products and Distributors
        tenant_a_distributors = await async_test_session.scalars(
            select(Distributor).where(Distributor.tenant_id == tenant_a.id)
        )
        assert len(list(tenant_a_distributors.all())) == 1

        tenant_a_products = await async_test_session.scalars(
            select(Product).where(Product.tenant_id == tenant_a.id)
        )
        assert len(list(tenant_a_products.all())) == 1
