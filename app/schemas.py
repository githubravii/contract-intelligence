from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Ingest schemas
class IngestResponse(BaseModel):
    document_ids: List[str]
    message: str
    total_documents: int

# Extract schemas
class Signatory(BaseModel):
    name: str
    title: Optional[str] = None

class ExtractionResponse(BaseModel):
    document_id: str
    parties: List[str]
    effective_date: Optional[str] = None
    term: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None
    termination: Optional[str] = None
    auto_renewal: Optional[str] = None
    confidentiality: Optional[str] = None
    indemnity: Optional[str] = None
    liability_cap: Optional[Dict[str, Any]] = None
    signatories: List[Signatory]

# Ask schemas
class Citation(BaseModel):
    document_id: str
    page: int
    char_start: int
    char_end: int
    text: str

class AskRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    sources: List[str]

# Audit schemas
class Finding(BaseModel):
    risk_type: str
    severity: str
    description: str
    evidence: str
    page: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    recommendations: Optional[str] = None

class AuditResponse(BaseModel):
    document_id: str
    findings: List[Finding]
    risk_score: float
    summary: str

# Webhook schemas
class WebhookCreate(BaseModel):
    url: str
    event_types: List[str] = Field(default=["extraction.complete", "audit.complete"])
    secret: Optional[str] = None

class WebhookResponse(BaseModel):
    id: int
    url: str
    event_types: List[str]
    active: bool
    created_at: datetime

# Health schemas
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    database: str
    redis: str