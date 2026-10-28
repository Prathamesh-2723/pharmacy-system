import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class ReturnRequest(Base, TimestampMixin, TenantMixin):
    __tablename__ = "return_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    return_request_no: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", index=True, nullable=False
    )  # DRAFT, APPROVED, SENT, ACKNOWLEDGED, PICKED_UP, CREDIT_ISSUED, SETTLED, REJECTED, DISPUTED
    total_estimated_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_credit_received: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    credit_sla_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="return_requests")
    distributor = relationship("Distributor", back_populates="return_requests")
    items = relationship("ReturnRequestItem", back_populates="return_request", cascade="all, delete-orphan")
    events = relationship("ReturnStatusEvent", back_populates="return_request", cascade="all, delete-orphan", order_by="desc(ReturnStatusEvent.created_at)")
    credit_notes = relationship("CreditNote", back_populates="return_request")


class ReturnRequestItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "return_request_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("return_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    batch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("batches.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    requested_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_purchase_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), default="Near Expiry Return", nullable=False)

    return_request = relationship("ReturnRequest", back_populates="items")
    batch = relationship("Batch", back_populates="return_items")


class ReturnStatusEvent(Base, TenantMixin):
    """Immutable audit trail of return request status transitions."""
    __tablename__ = "return_status_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("return_requests.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger: Mapped[str] = mapped_column(String(50), default="USER", nullable=False)  # USER, CRON, SYSTEM
    triggered_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    return_request = relationship("ReturnRequest", back_populates="events")
