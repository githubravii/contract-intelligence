from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
import os
from pathlib import Path

from app.database import get_db
from app.schemas import IngestResponse
from app.services.pdf_parser import PDFParser
from app.services.embeddings import EmbeddingService
from app.models import Document, Chunk
from app.utils.logger import logger
from app.utils.security import verify_api_key

router = APIRouter()
pdf_parser = PDFParser()
embedding_service = EmbeddingService()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Ingest PDF documents, extract text, create embeddings, and store in database.
    """
    document_ids = []
    
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(400, f"Only PDF files allowed: {file.filename}")
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Save file
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / f"{doc_id}_{file.filename}"
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Parse PDF
            parsed_data = await pdf_parser.parse_pdf(str(file_path))
            
            # Create document record
            document = Document(
                document_id=doc_id,
                filename=file.filename,
                file_path=str(file_path),
                mime_type="application/pdf",
                file_size=len(content),
                page_count=parsed_data["page_count"],
                text_content=parsed_data["full_text"],
                metadata=parsed_data["metadata"]
            )
            db.add(document)
            await db.flush()
            
            # Create chunks with embeddings
            chunks_data = await pdf_parser.create_chunks(
                parsed_data["full_text"],
                parsed_data["pages"]
            )
            
            for idx, chunk_data in enumerate(chunks_data):
                embedding = await embedding_service.create_embedding(chunk_data["text"])
                
                chunk = Chunk(
                    document_id=doc_id,
                    chunk_index=idx,
                    text=chunk_data["text"],
                    page_number=chunk_data["page"],
                    char_start=chunk_data["char_start"],
                    char_end=chunk_data["char_end"],
                    embedding=embedding
                )
                db.add(chunk)
            
            document_ids.append(doc_id)
            logger.info(f"Ingested document {doc_id}: {file.filename}")
        
        await db.commit()
        
        return IngestResponse(
            document_ids=document_ids,
            message=f"Successfully ingested {len(document_ids)} documents",
            total_documents=len(document_ids)
        )
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(500, f"Ingestion failed: {str(e)}")




