import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import hash_password, create_access_token
from app.db.session import get_db, async_session_factory


@pytest_asyncio.fixture
async def setup_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    # Create tenant and user
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    async with session_maker() as session:
        t = Tenant(id=tenant_id, name="Apollo Pharmacy", slug="apollo-test")
        u = User(
            id=user_id,
            tenant_id=tenant_id,
            email="owner@apollo.com",
            hashed_password=hash_password("Password123!"),
            full_name="Dr. Prathamesh Pharmacist",
            role="owner",
            is_active=True,
        )
        session.add_all([t, u])
        await session.commit()

    token = create_access_token(subject=user_id, tenant_id=tenant_id, role="owner")
    
    # Override FastAPI get_db dependency
    async def override_get_db():
        async with session_maker() as s:
            yield s

    from app.api.deps import get_db_session
    app.dependency_overrides[get_db_session] = override_get_db

    yield {"token": token, "tenant_id": tenant_id, "user_id": user_id}

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_api_full_happy_path(setup_test_db):
    token = setup_test_db["token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Login verification
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "owner@apollo.com", "password": "Password123!"},
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

        # 3. Create Distributor
        dist_res = await client.post(
            "/api/v1/distributors",
            headers=headers,
            json={
                "name": "Sun Pharma Logistics",
                "phone": "+919876543210",
                "email": "returns@sunpharma.com",
                "rule": {
                    "return_window_start_days_before_expiry": 90,
                    "return_window_end_days_before_expiry": 15,
                    "excluded_categories": ["Cold Chain"],
                    "credit_note_sla_days": 14,
                    "min_return_value": 0.0,
                },
            },
        )
        assert dist_res.status_code == 201
        dist_id = dist_res.json()["id"]

        # 4. Create Manual Batch inside return window (expiry in 35 days)
        expiry_in_35d = str(date.today() + timedelta(days=35))
        batch_res = await client.post(
            "/api/v1/batches/manual",
            headers=headers,
            json={
                "product_name": "Rosuvastatin 10mg",
                "category": "Cardiovascular",
                "distributor_id": dist_id,
                "batch_no": "ROSU-2026-01",
                "expiry_date": expiry_in_35d,
                "qty": 100,
                "purchase_price": 45.0,
            },
        )
        assert batch_res.status_code == 201
        b_data = batch_res.json()
        assert b_data["eligible"] is True
        assert b_data["urgency_bucket"] == "60D"
        assert b_data["value_at_risk"] == 4500.0

        # 5. Auto-Generate Draft Return
        auto_res = await client.post("/api/v1/returns/auto-generate", headers=headers)
        assert auto_res.status_code == 200
        returns_list = auto_res.json()
        assert len(returns_list) >= 1
        ret_id = returns_list[0]["id"]
        assert returns_list[0]["status"] == "DRAFT"

        # 6. Pharmacist 1-click Approve
        approve_res = await client.post(
            f"/api/v1/returns/{ret_id}/transition",
            headers=headers,
            json={"to_status": "APPROVED", "comment": "Approved for distributor pickup"},
        )
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "APPROVED"

        # 7. Transition to SENT (triggers dispatch notification)
        sent_res = await client.post(
            f"/api/v1/returns/{ret_id}/transition",
            headers=headers,
            json={"to_status": "SENT", "comment": "Dispatched to driver"},
        )
        assert sent_res.status_code == 200
        assert sent_res.json()["status"] == "SENT"

        # 8. Render Dispatch Slip & WhatsApp Share Link
        render_res = await client.get(f"/api/v1/returns/{ret_id}/render", headers=headers)
        assert render_res.status_code == 200
        render_data = render_res.json()
        assert "Rosuvastatin 10mg" in render_data["html_slip"]
        assert "wa.me" in render_data["whatsapp_share_url"]

        # 9. Reconcile Credit Note
        credit_res = await client.post(
            "/api/v1/credits/reconcile",
            headers=headers,
            json={
                "distributor_id": dist_id,
                "return_request_id": ret_id,
                "credit_note_no": "CN-SUN-9901",
                "credit_note_date": str(date.today()),
                "credited_amount": 4500.0,
                "remarks": "100% full credit accepted",
            },
        )
        assert credit_res.status_code == 201
        credit_data = credit_res.json()
        assert credit_data["status"] == "MATCHED"
        assert credit_data["shortfall_amount"] == 0.0

        # 10. Verify Dashboard KPIs reflect saved losses
        kpi_res = await client.get("/api/v1/dashboard/kpis", headers=headers)
        assert kpi_res.status_code == 200
        kpi_data = kpi_res.json()
        assert kpi_data["writeoffs_avoided_month"] >= 4500.0
