import uuid
from datetime import date
from typing import Any, Dict
from sqlalchemy import Boolean, Date, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class Distributor(Base, TimestampMixin, TenantMixin):
    __tablename__ = "distributors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=True)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    gstin: Mapped[str] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", back_populates="distributors")
    rules = relationship("DistributorRule", back_populates="distributor", cascade="all, delete-orphan", order_by="desc(DistributorRule.version)")
    batches = relationship("Batch", back_populates="distributor")
    return_requests = relationship("ReturnRequest", back_populates="distributor")
    credit_notes = relationship("CreditNote", back_populates="distributor")


class DistributorRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = "distributor_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date] = mapped_column(Date, nullable=True)
    rules_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    distributor = relationship("Distributor", back_populates="rules")
