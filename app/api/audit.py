from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas import AuditResponse
from app.services.risk_analyzer import RiskAnalyzer
from app.models import Document, AuditResult
from app.utils.logger import logger
from app.utils.security import verify_api_key
from app.services.webhook_service import WebhookService

router = APIRouter()
risk_analyzer = RiskAnalyzer()
webhook_service = WebhookService()

@router.post("/audit", response_model=AuditResponse)
async def audit_contract(
    document_id: str = Query(...),
    use_llm: bool = Query(True, description="Use LLM analysis in addition to rules"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Audit contract for risky clauses and compliance issues.
    """
    try:
        # Get document
        result = await db.execute(
            select(Document).where(Document.document_id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(404, f"Document {document_id} not found")
        
        # Delete existing audit results
        await db.execute(
            select(AuditResult).where(AuditResult.document_id == document_id)
        )
        
        # Run audit
        audit_results = await risk_analyzer.analyze_risks(
            document.text_content,
            use_llm=use_llm
        )
        
        # Store results
        findings = []
        for finding in audit_results["findings"]:
            audit_result = AuditResult(
                document_id=document_id,
                risk_type=finding["risk_type"],
                severity=finding["severity"],
                description=finding["description"],
                evidence=finding.get("evidence"),
                page_number=finding.get("page"),
                char_start=finding.get("char_start"),
                char_end=finding.get("char_end"),
                recommendations=finding.get("recommendations")
            )
            db.add(audit_result)
            findings.append(finding)
        
        await db.commit()
        
        logger.info(f"Audit completed for document {document_id}: {len(findings)} findings")
        
        # Send webhook
        await webhook_service.dispatch_event(
            "audit.complete",
            {
                "document_id": document_id,
                "findings_count": len(findings),
                "risk_score": audit_results["risk_score"]
            }
        )
        
        return AuditResponse(
            document_id=document_id,
            findings=findings,
            risk_score=audit_results["risk_score"],
            summary=audit_results["summary"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit failed: {str(e)}")
        raise HTTPException(500, f"Audit failed: {str(e)}")