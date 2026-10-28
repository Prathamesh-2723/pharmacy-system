from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_roles
from app.models.user import User
from app.services.ingestion_service import IngestionService
from app.services.invoice_parser import StubInvoiceParser

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


@router.post("/csv")
async def import_csv_invoices(
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(["owner", "pharmacist", "staff"])),
    session: AsyncSession = Depends(get_db_session),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are accepted for batch purchase import",
        )

    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode("utf-8-sig")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read CSV file: {str(e)}",
        )

    result = await IngestionService.process_csv(
        session=session,
        tenant_id=current_user.tenant_id,
        csv_content=content_str,
    )

    return {
        "filename": file.filename,
        "total_rows_processed": result.total_rows,
        "new_batches_imported": result.imported_count,
        "existing_batches_updated": result.updated_count,
        "error_count": len(result.errors),
        "errors": [
            {
                "row": err.row,
                "error": err.error,
                "raw_data": err.data,
            }
            for err in result.errors
        ],
    }


@router.post("/invoice-parse")
async def parse_invoice_ocr_stub(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    OCR / LayoutLM Document Parser Stub.
    Demonstrates clean interface extension point for machine learning pipeline.
    """
    parser = StubInvoiceParser()
    result = await parser.parse_invoice(file.file, file.filename)
    return {
        "status": "success",
        "parser_model": result.parser_model,
        "invoice_no": result.invoice_no,
        "invoice_date": str(result.invoice_date),
        "distributor_name": result.distributor_name,
        "distributor_gstin": result.distributor_gstin,
        "extracted_items_count": len(result.items),
        "items": [
            {
                "item_name": item.item_name,
                "batch_no": item.batch_no,
                "expiry_date": str(item.expiry_date),
                "qty": item.qty,
                "purchase_price": float(item.purchase_price),
                "mrp": float(item.mrp) if item.mrp else None,
                "category": item.category,
                "confidence_score": item.confidence_score,
            }
            for item in result.items
        ],
        "notes": "LayoutLM parser stub ready for PyTorch / ONNX model weight integration.",
    }
