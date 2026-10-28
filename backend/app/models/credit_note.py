import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class CreditNote(Base, TimestampMixin, TenantMixin):
    __tablename__ = "credit_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    return_request_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("return_requests.id", ondelete="SET NULL"), index=True, nullable=True
    )
    credit_note_no: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    credit_note_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    credited_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shortfall_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="MATCHED", index=True, nullable=False
    )  # MATCHED, PARTIAL, DISPUTED
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="credit_notes")
    distributor = relationship("Distributor", back_populates="credit_notes")
    return_request = relationship("ReturnRequest", back_populates="credit_notes")
