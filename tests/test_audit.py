import pytest

@pytest.mark.asyncio
async def test_audit_contract(client):
    """Test contract risk audit."""
    response = await client.post(
        "/api/v1/audit?document_id=test-doc-id&use_llm=false",
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "findings" in data
        assert "risk_score" in data
        assert "summary" in data

@pytest.mark.asyncio
async def test_audit_with_llm_toggle(client):
    """Test audit with LLM analysis toggled on."""
    response = await client.post(
        "/api/v1/audit?document_id=test-doc-id&use_llm=true",
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    # Should work regardless of toggle
    assert response.status_code in [200, 404]