from anthropic import AsyncAnthropic
import json
import re
from typing import Dict, Any
import spacy

from app.config import settings
from app.utils.logger import logger

class FieldExtractor:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("spaCy model not loaded, using fallback methods")
            self.nlp = None
    
    async def extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract structured fields from contract text."""
        
        # Load extraction prompt
        with open("prompts/extraction_prompt.txt", "r") as f:
            prompt_template = f.read()
        
        prompt = prompt_template.format(contract_text=text[:10000])  # Limit to first 10k chars
        
        # Call Claude
        message = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
            else:
                extracted = {}
        except json.JSONDecodeError:
            logger.error("Failed to parse extraction response as JSON")
            extracted = {}
        
        # Fallback extraction using rules
        extracted = self._apply_fallback_extraction(text, extracted)
        
        return extracted
    
    def _apply_fallback_extraction(
        self, 
        text: str, 
        extracted: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply rule-based extraction as fallback."""
        
        # Extract dates if not found
        if not extracted.get("effective_date"):
            date_patterns = [
                r'effective\s+date[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
                r'dated\s+(\w+\s+\d{1,2},?\s+\d{4})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extracted["effective_date"] = match.group(1)
                    break
        
        # Extract liability cap
        if not extracted.get("liability_cap"):
            cap_pattern = r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:USD|dollars)?'
            matches = re.findall(cap_pattern, text)
            if matches:
                amount = matches[0].replace(',', '')
                extracted["liability_cap"] = {
                    "number": float(amount),
                    "currency": "USD"
                }
        
        # Extract parties using NLP if available
        if not extracted.get("parties") and self.nlp:
            doc = self.nlp(text[:5000])
            parties = set()
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    parties.add(ent.text)
            extracted["parties"] = list(parties)[:5]
        
        # Ensure all fields exist
        fields = [
            "parties", "effective_date", "term", "governing_law",
            "payment_terms", "termination", "auto_renewal",
            "confidentiality", "indemnity", "signatories"
        ]
        for field in fields:
            if field not in extracted:
                extracted[field] = [] if field in ["parties", "signatories"] else None
        
        return extracted