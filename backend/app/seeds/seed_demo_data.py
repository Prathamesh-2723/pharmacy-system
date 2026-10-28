import asyncio
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import async_session_factory, engine
from app.models.tenant import Tenant
from app.models.user import User
from app.models.distributor import Distributor, DistributorRule
from app.models.product import Product
from app.models.batch import Batch
from app.models.return_request import ReturnRequest, ReturnRequestItem, ReturnStatusEvent
from app.models.credit_note import CreditNote

DISTRIBUTOR_NAMES = [
    ("Sun Pharma Logistics", "SUN001", "+919811122201", "returns@sunlogistics.com", ["Cold Chain", "Schedule X"], 90, 15, 14, 500.0),
    ("Cipla Distribution Network", "CIP002", "+919811122202", "claims@cipladist.com", ["Cold Chain"], 60, 10, 10, 0.0),
    ("Abbott Healthcare Supply", "ABT003", "+919811122203", "returns@abbottsupply.com", ["Narcotics"], 90, 15, 14, 1000.0),
    ("Dr. Reddy's Supply Hub", "DRR004", "+919811122204", "credit@drreddyshub.com", [], 120, 20, 21, 500.0),
    ("Lupin MedLink", "LUP005", "+919811122205", "returns@lupinlink.com", ["Cold Chain", "Breakage"], 90, 15, 14, 0.0),
    ("Mankind Pharma Hub", "MAN006", "+919811122206", "service@mankindhub.com", [], 60, 15, 7, 250.0),
    ("Torrent Distribution Ltd", "TOR007", "+919811122207", "returns@torrentdist.com", ["Schedule X"], 90, 10, 14, 500.0),
    ("Alkem Logistics Co", "ALK008", "+919811122208", "alkem@returnsmed.com", [], 90, 15, 12, 0.0),
    ("Zydus Healthcare Supply", "ZYD009", "+919811122209", "claims@zydushealth.com", ["Cold Chain"], 90, 20, 15, 750.0),
    ("Glenmark Pharma Supply", "GLN010", "+919811122210", "returns@glenmarksupply.com", ["Narcotics"], 120, 15, 14, 500.0),
    ("Intas Pharmaceuticals Dist", "INT011", "+919811122211", "service@intasdist.com", [], 60, 10, 10, 0.0),
    ("Macleods Healthcare Link", "MAC012", "+919811122212", "claims@macleods.com", ["Cold Chain"], 90, 15, 14, 500.0),
    ("Aristo Pharma Network", "ARI013", "+919811122213", "aristo@returns.in", [], 60, 15, 14, 0.0),
    ("USV Logistics India", "USV014", "+919811122214", "returns@usvlogistics.com", ["Schedule X"], 90, 15, 14, 250.0),
    ("Micro Labs Hub", "MIC015", "+919811122215", "support@microlabs.in", [], 90, 10, 10, 0.0),
    ("FDC MedSupply Services", "FDC016", "+919811122216", "returns@fdcsupply.com", ["Cold Chain"], 60, 15, 14, 500.0),
    ("Ipca Laboratories Dist", "IPC017", "+919811122217", "claims@ipcadist.com", [], 90, 15, 14, 0.0),
    ("JB Chemicals Link", "JBC018", "+919811122218", "jbchem@returns.in", ["Schedule X"], 90, 15, 15, 500.0),
    ("Hetero Healthcare Dist", "HET019", "+919811122219", "returns@heterohealth.com", [], 90, 20, 14, 0.0),
    ("Biocon Biologicals Supply", "BIO020", "+919811122220", "claims@bioconsupply.com", ["Breakage"], 120, 30, 21, 1500.0),
    ("Sanofi India Logistics", "SAN021", "+919811122221", "returns@sanofilogistics.com", ["Cold Chain"], 90, 15, 14, 1000.0),
    ("GlaxoSmithKline Dist Hub", "GSK022", "+919811122222", "claims@gskdist.com", [], 90, 15, 14, 500.0),
    ("Pfizer Distribution Hub", "PFI023", "+919811122223", "returns@pfizerhub.com", ["Cold Chain", "Narcotics"], 90, 20, 21, 1000.0),
    ("Novartis Healthcare Supply", "NOV024", "+919811122224", "claims@novartiscare.com", ["Cold Chain"], 120, 15, 14, 1000.0),
    ("AstraZeneca India Link", "AZI025", "+919811122225", "returns@azilink.com", [], 90, 15, 14, 500.0),
    ("Emcure Pharma Dist", "EMC026", "+919811122226", "emcure@returns.in", ["Schedule X"], 90, 15, 10, 0.0),
    ("Ajanta Pharma Logistics", "AJA027", "+919811122227", "returns@ajantalogistics.com", [], 60, 10, 14, 0.0),
    ("Alembic MedSupply Hub", "ALM028", "+919811122228", "claims@alembicsupply.com", ["Cold Chain"], 90, 15, 14, 500.0),
    ("Corona Remedies Logistics", "COR029", "+919811122229", "returns@coronaremedies.com", [], 60, 15, 12, 250.0),
    ("Blue Cross Labs Dist", "BCL030", "+919811122230", "claims@bluecrossdist.com", ["Breakage"], 90, 15, 14, 0.0),
]

