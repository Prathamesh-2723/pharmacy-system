import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, TenantMixin


class Product(Base, TimestampMixin, TenantMixin):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    generic_name: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="General", index=True, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(255), nullable=True)
    hsn_code: Mapped[str] = mapped_column(String(30), nullable=True)
    packaging_unit: Mapped[str] = mapped_column(String(50), default="Strip", nullable=True)
    default_distributor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("distributors.id", ondelete="SET NULL"), nullable=True
    )

    tenant = relationship("Tenant", back_populates="products")
    batches = relationship("Batch", back_populates="product", cascade="all, delete-orphan")
