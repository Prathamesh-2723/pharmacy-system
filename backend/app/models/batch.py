import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class Batch(Base, TimestampMixin, TenantMixin):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    batch_no: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    initial_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    mrp: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=True)
    invoice_ref: Mapped[str] = mapped_column(String(100), nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", index=True, nullable=False
    )  # ACTIVE, RETURNING, RETURNED, EXPIRED, SOLD_OUT

    tenant = relationship("Tenant", back_populates="batches")
    product = relationship("Product", back_populates="batches")
    distributor = relationship("Distributor", back_populates="batches")
    return_items = relationship("ReturnRequestItem", back_populates="batch")


class PurchaseInvoice(Base, TimestampMixin, TenantMixin):
    __tablename__ = "purchase_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    invoice_no: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