CATEGORIES = ["Antibiotics", "Analgesic", "Cardiovascular", "Antidiabetic", "Antacid", "Respiratory", "Vitamin", "Dermatology", "Cold Chain", "Ophthalmology"]

MEDICINE_BASES = [
    ("Augmentin 625 Duo", "Antibiotics", 185.00),
    ("Dolo 650", "Analgesic", 32.50),
    ("Telma 40", "Cardiovascular", 145.00),
    ("Glycomet GP 2", "Antidiabetic", 178.00),
    ("Pan D Capsule", "Antacid", 165.00),
    ("Rosuvas 10", "Cardiovascular", 210.00),
    ("Amlong 5", "Cardiovascular", 65.00),
    ("Shelcal 500", "Vitamin", 112.00),
    ("Thyronorm 50", "Endocrine", 140.00),
    ("Montair LC", "Respiratory", 195.00),
    ("Azithral 500", "Antibiotics", 125.00),
    ("Clavam 625", "Antibiotics", 182.00),
    ("Monocef 1g Inj", "Antibiotics", 62.00),
    ("Pantocid 40", "Antacid", 115.00),
    ("Januvia 100", "Antidiabetic", 380.00),
    ("Lantus Solostar", "Cold Chain", 650.00),
    ("Combiflam", "Analgesic", 45.00),
    ("Ascoril D Plus", "Respiratory", 118.00),
    ("Allegra 120", "Respiratory", 168.00),
    ("Becosules Z", "Vitamin", 48.00),
    ("Ecosprin 75", "Cardiovascular", 12.50),
    ("Atorva 20", "Cardiovascular", 190.00),
    ("Zoryl M2", "Antidiabetic", 160.00),
    ("Omez 20", "Antacid", 68.00),
    ("Ciproglen 500", "Antibiotics", 54.00),
    ("Levolin 1mg", "Respiratory", 85.00),
    ("Deriphyllin Retard", "Respiratory", 42.00),
    ("Taxim O 200", "Antibiotics", 120.00),
    ("Cefix 200", "Antibiotics", 115.00),
    ("Supradyn Daily", "Vitamin", 55.00),
    ("Volini Gel", "Analgesic", 95.00),
    ("Betadine Ointment", "Dermatology", 75.00),
    ("Skinbless Lite", "Dermatology", 240.00),
    ("Refresh Tears Eye Drops", "Ophthalmology", 145.00),
    ("Moxicip Eye Drops", "Ophthalmology", 160.00),
    ("Calpol 500", "Analgesic", 22.00),
    ("Livogen Adult", "Vitamin", 85.00),
    ("Neurobion Forte", "Vitamin", 38.00),
    ("Duphaston 10mg", "Endocrine", 680.00),
    ("Gelusil MPS Liquid", "Antacid", 98.00),
]


