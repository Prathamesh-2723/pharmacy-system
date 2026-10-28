from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import BinaryIO, List, Optional


@dataclass
class ParsedInvoiceItem:
    item_name: str
    batch_no: str
    expiry_date: date
    qty: int
    purchase_price: Decimal
    mrp: Optional[Decimal] = None
    category: Optional[str] = "General"
    confidence_score: float = 1.0


@dataclass
class ParsedInvoiceResult:
    invoice_no: str
    invoice_date: date
    distributor_name: str
    distributor_gstin: Optional[str]
    items: List[ParsedInvoiceItem]
    raw_text: Optional[str] = None
    parser_model: str = "stub_parser_v1"


class InvoiceParser(ABC):
    """
    Abstract interface for parsing pharmacy purchase invoices.
    Enables future plug-and-play integrations with OCR (e.g. AWS Textract,
    Google Document AI, LayoutLMv3, or Donut).
    """

    @abstractmethod
    async def parse_invoice(self, file_stream: BinaryIO, filename: str) -> ParsedInvoiceResult:
        """Parse raw PDF/image invoice into structured line items and distributor metadata."""
        pass


class StubInvoiceParser(InvoiceParser):
    """
    Default stub parser implementation.
    Returns structured demonstration items indicating OCR layout parser ready for model weights.
    """

    async def parse_invoice(self, file_stream: BinaryIO, filename: str) -> ParsedInvoiceResult:
        return ParsedInvoiceResult(
            invoice_no=f"INV-OCR-{filename[:8].upper()}",
            invoice_date=date.today(),
            distributor_name="Sample Distributor OCR",
            distributor_gstin="27ABCDE1234F1Z5",
            items=[
                ParsedInvoiceItem(
                    item_name="Ciprofloxacin 500mg",
                    batch_no="CIP-2026-X1",
                    expiry_date=date(2026, 12, 31),
                    qty=100,
                    purchase_price=Decimal("18.50"),
                    mrp=Decimal("26.00"),
                    category="Antibiotics",
                    confidence_score=0.98,
                ),
                ParsedInvoiceItem(
                    item_name="Pantoprazole 40mg",
                    batch_no="PAN-2026-Y2",
                    expiry_date=date(2027, 3, 31),
                    qty=200,
                    purchase_price=Decimal("12.00"),
                    mrp=Decimal("19.50"),
                    category="Antacid",
                    confidence_score=0.95,
                ),
            ],
            raw_text="[STUB] LayoutLM / OCR Document extraction stub",
            parser_model="stub_layoutlm_v1",
        )
