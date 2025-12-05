from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AskRequest, AskResponse
from app.services.rag_engine import RAGEngine
from app.utils.logger import logger
from app.utils.security import verify_api_key

router = APIRouter()
rag_engine = RAGEngine()

@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Answer questions using RAG over uploaded documents.
    """
    try:
        result = await rag_engine.answer_question(
            question=request.question,
            document_ids=request.document_ids,
            top_k=request.top_k,
            db=db
        )
        
        logger.info(f"Answered question with {len(result['citations'])} citations")
        
        return AskResponse(
            answer=result["answer"],
            citations=result["citations"],
            sources=result["sources"]
        )
    
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(500, f"Question answering failed: {str(e)}")

@router.get("/ask/stream")
async def ask_question_stream(
    question: str,
    document_ids: str = None,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Answer questions with streaming response using Server-Sent Events.
    """
    doc_ids = document_ids.split(",") if document_ids else None
    
    async def generate():
        try:
            async for chunk in rag_engine.answer_question_stream(
                question=question,
                document_ids=doc_ids,
                top_k=top_k,
                db=db
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )