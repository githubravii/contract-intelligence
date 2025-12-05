import fitz  # PyMuPDF
from typing import List, Dict, Any
from app.config import settings

class PDFParser:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    async def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text and metadata from PDF."""
        doc = fitz.open(file_path)
        
        pages = []
        full_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages.append({
                "page_number": page_num + 1,
                "text": text,
                "char_start": len("".join(full_text)),
                "char_end": len("".join(full_text)) + len(text)
            })
            full_text.append(text)
        
        metadata = {
            "author": doc.metadata.get("author", ""),
            "title": doc.metadata.get("title", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", "")
        }
        
        doc.close()
        
        return {
            "full_text": "\n".join(full_text),
            "pages": pages,
            "page_count": len(pages),
            "metadata": metadata
        }
    
    async def create_chunks(
        self, 
        text: str, 
        pages: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        
        current_pos = 0
        chunk_idx = 0
        
        while current_pos < len(words):
            # Get chunk
            chunk_words = words[current_pos:current_pos + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            # Find page number for this chunk
            char_start = len(" ".join(words[:current_pos]))
            char_end = char_start + len(chunk_text)
            
            page_num = 1
            for page in pages:
                if char_start >= page["char_start"] and char_start < page["char_end"]:
                    page_num = page["page_number"]
                    break
            
            chunks.append({
                "text": chunk_text,
                "page": page_num,
                "char_start": char_start,
                "char_end": char_end
            })
            
            # Move forward
            current_pos += self.chunk_size - self.chunk_overlap
            chunk_idx += 1
        
        return chunks

