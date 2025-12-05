from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas import ExtractionResponse
from app.services.extractor import FieldExtractor
from app.models import Document, Extraction
from app.utils.logger import logger
from app.utils.security import verify_api_key
from app.services.webhook_service import WebhookService

router = APIRouter()
extractor = FieldExtractor()
webhook_service = WebhookService()

@router.post("/extract", response_model=ExtractionResponse)
async def extract_fields(
    document_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Extract structured fields from a contract document.
    """
    try:
        # Get document
        result = await db.execute(
            select(Document).where(Document.document_id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(404, f"Document {document_id} not found")
        
        # Check if already extracted
        result = await db.execute(
            select(Extraction).where(Extraction.document_id == document_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return _format_extraction_response(document_id, existing)
        
        # Extract fields
        extracted_data = await extractor.extract_fields(document.text_content)
        
        # Store extraction
        extraction = Extraction(
            document_id=document_id,
            parties=extracted_data.get("parties", []),
            effective_date=extracted_data.get("effective_date"),
            term=extracted_data.get("term"),
            governing_law=extracted_data.get("governing_law"),
            payment_terms=extracted_data.get("payment_terms"),
            termination=extracted_data.get("termination"),
            auto_renewal=extracted_data.get("auto_renewal"),
            confidentiality=extracted_data.get("confidentiality"),
            indemnity=extracted_data.get("indemnity"),
            liability_cap_number=extracted_data.get("liability_cap", {}).get("number"),
            liability_cap_currency=extracted_data.get("liability_cap", {}).get("currency"),
            signatories=extracted_data.get("signatories", [])
        )
        db.add(extraction)
        await db.commit()
        
        logger.info(f"Extracted fields for document {document_id}")
        
        # Send webhook notification
        await webhook_service.dispatch_event(
            "extraction.complete",
            {"document_id": document_id, "status": "success"}
        )
        
        return _format_extraction_response(document_id, extraction)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")

def _format_extraction_response(doc_id: str, extraction: Extraction) -> ExtractionResponse:
    liability_cap = None
    if extraction.liability_cap_number:
        liability_cap = {
            "number": extraction.liability_cap_number,
            "currency": extraction.liability_cap_currency
        }
    
    return ExtractionResponse(
        document_id=doc_id,
        parties=extraction.parties,
        effective_date=extraction.effective_date,
        term=extraction.term,
        governing_law=extraction.governing_law,
        payment_terms=extraction.payment_terms,
        termination=extraction.termination,
        auto_renewal=extraction.auto_renewal,
        confidentiality=extraction.confidentiality,
        indemnity=extraction.indemnity,
        liability_cap=liability_cap,
        signatories=extraction.signatories
    )
