import pytest

@pytest.mark.asyncio
async def test_ask_question(client):
    """Test RAG question answering."""
    payload = {
        "question": "What are the payment terms?",
        "document_ids": ["test-doc-id"],
        "top_k": 5
    }
    
    response = await client.post(
        "/api/v1/ask",
        json=payload,
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "citations" in data
        assert "sources" in data

@pytest.mark.asyncio
async def test_ask_stream(client):
    """Test streaming question answering."""
    response = await client.get(
        "/api/v1/ask/stream?question=What is this contract about?",
        headers={"X-API-Key": "dev-secret-key"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"