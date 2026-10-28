import csv
import io
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.distributor import Distributor, DistributorRule
from app.models.product import Product
from app.models.batch import Batch, PurchaseInvoice


@dataclass
class RowError:
    row: int
    error: str
    data: Dict[str, Any]


@dataclass
class IngestionResult:
    total_rows: int = 0
    imported_count: int = 0
    updated_count: int = 0
    errors: List[RowError] = field(default_factory=list)


def parse_date(date_str: str) -> Optional[date]:
    """Parse multiple common date formats found in pharmacy billing software."""
    if not date_str:
        return None
    cleaned = date_str.strip()

    # Formats to try:
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%Y",
        "%Y/%m/%d",
        "%b %Y",
        "%B %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # If format was MM/YYYY without day, set to the last day of that month
            if fmt in ("%m/%Y", "%b %Y", "%B %Y"):
                # Approximate to end of month: month + 1 day 1 minus 1 day
                next_month = dt.month % 12 + 1
                year = dt.year + (dt.month // 12)
                first_of_next = date(year, next_month, 1)
                import datetime as dt_module
                last_day = first_of_next - dt_module.timedelta(days=1)
                return last_day
            return dt.date()
        except ValueError:
            continue
    return None


class IngestionService:
    @staticmethod
    def _normalize_header(header: str) -> str:
        """Normalize CSV column header to snake_case without special chars."""
        h = header.strip().lower()
        h = re.sub(r"[^a-z0-9_]+", "_", h).strip("_")
        aliases = {
            "item_name": "item",
            "product": "item",
            "medicine": "item",
            "product_name": "item",
            "batch": "batch_no",
            "batch_number": "batch_no",
            "expiry_date": "expiry",
            "exp_date": "expiry",
            "exp": "expiry",
            "distributor_name": "distributor",
            "supplier": "distributor",
            "vendor": "distributor",
            "quantity": "qty",
            "units": "qty",
            "rate": "price",
            "purchase_rate": "price",
            "cost": "price",
            "invoice": "invoice_no",
            "inv_no": "invoice_no",
            "bill_no": "invoice_no",
        }
        return aliases.get(h, h)

    @classmethod
    async def process_csv(
        cls,
        session: AsyncSession,
        tenant_id: str,
        csv_content: str,
    ) -> IngestionResult:
        """
        Parses CSV input, validates row by row, and inserts/updates products,
        distributors, and batches idempotently.
        """
        result = IngestionResult()
        stream = io.StringIO(csv_content.strip())
        reader = csv.reader(stream)

        try:
            raw_headers = next(reader)
        except StopIteration:
            result.errors.append(RowError(row=0, error="CSV file is empty", data={}))
            return result

        headers = [cls._normalize_header(h) for h in raw_headers]
        required_fields = {"item", "batch_no", "expiry", "distributor", "qty", "price", "invoice_no"}
        missing_fields = required_fields - set(headers)
        if missing_fields:
            result.errors.append(
                RowError(
                    row=1,
                    error=f"Missing required CSV columns: {', '.join(sorted(missing_fields))}",
                    data={"found_headers": raw_headers},
                )
            )
            return result

        # Cache lookups within this transaction to optimize ingestion speed
        distributor_cache: Dict[str, Distributor] = {}
        product_cache: Dict[str, Product] = {}

        # Preload existing distributors and products for this tenant
        dists = await session.scalars(select(Distributor).where(Distributor.tenant_id == tenant_id))
        for d in dists.all():
            distributor_cache[d.name.strip().lower()] = d

        prods = await session.scalars(select(Product).where(Product.tenant_id == tenant_id))
        for p in prods.all():
            product_cache[p.name.strip().lower()] = p

        row_number = 1
        for row in reader:
            row_number += 1
            if not row or all(not cell.strip() for cell in row):
                continue
            result.total_rows += 1

            if len(row) < len(headers):
                result.errors.append(
                    RowError(row=row_number, error="Row has fewer columns than headers", data={"raw": row})
                )
                continue

            row_dict = {headers[i]: row[i].strip() for i in range(len(headers))}

            # 1. Validate Item Name
            item_name = row_dict.get("item", "").strip()
            if not item_name:
                result.errors.append(
                    RowError(row=row_number, error="Item name cannot be empty", data=row_dict)
                )
                continue

            # 2. Validate Batch Number
            batch_no = row_dict.get("batch_no", "").strip()
            if not batch_no:
                result.errors.append(
                    RowError(row=row_number, error="Batch number cannot be empty", data=row_dict)
                )
                continue

            # 3. Validate Expiry Date
            expiry_str = row_dict.get("expiry", "")
            expiry_date = parse_date(expiry_str)
            if not expiry_date:
                result.errors.append(
                    RowError(
                        row=row_number,
                        error=f"Invalid expiry date format: '{expiry_str}'. Expected YYYY-MM-DD or MM/YYYY",
                        data=row_dict,
                    )
                )
                continue

            # 4. Validate Distributor Name
            distributor_name = row_dict.get("distributor", "").strip()
            if not distributor_name:
                result.errors.append(
                    RowError(row=row_number, error="Distributor name cannot be empty", data=row_dict)
                )
                continue

            # 5. Validate Quantity
            try:
                qty = int(row_dict.get("qty", "0"))
                if qty < 0:
                    raise ValueError("Quantity cannot be negative")
            except ValueError as ve:
                result.errors.append(
                    RowError(row=row_number, error=f"Invalid quantity: {ve}", data=row_dict)
                )
                continue

            # 6. Validate Purchase Price
            try:
                price_str = row_dict.get("price", "0").replace("$", "").replace("₹", "").replace(",", "").strip()
                price = Decimal(price_str)
                if price <= Decimal("0.00"):
                    raise ValueError("Price must be greater than zero")
            except (InvalidOperation, ValueError):
                result.errors.append(
                    RowError(row=row_number, error=f"Invalid purchase price: '{row_dict.get('price')}'", data=row_dict)
                )
                continue

            # Optional Fields
            category = row_dict.get("category", "General").strip() or "General"
            invoice_no = row_dict.get("invoice_no", f"INV-{date.today().strftime('%Y%m%d')}").strip()
            mrp_str = row_dict.get("mrp", "").replace("$", "").replace("₹", "").replace(",", "").strip()
            mrp = Decimal(mrp_str) if mrp_str else price * Decimal("1.25")

            # --- Idempotent Resolution & DB Persist ---
            dist_key = distributor_name.lower()
            distributor = distributor_cache.get(dist_key)
            if not distributor:
                distributor = Distributor(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    name=distributor_name,
                    code=distributor_name[:6].upper().replace(" ", ""),
                )
                session.add(distributor)
                await session.flush()
                # Create default rule for new distributor
                rule = DistributorRule(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    distributor_id=distributor.id,
                    version=1,
                    rules_config={
                        "return_window_start_days_before_expiry": 90,
                        "return_window_end_days_before_expiry": 15,
                        "excluded_categories": ["Cold Chain"],
                        "requires_prior_authorization": False,
                        "return_format": "standard_v1",
                        "pickup_days": ["Monday", "Thursday"],
                        "credit_note_sla_days": 14,
                        "min_return_value": "500.00",
                    },
                )
                session.add(rule)
                distributor_cache[dist_key] = distributor

            prod_key = item_name.lower()
            product = product_cache.get(prod_key)
            if not product:
                product = Product(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    sku=f"SKU-{abs(hash(item_name)) % 100000:05d}",
                    name=item_name,
                    category=category,
                    default_distributor_id=distributor.id,
                )
                session.add(product)
                await session.flush()
                product_cache[prod_key] = product

            # Check if this batch already exists for this tenant, product, distributor, batch_no
            existing_batch = await session.scalar(
                select(Batch).where(
                    Batch.tenant_id == tenant_id,
                    Batch.product_id == product.id,
                    Batch.distributor_id == distributor.id,
                    Batch.batch_no == batch_no,
                )
            )

            if existing_batch:
                # Idempotent update: update current_qty and purchase_price
                existing_batch.current_qty = qty
                existing_batch.purchase_price = price
                existing_batch.expiry_date = expiry_date
                existing_batch.invoice_ref = invoice_no
                result.updated_count += 1
            else:
                new_batch = Batch(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    product_id=product.id,
                    distributor_id=distributor.id,
                    batch_no=batch_no,
                    expiry_date=expiry_date,
                    initial_qty=qty,
                    current_qty=qty,
                    purchase_price=price,
                    mrp=mrp,
                    invoice_ref=invoice_no,
                    purchase_date=date.today(),
                )
                session.add(new_batch)
                result.imported_count += 1

        await session.commit()
        return result
