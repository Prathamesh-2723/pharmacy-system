# ExpiryOS — Multi-Tenant Pharmacy Expiry Management & Return Automation SaaS

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14_App_Router-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL RLS](https://img.shields.io/badge/PostgreSQL-RLS_Isolated-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-Tailored_Dark_Mode-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

**ExpiryOS** is a production-grade multi-tenant SaaS built specifically for retail pharmacies to eliminate stock write-offs, automate distributor-specific return policies, auto-generate batch return requests, and track credit note settlements.

---

## 1. System Architecture

```mermaid
graph TD
    subgraph Frontend ["Frontend (Next.js 14 App Router + Tailwind + shadcn/ui)"]
        UI_Dash["Executive Financial Dashboard"]
        UI_Stock["Expiry & Batch Risk Manager"]
        UI_Rules["Distributor Rule Configurator"]
        UI_Returns["Return Kanban & Approval Workflow"]
        UI_Credit["Credit Reconciliation & Shortfalls"]
        UI_Upload["CSV & Manual Batch Ingestion"]
    end

    subgraph Backend ["Backend (FastAPI Async + SQLAlchemy 2.x)"]
        API_Gateway["FastAPI App + CORS + JWT Auth"]
        Auth_Middleware["JWT Auth + Tenant Context Middleware"]
        RLS_Context["PostgreSQL Row-Level Security Context"]
        
        subgraph Services ["Application Services"]
            Ingest_Svc["CSV Ingestion & Validation Service"]
            Rules_Engine["Pure Rules Engine (Framework-Independent)"]
            Return_Svc["Return Request & Lifecycle State Machine"]
            Credit_Svc["Credit Reconciliation & Shortfall Service"]
            Template_Svc["Jinja2 & Dispatch Slip Renderer"]
            Notify_Svc["Notification Abstraction (WhatsApp & Email)"]
        end
        
        subgraph Worker ["Async Worker & Scheduler (Celery + Redis)"]
            Celery_Beat["Celery Beat (Daily Expiry Scan @ 01:00 AM)"]
            Celery_Worker["Background Worker (SLA Escalations)"]
        end
    end

    subgraph DataStore ["Data Storage & Isolation"]
        PG[(PostgreSQL 16 with RLS Enabled)]
        Redis[(Redis Cache & Task Queue)]
    end

    Frontend -->|HTTP / JSON + JWT| API_Gateway
    API_Gateway --> Auth_Middleware
    Auth_Middleware --> RLS_Context
    RLS_Context --> Services
    Services --> PG
    Celery_Beat --> Redis
    Celery_Worker --> Redis
    Celery_Worker --> Services
    Services --> Notify_Svc
```

---

## 2. Key Features

### 1. Data Ingestion & OCR Interface
- **Idempotent CSV Import**: Bulk ingest purchase entries (`item, batch_no, expiry, distributor, qty, price, invoice_no`). Re-importing identical batches updates stock without duplicates.
- **Row-Level Validation**: Invalid dates or negative quantities are flagged with row numbers and exact reasons while remaining rows are safely imported.
- **OCR / LayoutLM Interface Stub**: Clean abstract interface `InvoiceParser` designed for deep learning document extraction.

### 2. Pure Distributor Rules Engine (Core IP)
- Fully framework-independent evaluator: `evaluate(batch, distributor_rules, today)`.
- Configurable return window thresholds (e.g. 90 to 15 days before expiry).
- Multi-category exclusions (Cold Chain, Schedule X, Narcotics, Breakage).
- Multiple rule versions per distributor with effective date ranges.
- Mathematical priority scoring:
  $$\text{Priority Score} = \text{Value at Risk} \times \text{Urgency Weight} \times \text{Window Proximity Factor}$$

### 3. Expiry Monitoring & Urgency Horizons
- Daily automated scanner classifying inventory into urgency buckets:
  - **Critical (&le; 15 days)**
  - **High Risk (16–30 days)**
  - **Moderate (31–60 days)**
  - **Planned (61–90 days)**
- Proactively flags batches whose distributor return window closes within 7 days.

### 4. Return Workflow & Kanban State Machine
- Lifecycle state machine:
  $$\text{DRAFT} \rightarrow \text{APPROVED} \rightarrow \text{SENT} \rightarrow \text{ACKNOWLEDGED} \rightarrow \text{PICKED\_UP} \rightarrow \text{CREDIT\_ISSUED} \rightarrow \text{SETTLED}$$
- 1-Click Pharmacist Approval and Bulk Approval.
- Printable dispatch slips with pharmacy GSTIN declarations.
- Direct **WhatsApp Web 1-click dispatch links** (`wa.me/?text=...`) for instant communication with distributor delivery agents.

### 5. Credit Note Reconciliation & Shortfall Tracking
- Match distributor credit notes to return requests.
- Automatic shortfall calculation:
  $$\text{Shortfall} = \max(0, \text{Expected Return Value} - \text{Credited Amount})$$
- Auto-escalation of distributor credit SLA breaches.

---

## 3. Quickstart Guide

### Option A: Docker Compose (All-In-One Containerized)
```bash
# Clone the repository and run:
docker compose up --build
```
- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### Option B: Local Standalone Development

#### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run database seed script (1 tenant, 30 distributors, 1,000 SKUs, 1,500 batches)
python -m app.seeds.seed_demo_data

# Start backend dev server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup (Next.js)
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Demo Login Credentials

The seed script preconfigures 3 realistic roles for **Apollo Healthcare & Retail Pharmacy**:

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Owner** | `owner@apollo.com` | `Password123!` | Full admin, rule editing, credit reconciliation |
| **Pharmacist** | `pharmacist@apollo.com` | `Password123!` | Batch entries, return approvals, dispatching |
| **Staff** | `staff@apollo.com` | `Password123!` | Inventory viewing and manual batch entry |

---

## 5. End-to-End Demo Walkthrough

1. **Sign In**: Navigate to `/login` and click the **Owner** preset button to log in.
2. **Review Executive KPIs**: View the **Loss Avoidance Meter** displaying avoid write-offs this month, and the urgency horizon distribution.
3. **Inspect Near-Expiry Stock**: Go to `/batches`, filter by "Window Closing (&le;7d)" or search by medicine name (e.g. `Augmentin` or `Pan D`).
4. **Auto-Draft Returns**: Click **"Scan & Auto-Draft"** on the Return Workflow board (`/returns`). The engine groups eligible near-expiry batches by distributor into draft requests.
5. **1-Click Approve**: Click **"Approve"** on a draft return or **"Approve All Drafts"** in bulk.
6. **Dispatch & WhatsApp Transmission**:
   - Transition to **"Dispatch"**.
   - Click the document icon to view the printable dispatch slip.
   - Click **"Send via WhatsApp"** to preview the pre-formatted WhatsApp text and generate a direct `wa.me` share link.
7. **Reconcile Credit Note**:
   - Go to `/credits` and click **"Record Credit Note"**.
   - Select the return request, enter the distributor credit note number, and enter the credited amount.
   - If the distributor deducted a fee, ExpiryOS flags the shortfall amount and updates the dashboard.

---

## 6. Running Tests

```bash
# Run backend pytest suite (24 tests covering Rules Engine, Ingestion, RLS, Return Lifecycle, and API)
python -m pytest backend/tests/ -v -c backend/pytest.ini

# Build frontend production bundle
cd frontend && npm run build
```
