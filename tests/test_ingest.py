import pytest
from io import BytesIO

@pytest.mark.asyncio
async def test_ingest_single_pdf(client):
    """Test ingesting a single PDF."""
    pdf_content = b"%PDF-1.4\n...mock pdf content..."
    files = {"files": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
    
    response = await client.post(
        "/api/v1/ingest",
        files=files,
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_ids" in data
    assert len(data["document_ids"]) == 1

@pytest.mark.asyncio
async def test_ingest_multiple_pdfs(client):
    """Test ingesting multiple PDFs."""
    files = [
        ("files", ("test1.pdf", BytesIO(b"%PDF-1.4\n..."), "application/pdf")),
        ("files", ("test2.pdf", BytesIO(b"%PDF-1.4\n..."), "application/pdf"))
    ]
    
    response = await client.post(
        "/api/v1/ingest",
        files=files,
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["document_ids"]) == 2

@pytest.mark.asyncio
async def test_ingest_invalid_file_type(client):
    """Test that non-PDF files are rejected."""
    files = {"files": ("test.txt", BytesIO(b"text content"), "text/plain")}
    
    response = await client.post(
        "/api/v1/ingest",
        files=files,
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    assert response.status_code == 400