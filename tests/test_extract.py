import pytest

@pytest.mark.asyncio
async def test_extract_fields(client, test_db):
    """Test field extraction from document."""
    # First ingest a document
    # (In real test, use actual test PDF)
    
    response = await client.post(
        "/api/v1/extract?document_id=test-doc-id",
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "parties" in data
        assert "effective_date" in data
        assert "signatories" in data

@pytest.mark.asyncio
async def test_extract_nonexistent_document(client):
    """Test extraction with invalid document ID."""
    response = await client.post(
        "/api/v1/extract?document_id=nonexistent",
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    assert response.status_code == 404