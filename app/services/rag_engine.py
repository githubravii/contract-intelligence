from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from anthropic import AsyncAnthropic
import json

from app.models import Chunk, Document
from app.services.embeddings import EmbeddingService
from app.config import settings
from app.utils.logger import logger

class RAGEngine:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def answer_question(
        self,
        question: str,
        document_ids: Optional[List[str]],
        top_k: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Answer question using RAG."""
        
        # Create question embedding
        question_embedding = await self.embedding_service.create_embedding(question)
        
        # Build query
        query = select(
            Chunk,
            Document.filename
        ).join(
            Document, Chunk.document_id == Document.document_id
        )
        
        if document_ids:
            query = query.where(Chunk.document_id.in_(document_ids))
        
        # Vector similarity search
        query = query.order_by(
            Chunk.embedding.cosine_distance(question_embedding)
        ).limit(top_k)
        
        result = await db.execute(query)
        chunks = result.all()
        
        if not chunks:
            return {
                "answer": "I don't have enough information to answer this question.",
                "citations": [],
                "sources": []
            }
        
        # Build context
        context_parts = []
        citations = []
        sources = set()
        
        for chunk, filename in chunks:
            context_parts.append(f"[Document: {filename}, Page {chunk.page_number}]\n{chunk.text}")
            citations.append({
                "document_id": chunk.document_id,
                "page": chunk.page_number,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            })
            sources.add(filename)
        
        context = "\n\n".join(context_parts)
        
        # Load prompt
        with open("prompts/qa_prompt.txt", "r") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.format(
            context=context,
            question=question
        )
        
        # Call Claude
        message = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = message.content[0].text
        
        return {
            "answer": answer,
            "citations": citations,
            "sources": list(sources)
        }
    
    async def answer_question_stream(
        self,
        question: str,
        document_ids: Optional[List[str]],
        top_k: int,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """Stream answer using SSE."""
        
        # Get context (same as above)
        question_embedding = await self.embedding_service.create_embedding(question)
        
        query = select(Chunk, Document.filename).join(
            Document, Chunk.document_id == Document.document_id
        )
        
        if document_ids:
            query = query.where(Chunk.document_id.in_(document_ids))
        
        query = query.order_by(
            Chunk.embedding.cosine_distance(question_embedding)
        ).limit(top_k)
        
        result = await db.execute(query)
        chunks = result.all()
        
        if not chunks:
            yield json.dumps({"type": "error", "message": "No relevant context found"})
            return
        
        context_parts = []
        for chunk, filename in chunks:
            context_parts.append(f"[Document: {filename}, Page {chunk.page_number}]\n{chunk.text}")
        
        context = "\n\n".join(context_parts)
        
        with open("prompts/qa_prompt.txt", "r") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.format(context=context, question=question)
        
        # Stream response
        async with self.client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield json.dumps({"type": "content", "text": text})