async def seed():
    print("[SEED] Starting ExpiryOS demo data seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if already seeded
        existing_tenant = (await session.scalars(select(Tenant).where(Tenant.slug == "apollo-pharmacy"))).first()
        if existing_tenant:
            print("[SEED] Tenant 'apollo-pharmacy' already exists! Skipping duplicate seed.")
            return

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name="Apollo Healthcare & Retail Pharmacy",
            slug="apollo-pharmacy",
            gstin="27AAACA1234F1Z9",
            address="Plot 42, Healthcare Arcade, MG Road, Mumbai 400001",
            phone="+91 22 2847 9000",
        )
        session.add(tenant)
        await session.flush()

        # Users
        users = [
            User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email="owner@apollo.com",
                hashed_password=hash_password("Password123!"),
                full_name="Dr. Vikram Mehta",
                role="owner",
                is_active=True,
            ),
            User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email="pharmacist@apollo.com",
                hashed_password=hash_password("Password123!"),
                full_name="Ananya Sharma",
                role="pharmacist",
                is_active=True,
            ),
            User(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email="staff@apollo.com",
                hashed_password=hash_password("Password123!"),
                full_name="Rahul Verma",
                role="staff",
                is_active=True,
            ),
        ]
        session.add_all(users)
        await session.flush()

        # 30 Distributors
        distributors = []
        for name, code, phone, email, exclusions, win_start, win_end, sla, min_val in DISTRIBUTOR_NAMES:
            d_id = str(uuid.uuid4())
            dist = Distributor(
                id=d_id,
                tenant_id=tenant_id,
                name=name,
                code=code,
                contact_person=f"Mr. {name.split()[0]} Account Manager",
                phone=phone,
                email=email,
                address=f"Warehouse B-{code}, Industrial Pharma Park, Sector 4",
                gstin=f"27{code}9876Q1Z2",
            )
            session.add(dist)
            rule = DistributorRule(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                distributor_id=d_id,
                version=1,
                rules_config={
                    "return_window_start_days_before_expiry": win_start,
                    "return_window_end_days_before_expiry": win_end,
                    "excluded_categories": exclusions,
                    "requires_prior_authorization": False,
                    "return_format": "standard_v1",
                    "pickup_days": ["Monday", "Thursday"],
                    "credit_note_sla_days": sla,
                    "min_return_value": min_val,
                },
                is_active=True,
            )
            session.add(rule)
            distributors.append(dist)
        await session.flush()
        print(f"[OK] Created 1 Tenant, 3 Users, and {len(distributors)} Distributors with active return rules.")

        # ~1000 SKUs (Products)
        products = []
        random.seed(42)
        sku_counter = 1
        for i in range(1000):
            base_med, default_cat, base_price = random.choice(MEDICINE_BASES)
            strength_variations = ["250mg", "500mg", "650mg", "1000mg", "SR", "Forte", "Plus", "XR", "Drop"]
            variation = random.choice(strength_variations)
            prod_name = f"{base_med.split()[0]} {variation}"
            assigned_dist = random.choice(distributors)
            
            p = Product(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                sku=f"SKU-{sku_counter:05d}",
                name=prod_name,
                category=default_cat,
                default_distributor_id=assigned_dist.id,
                manufacturer=assigned_dist.name.replace(" Logistics", "").replace(" Hub", "").replace(" Supply", ""),
                hsn_code=f"3004{random.randint(10, 99)}",
                packaging_unit="Strip" if default_cat != "Ophthalmology" else "Bottle",
            )
            products.append(p)
            session.add(p)
            sku_counter += 1
        await session.flush()
        print(f"[OK] Created {len(products)} Product SKUs across 10 therapeutic categories.")

        # Batches (Mixed expiry distributions: 15D, 30D, 60D, 90D, Future, Expired)
        today = date.today()
        batches = []
        
        # We create ~1,500 batches
        for i in range(1500):
            p = random.choice(products)
            dist_id = p.default_distributor_id or random.choice(distributors).id
            
            roll = random.random()
            if roll < 0.25:
                days_delta = random.randint(12, 30)
            elif roll < 0.60:
                days_delta = random.randint(31, 75)
            elif roll < 0.80:
                days_delta = random.randint(76, 95)
            elif roll < 0.95:
                days_delta = random.randint(120, 360)
            else:
                days_delta = random.randint(-25, -2)

            exp_date = today + timedelta(days=days_delta)
            qty = random.randint(10, 200)
            price = Decimal(str(round(random.uniform(8.50, 280.00), 2)))
            mrp = round(price * Decimal("1.30"), 2)

            batch = Batch(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                product_id=p.id,
                distributor_id=dist_id,
                batch_no=f"B{today.year}-{random.randint(1000, 9999)}",
                expiry_date=exp_date,
                initial_qty=qty,
                current_qty=qty,
                purchase_price=price,
                mrp=mrp,
                invoice_ref=f"INV-{random.randint(10000, 99999)}",
                purchase_date=today - timedelta(days=random.randint(90, 300)),
                status="ACTIVE",
            )
            batches.append(batch)
            session.add(batch)

        await session.flush()
        print(f"[OK] Created {len(batches)} Batches with varied expiry horizons.")

        # Seed realistic Return Requests across different Kanban states
        sample_dists = distributors[:6]
        states = ["DRAFT", "APPROVED", "SENT", "ACKNOWLEDGED", "CREDIT_ISSUED", "SETTLED"]

        for idx, dist in enumerate(sample_dists):
            st = states[idx % len(states)]
            # Pick 3 batches of this distributor
            matching_batches = [b for b in batches if b.distributor_id == dist.id][:4]
            if not matching_batches:
                continue

            tot_val = sum((b.purchase_price * b.current_qty for b in matching_batches), Decimal("0.00"))
            ret = ReturnRequest(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                distributor_id=dist.id,
                return_request_no=f"RET-{today.strftime('%Y%m%d')}-00{idx+1}",
                status=st,
                total_estimated_value=tot_val,
                total_credit_received=tot_val if st == "SETTLED" else (tot_val * Decimal("0.85") if st == "CREDIT_ISSUED" else Decimal("0.00")),
                item_count=len(matching_batches),
                approved_at=datetime.now(timezone.utc) - timedelta(days=3) if st != "DRAFT" else None,
                dispatched_at=datetime.now(timezone.utc) - timedelta(days=2) if st in ["SENT", "ACKNOWLEDGED", "CREDIT_ISSUED", "SETTLED"] else None,
                credit_sla_deadline=datetime.now(timezone.utc) + timedelta(days=10) if st in ["SENT", "ACKNOWLEDGED"] else None,
            )
            session.add(ret)
            await session.flush()

            for b in matching_batches:
                item = ReturnRequestItem(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    return_request_id=ret.id,
                    batch_id=b.id,
                    requested_qty=b.current_qty,
                    accepted_qty=b.current_qty if st in ["CREDIT_ISSUED", "SETTLED"] else None,
                    unit_purchase_price=b.purchase_price,
                    total_value=b.purchase_price * b.current_qty,
                    reason="Near Expiry Return Window Active",
                )
                session.add(item)
                if st in ["APPROVED", "SENT", "ACKNOWLEDGED", "CREDIT_ISSUED"]:
                    b.status = "RETURNING"
                elif st == "SETTLED":
                    b.status = "RETURNED"

            # Audit event
            event = ReturnStatusEvent(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                return_request_id=ret.id,
                from_status=None,
                to_status=st,
                trigger="SEED_DATA",
                comment=f"Initial seed return in status {st}",
            )
            session.add(event)

            # Credit note if settled or credit_issued
            if st in ["CREDIT_ISSUED", "SETTLED"]:
                is_full = (st == "SETTLED")
                cred_amt = tot_val if is_full else round(tot_val * Decimal("0.85"), 2)
                cn = CreditNote(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    distributor_id=dist.id,
                    return_request_id=ret.id,
                    credit_note_no=f"CN-{dist.code}-{random.randint(1000, 9999)}",
                    credit_note_date=today - timedelta(days=1),
                    expected_amount=tot_val,
                    credited_amount=cred_amt,
                    shortfall_amount=tot_val - cred_amt,
                    status="MATCHED" if is_full else "PARTIAL",
                    remarks="100% Settled" if is_full else "Shortfall: 15% distributor handling deduction",
                )
                session.add(cn)

        await session.commit()
        print("[OK] Seeding successfully completed!")
        print("---------------------------------------------------------------")
        print("Login credentials:")
        print("  Owner:      owner@apollo.com      / Password123!")
        print("  Pharmacist: pharmacist@apollo.com / Password123!")
        print("  Staff:      staff@apollo.com      / Password123!")
        print("---------------------------------------------------------------")


if __name__ == "__main__":
    asyncio.run(seed())
