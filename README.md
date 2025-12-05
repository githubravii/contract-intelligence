# Contract Intelligence API
AI-powered contract analysis and risk detection system with RAG-based Q&A, field extraction, and compliance auditing.
🚀 Quick Start
bash# 1. Clone repository
git clone <your-repo-url>
cd contract-intelligence

# 2. Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start services
make up

# 4. Access API
# Swagger docs: http://localhost:8000/docs
# API: http://localhost:8000/api/v1
📋 Features

Document Ingestion: Upload and process PDF contracts with automatic text extraction and vectorization
Field Extraction: Extract 11+ structured fields (parties, dates, terms, liability caps, etc.)
RAG Q&A: Answer questions grounded in uploaded documents with precise citations
Risk Audit: Detect risky clauses using hybrid rule-based + LLM analysis
Streaming: Real-time SSE streaming for long-running queries
Webhooks: Event notifications for async operations

# Response
{
  "document_ids": ["abc-123", "def-456"],
  "message": "Successfully ingested 2 documents",
  "total_documents": 2
}
2. Extract Fields
bashcurl -X POST "http://localhost:8000/api/v1/extract?document_id=abc-123" \
  -H "X-API-Key: dev-secret-key"

# Response
{
  "document_id": "abc-123",
  "parties": ["Acme Corp", "Widget Inc"],
  "effective_date": "January 1, 2024",
  "term": "12 months",
  "governing_law": "State of California",
  "payment_terms": "Net 30 days",
  "liability_cap": {
    "number": 1000000,
    "currency": "USD"
  },
  "signatories": [
    {"name": "John Doe", "title": "CEO"},
    {"name": "Jane Smith", "title": "CFO"}
  ]
}
3. Ask Questions (RAG)
bashcurl -X POST "http://localhost:8000/api/v1/ask" \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the payment terms?",
    "document_ids": ["abc-123"],
    "top_k": 5
  }'

# Response
{
  "answer": "The payment terms specify Net 30 days...",
  "citations": [
    {
      "document_id": "abc-123",
      "page": 3,
      "char_start": 1250,
      "char_end": 1450,
      "text": "Payment shall be made within..."
    }
  ],
  "sources": ["contract1.pdf"]
}
4. Stream Answer
bashcurl -N "http://localhost:8000/api/v1/ask/stream?question=Summarize%20this%20contract" \
  -H "X-API-Key: dev-secret-key"

# SSE Stream
data: {"type": "content", "text": "This"}
data: {"type": "content", "text": " contract"}
...
5. Audit Contract
bashcurl -X POST "http://localhost:8000/api/v1/audit?document_id=abc-123&use_llm=true" \
  -H "X-API-Key: dev-secret-key"

# Response
{
  "document_id": "abc-123",
  "findings": [
    {
      "risk_type": "auto_renewal_short_notice",
      "severity": "high",
      "description": "Auto-renewal with only 15 days notice",
      "evidence": "automatically renews with 15 days notice",
      "recommendations": "Negotiate for at least 30 days"
    },
    {
      "risk_type": "unlimited_liability",
      "severity": "critical",
      "description": "No liability cap found",
      "evidence": "...",
      "recommendations": "Add liability cap clause"
    }
  ],
  "risk_score": 7.5,
  "summary": "Risk Score: 7.5/10. Found 2 issues: 1 critical, 1 high"
}
6. Webhooks
bash# Register webhook
curl -X POST "http://localhost:8000/api/v1/webhook/events" \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "event_types": ["extraction.complete", "audit.complete"]
  }'

# List webhooks
curl "http://localhost:8000/api/v1/webhook/events" \
  -H "X-API-Key: dev-secret-key"
7. Health & Metrics
bash# Health check
curl "http://localhost:8000/healthz"

# Prometheus metrics
curl "http://localhost:8000/metrics"
🧪 Testing
bash# Run all tests
make test

# Run specific test file
docker-compose exec api pytest tests/test_extract.py -v

# Run with coverage
docker-compose exec api pytest tests/ -v --cov=app --cov-report=html
📊 Evaluation
bash# Run Q&A evaluation
docker-compose exec api python eval/run_eval.py

# View results
cat eval/results.txt
🔐 Environment Variables
(-------)

🎯 Sample Contracts
The system includes 3 public contract PDFs for testing:

DEMO NDA Sample  - Standard mutual non-disclosure agreement
Source: SEC EDGAR


DEMO MSA Sample - Master services agreement

Source: Public contract repository


DEMO ToS Sample - Terms of service agreement

Source: Open source contracts



Note: All sample contracts are publicly available and used for demonstration purposes only.
🚨 Trade-offs & Design Decisions
1. Chunking Strategy

Decision: Fixed-size word-based chunking with overlap
Trade-off: Simple but may split sentences; alternatives: semantic chunking, recursive splitting
Rationale: Balance between simplicity and effectiveness for legal text

2. Embedding Model

Decision: all-MiniLM-L6-v2 (384 dimensions)
Trade-off: Fast and lightweight vs. more accurate larger models
Rationale: Good balance for production; can upgrade to e5-large for better accuracy

3. LLM Usage

Decision: Claude Sonnet 4 for extraction, Q&A, and risk analysis
Trade-off: Cost vs. accuracy; could use smaller models for some tasks
Rationale: High accuracy requirements for legal documents justify premium model

4. Dual-Mode Risk Detection

Decision: Rule-based patterns + optional LLM analysis
Trade-off: Speed vs. comprehensiveness
Rationale: Rules provide fast baseline; LLM catches edge cases

5. Database Choice

Decision: PostgreSQL with pgvector extension
Trade-off: Single database vs. dedicated vector DB (Pinecone, Weaviate)
Rationale: Simpler architecture, good performance for moderate scale

6. Sync vs Async

Decision: Async FastAPI with asyncio
Trade-off: Code complexity vs. performance
Rationale: Better handling of I/O-bound operations (DB, LLM calls)

🔒 Security Features

API Key Authentication: Header-based auth on all endpoints
PII Redaction: Automatic redaction of SSN, emails, phone numbers in logs
Input Validation: Pydantic schemas for request validation
File Type Restriction: Only PDF files accepted
Size Limits: Configurable max upload size (default 50MB)
Rate Limiting: Per-minute request limits (future: Redis-based)

🐛 Known Limitations

PDF Parsing: Complex layouts with tables may not parse perfectly
Hallucination: LLM may occasionally generate incorrect information (mitigated by RAG grounding)
Language Support: Currently English-only
Scale: Current setup suitable for ~10K documents; needs sharding for larger scale
Webhook Delivery: No retry logic (use task queue in production)

📝 Makefile Commands
bashmake up        # Start all services
make down      # Stop all services
make logs      # View API logs
make test      # Run tests
make clean     # Remove all data
make migrate   # Run database migrations
make shell     # Open shell in API container


📚 Additional Resources

Design Document - Detailed architecture and data models
API Documentation - Interactive Swagger UI
Prompts - All LLM prompts with rationale

🤝 Contributing
RAVI RANJAN
@Github link :- githubravii
