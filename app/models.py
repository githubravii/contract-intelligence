from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    mime_type = Column(String(100))
    file_size = Column(Integer)
    page_count = Column(Integer)
    text_content = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("Extraction", back_populates="document", cascade="all, delete-orphan")
    audit_results = relationship("AuditResult", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page_number = Column(Integer)
    char_start = Column(Integer)
    char_end = Column(Integer)
    embedding = Column(Vector(384))  # Dimension for all-MiniLM-L6-v2
    metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index('ix_chunks_document_id', 'document_id'),
    )

class Extraction(Base):
    __tablename__ = "extractions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=False, unique=True)
    parties = Column(JSON, default=[])
    effective_date = Column(String(50))
    term = Column(String(255))
    governing_law = Column(String(255))
    payment_terms = Column(Text)
    termination = Column(Text)
    auto_renewal = Column(String(255))
    confidentiality = Column(Text)
    indemnity = Column(Text)
    liability_cap_number = Column(Float)
    liability_cap_currency = Column(String(10))
    signatories = Column(JSON, default=[])
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="extractions")

class AuditResult(Base):
    __tablename__ = "audit_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.document_id"), nullable=False)
    risk_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    evidence = Column(Text)
    page_number = Column(Integer)
    char_start = Column(Integer)
    char_end = Column(Integer)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="audit_results")

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(512), nullable=False)
    event_types = Column(JSON, default=[])
    active = Column(Integer, default=1)
    secret = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())